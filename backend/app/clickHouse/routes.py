from flask import jsonify, request, Response
from clickhouse_connect import get_client
from dotenv import load_dotenv
import pyarrow.ipc as ipc
from queue import Queue
import os
import json
from . import clickHouse_BP
from ..rpc_client import TopicModelRpcClient  # Import the RPC client modules
from ..rpc_client import SentimentAnalysisRpcClient 
from app.extensions import db
import uuid

import io
import pandas as pd

from io import BytesIO
import time

import app.redis_client as redis

load_dotenv()

#Currently set to 25, increase later if needed.
POOL_SIZE = 25
connection_pool = Queue(maxsize=POOL_SIZE)

def get_new_client():
    return get_client(
        host=os.getenv('CH_HOST'),
        port=os.getenv('CH_PORT'),
        database=os.getenv('CH_DATABASE'),
        username=os.getenv('CH_USER'),
        password=os.getenv('CH_PASSWORD')
    )


for _ in range(POOL_SIZE):
    connection_pool.put(get_new_client())


def get_pooled_client():
    try:
        return connection_pool.get(timeout=5)  
    except:
        raise Exception("No ClickHouse connections are available.")


def release_client(client):
    if client:
        connection_pool.put(client)


@clickHouse_BP.route('/api/search_list', methods=['GET'])
def search_list():
    prefix = request.args.get('subreddit', '').strip()
    if not prefix:
        return jsonify([])

    client = None
    try:
        client = get_pooled_client()
        # Query the dedicated `subreddits` table with case-insensitive prefix match
        # Use a ClickHouse parameter ({prefix:String}) to safely bind the user input.
        # The LIKE pattern is assembled server-side from the bound value via concat().
        sql = (
            "SELECT subreddit "
            "FROM subreddits "
            "WHERE lower(subreddit) LIKE concat(lower({prefix:String}), '%') "
            "ORDER BY subreddit ASC "
            "LIMIT 10"
        )
        qr = client.query(sql, parameters={"prefix": prefix})
        # Extract rows from QueryResult
        rows = getattr(qr, 'result_set', None) or getattr(qr, 'rows', None) or qr
        suggestions = [row[0] for row in rows]
        return jsonify(suggestions)
    except Exception:
        # If table doesn't exist or any error, return empty list
        return jsonify([])
    finally:
        if client:
            release_client(client)


def _build_feed_query(base_query: str, subreddit: str, start_date: str | None,
                      end_date: str | None, search_value: str) -> tuple[str, dict]:
    """
    Appends WHERE / ORDER BY clauses to *base_query* and returns the final SQL
    string together with a parameters dict ready for clickhouse-connect.

    All user-supplied values are bound as typed ClickHouse parameters so that
    the driver handles quoting and escaping — no f-string interpolation of
    untrusted data anywhere.
    """
    conditions = []
    parameters: dict = {}

    if subreddit:
        conditions.append("subreddit = {subreddit:String}")
        parameters["subreddit"] = subreddit

    if start_date:
        start_date_formatted = start_date.replace("T", " ").split(".")[0]
        conditions.append("created_utc >= toDateTime64({start_date:String}, 3)")
        parameters["start_date"] = start_date_formatted

    if end_date:
        end_date_formatted = end_date.replace("T", " ").split(".")[0]
        conditions.append("created_utc <= toDateTime64({end_date:String}, 3)")
        parameters["end_date"] = end_date_formatted

    if search_value:
        # concat() keeps the wildcard characters out of the bound value so the
        # driver never sees a string that needs special-character handling.
        conditions.append("selftext LIKE concat('%', {search_value:String}, '%')")
        parameters["search_value"] = search_value

    # Always exclude AutoModerator — this is a static literal, not user input.
    conditions.append("author != 'AutoModerator'")

    query = base_query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_utc DESC"
    query += " LIMIT 9999999999999 OFFSET 0"

    return query, parameters


