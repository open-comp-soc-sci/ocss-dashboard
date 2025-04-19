from flask import jsonify, request, Response
from clickhouse_connect import get_client
from dotenv import load_dotenv
import pyarrow as pa
import pyarrow.ipc as ipc
from queue import Queue
import os
import json
import pika
from . import clickHouse_BP
from ..rpc_client import TopicModelRpcClient  # Import the RPC client modules
from ..rpc_client import SentimentAnalysisRpcClient 

import csv
import io
import pandas as pd
from openpyxl import Workbook
from io import BytesIO
import time

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
    client = None
    try:
        subreddit = request.args.get('subreddit', '')
        
        subreddit_query = f"""
        SELECT DISTINCT subreddit FROM (
            SELECT subreddit FROM reddit_submissions
            UNION ALL
            SELECT subreddit FROM reddit_comments
        )
        WHERE subreddit ILIKE '%{subreddit}%'
        GROUP BY subreddit
        ORDER BY COUNT(*) DESC
        LIMIT 10
        """

        client = get_pooled_client()
        if client is None:
            return jsonify({"error": "Failed to get ClickHouse client."}), 500

        result = client.query_arrow(subreddit_query)

        if not result:
            return jsonify({"message": "No subreddits found.", "subreddits": []}), 200

        subreddit_list = result.column('subreddit').to_pylist()
        print("results", subreddit_list)
        return jsonify(subreddit_list)
    
    except Exception as e:
        print(f"Error in search_list: {e}", flush=True)
        return jsonify({"error": str(e)}), 500
    
    finally:
        release_client(client)

@clickHouse_BP.route("/api/get_arrow", methods=["GET"])
def get_arrow():
    client = None
    try:
        # Retrieve query parameters.
        subreddit = request.args.get('subreddit', '')
        # subreddit = subreddit.lower()
        start_date = request.args.get('startDate', None)
        end_date = request.args.get('endDate', None)
        option = request.args.get('option', 'reddit_comments')  # Default to comments if not specified
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

        conditions = []
        if subreddit:
            conditions.append(f"subreddit = '{subreddit}'")
        if start_date:
            start_date_formatted = start_date.replace("T", " ").split(".")[0]
            conditions.append(f"created_utc >= toDateTime64('{start_date_formatted}', 3)")
        if end_date:
            end_date_formatted = end_date.replace("T", " ").split(".")[0]
            conditions.append(f"created_utc <= toDateTime64('{end_date_formatted}', 3)")
        if search_value:
            conditions.append(f"selftext LIKE '%{search_value}%'")

        # Add condition to filter out posts by AutoModerator.
        conditions.append("author != 'AutoModerator'")
        
        query = base_query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_utc DESC"
        query += " LIMIT 9999999999999 OFFSET 0"
        
        client = get_pooled_client()
        if client is None:
            return jsonify({"error": "Failed to get ClickHouse client."}), 500

        
        # Use query_arrow to get an Arrow Table directly.
        start_time = time.time()
        table = client.query_arrow(query, use_strings=True)
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
        parameters = {
            "data_source": request_data.get("data_source", "api"),
            "subreddit": request_data.get("subreddit", ""),
            "option": request_data.get("option", "reddit_submissions"),
            "startDate": request_data.get("startDate", ""),
            "endDate": request_data.get("endDate", "")
        }
        message = json.dumps(parameters)
        
        # Instantiate the TopicModelRpcClient.
        topic_rpc_client = TopicModelRpcClient()
        
        # Call the topic modeling RPC client and capture the result.
        result = topic_rpc_client.call(message)
        
        # Return the topic clustering result directly to the frontend.
        return jsonify({"result": json.loads(result)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@clickHouse_BP.route("/api/run_sentiment", methods=["POST"])
def run_sentiment():
    topic_result = request.get_json().get("topic_result")
    # just forward the full thing:
    message = json.dumps(topic_result)
    result = SentimentAnalysisRpcClient().call(message)
    return jsonify({"result": json.loads(result)}), 200


@clickHouse_BP.route("/api/export_data", methods=["GET"])
def export_data():
    try:
        option = request.args.get('option', default='reddit_submissions')
        subreddit = request.args.get('subreddit', '', type=str)
        # subreddit = subreddit.lower()
        # Read our search parameter from a simpler key.
        search_value = request.args.get('search_value', '', type=str)
        start_date = request.args.get('startDate', None, type=str)
        end_date = request.args.get('endDate', None, type=str)
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
        conditions = []
        if subreddit:
            conditions.append(f"subreddit = '{subreddit}'")
        # Use search_value to filter by the body/selftext column.
        if search_value:
            conditions.append(f"selftext LIKE '%{search_value}%'")
        if start_date:
            start_date_formatted = start_date.replace("T", " ").split(".")[0]
            conditions.append(f"created_utc >= toDateTime64('{start_date_formatted}', 3)")
        if end_date:
            end_date_formatted = end_date.replace("T", " ").split(".")[0]
            conditions.append(f"created_utc <= toDateTime64('{end_date_formatted}', 3)")

        query = base_query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_utc DESC"

        client = get_pooled_client()
        table = client.query_arrow(query, use_strings=True)

        # Process different export formats...
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
            return Response(
                output.getvalue(), 
                mimetype='text/csv', 
                headers={"Content-Disposition": f"attachment; filename={subreddit}.csv" if subreddit else "attachment; filename=reddit_export.csv"}
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