@clickHouse_BP.route("/api/get_arrow", methods=["GET"])
def get_arrow():
    client = None
    try:
        subreddit    = request.args.get('subreddit', '')
        start_date   = request.args.get('startDate', None)
        end_date     = request.args.get('endDate', None)
        option       = request.args.get('option', 'reddit_comments')
        search_value = request.args.get('search_value', '', type=str)

        if not option or option.strip() == '':
            return jsonify({"error": "Data option was not selected."}), 400

        if ',' in option:
            # If both options are selected, use a UNION ALL query.
            base_query = (
                "SELECT * FROM ("
                "    (SELECT subreddit, author, title, selftext, created_utc, id FROM reddit_submissions) "
                "    UNION ALL "
                "    (SELECT subreddit, author, '(Comment)' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments)"
                ") AS combined"
            )
        elif option == "reddit_submissions":
            base_query = "SELECT subreddit, author, title, selftext, created_utc, id FROM reddit_submissions"
        elif option == "reddit_comments":
            base_query = "SELECT subreddit, author, '(Comment)' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments"
        # Fix to prevent error to console
        else:
            return jsonify({"error": "Invalid option provided."}), 400

        query, parameters = _build_feed_query(
            base_query, subreddit, start_date, end_date, search_value
        )

        client = get_pooled_client()
        if client is None:
            return jsonify({"error": "Failed to get ClickHouse client."}), 500

        # Use query_arrow to get an Arrow Table directly.
        start_time = time.time()
        table = client.query_arrow(query, parameters=parameters, use_strings=True)
        query_arrow_time = time.time() - start_time
        print(f"Query Arrow time: {query_arrow_time:.4f} seconds", flush=True)

        # Return empty Arrow stream
        if table.num_rows == 0:
            stream = io.BytesIO()
            with ipc.new_stream(stream, table.schema) as writer:
                writer.write_table(table)
            stream.seek(0)
            return Response(
                stream.getvalue(), 
                mimetype='application/vnd.apache.arrow.stream',
                headers={"Content-Disposition": "attachment; filename=data.arrow"}
            )
        
        # Serialize the Arrow Table into a binary stream.
        start_time = time.time()
        stream = io.BytesIO()
        with ipc.new_stream(stream, table.schema) as writer:
            writer.write_table(table)
        serialization_time = time.time() - start_time
        print(f"Arrow serialization time: {serialization_time:.4f} seconds", flush=True)
        
        total_time = query_arrow_time + serialization_time
        print(f"Total Arrow processing time: {total_time:.4f} seconds", flush=True)
        
        stream.seek(0)
        return Response(
            stream.getvalue(), 
            mimetype='application/vnd.apache.arrow.stream',
            headers={"Content-Disposition": "attachment; filename=data.arrow"}
        )
    
    except Exception as e:
        print(f"Error in get_arrow: {e}", flush=True)
        return jsonify({"error": str(e)}), 500
    
    finally:
        release_client(client)


@clickHouse_BP.route("/api/run_topic", methods=["POST"])
def run_topic():
    try:
        # Retrieve parameters from the POST body.
        request_data = request.get_json() or {}

        # generate job id to track progress on the frontend
        job_id = str(uuid.uuid4())

        parameters = {
            "job_id": job_id,
            "data_source": request_data.get("data_source", "api"),
            "subreddit": request_data.get("subreddit", ""),
            "option": request_data.get("option", "reddit_submissions"),
            "startDate": request_data.get("startDate", ""),
            "endDate": request_data.get("endDate", ""),
        }
        message = json.dumps(parameters)
        
        # Instantiate the TopicModelRpcClient.
        topic_rpc_client = TopicModelRpcClient()
        
        # Send the data to the RPC Client
        topic_rpc_client.send_job(message, job_id)
        
        # Return the job id to the frontend
        return jsonify({"job_id": job_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@clickHouse_BP.route("/api/get_result/<job_id>")
def get_result(job_id):
    # Fetch result from Redis
    result = redis.get_result(job_id)

    if result is None:
        return jsonify({"status": "processing"}), 202

    return jsonify({"result": json.loads(result)})


@clickHouse_BP.route("/api/progress/<job_id>")
def get_progress(job_id):
    # Fetch progress from Redis
    progress = redis.get_progress(job_id)
    
    if progress is None:
        return jsonify({"status": "processing"}), 202
    
    return jsonify(json.loads(progress))


@clickHouse_BP.route("/api/run_sentiment", methods=["POST"])
def run_sentiment():
    try:
        request_data = request.get_json() or {}
        topic_result = request_data.get("topic_result")
        raw_custom_keywords = request_data.get("custom_keywords", [])
        if isinstance(raw_custom_keywords, list):
            custom_keywords = raw_custom_keywords
        elif isinstance(raw_custom_keywords, str):
            custom_keywords = [raw_custom_keywords]
        else:
            return jsonify({"error": "custom_keywords must be an array of strings"}), 400

        if not isinstance(topic_result, dict):
            return jsonify({"error": "topic_result must be an object"}), 400

        # generate job id to track progress on the frontend
        job_id = str(uuid.uuid4())

        # Forward the existing topic payload and optionally inject custom keywords.
        payload = dict(topic_result)
        payload["job_id"] = job_id
        payload["custom_keywords"] = custom_keywords

        message = json.dumps(payload)
        SentimentAnalysisRpcClient().send_job(message, job_id)

        # Return the job id to the frontend
        return jsonify({"job_id": job_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _build_export_query(base_query: str, subreddit: str, search_value: str,
                        start_date: str | None, end_date: str | None) -> tuple[str, dict]:
    """
    Same pattern as _build_feed_query but for the export endpoint, which does
    not filter by author and does not need the LIMIT clause.
    """
    conditions = []
    parameters: dict = {}

    if subreddit:
        conditions.append("subreddit = {subreddit:String}")
        parameters["subreddit"] = subreddit

    if search_value:
        # Use search_value to filter by the body/selftext column.
        conditions.append("selftext LIKE concat('%', {search_value:String}, '%')")
        parameters["search_value"] = search_value

    if start_date:
        start_date_formatted = start_date.replace("T", " ").split(".")[0]
        conditions.append("created_utc >= toDateTime64({start_date:String}, 3)")
        parameters["start_date"] = start_date_formatted

    if end_date:
        end_date_formatted = end_date.replace("T", " ").split(".")[0]
        conditions.append("created_utc <= toDateTime64({end_date:String}, 3)")
        parameters["end_date"] = end_date_formatted

    query = base_query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_utc DESC"

    return query, parameters


@clickHouse_BP.route("/api/export_data", methods=["GET"])
def export_data():
    client = None
    try:
        option        = request.args.get('option', default='reddit_submissions')
        subreddit     = request.args.get('subreddit', '', type=str)
        search_value  = request.args.get('search_value', '', type=str)
        start_date    = request.args.get('startDate', None, type=str)
        end_date      = request.args.get('endDate', None, type=str)
        export_format = request.args.get('format', default='csv')

        if ',' in option:
            # If both options are selected, use a UNION ALL query.
            base_query = (
                "SELECT * FROM ("
                "    (SELECT subreddit, title, selftext, created_utc, id FROM reddit_submissions) "
                "    UNION ALL "
                "    (SELECT subreddit, '(Comment)' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments)"
                ") AS combined"
            )
        elif option == "reddit_submissions":
            base_query = "SELECT subreddit, title, selftext, created_utc, id FROM reddit_submissions"
        elif option == "reddit_comments":
            base_query = "SELECT subreddit, '(Comment)' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments"
        else:
            return jsonify({"error": "Invalid option provided."}), 400

        query, parameters = _build_export_query(
            base_query, subreddit, search_value, start_date, end_date
        )

        client = get_pooled_client()
        table = client.query_arrow(query, parameters=parameters, use_strings=True)

        if export_format == 'excel':
            df = table.to_pandas()
            import pytz
            local_tz = pytz.timezone("America/New_York")  # Adjust to your timezone.
            if 'created_utc' in df.columns:
                if pd.api.types.is_datetime64tz_dtype(df['created_utc']):
                    df['created_utc'] = df['created_utc'].dt.tz_convert(local_tz).dt.tz_localize(None)
                else:
                    df['created_utc'] = pd.to_datetime(df['created_utc'], utc=True).dt.tz_convert(local_tz).dt.tz_localize(None)
            output = BytesIO()
            df.to_excel(output, index=False, sheet_name="Reddit Export")
            output.seek(0)
            # Dynamically name the file using the subreddit value.
            filename = f"{subreddit}.xlsx" if subreddit else "reddit_export.xlsx"
            return Response(
                output.getvalue(),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif export_format == 'csv':
            df = table.to_pandas()
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            filename = f"{subreddit}.csv" if subreddit else "reddit_export.csv"
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif export_format == 'json':
            df = table.to_pandas()
            return jsonify(df.to_dict(orient='records'))
        elif export_format == 'arrow':
            stream = io.BytesIO()
            with ipc.new_stream(stream, table.schema) as writer:
                writer.write_table(table)
            stream.seek(0)
            return Response(
                stream.getvalue(),
                mimetype='application/vnd.apache.arrow.stream',
                headers={"Content-Disposition": "attachment; filename=data.arrow"}
            )
        else:
            return jsonify({"error": "Unsupported export format."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_client(client)
