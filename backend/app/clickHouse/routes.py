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


import io
import pandas as pd

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
    prefix = request.args.get('subreddit', '').strip()
    if not prefix:
        return jsonify([])

    client = None
    try:
        client = get_pooled_client()
        sql = """
            SELECT subreddit
            FROM subreddits
            WHERE lower(subreddit) LIKE %(prefix)s
            ORDER BY subreddit ASC
            LIMIT 10
        """
        params = {"prefix": prefix.lower() + "%"}
        qr = client.query(sql, parameters=params)
        rows = qr.result_rows
        return jsonify([row[0] for row in rows])
    except Exception:
        # If table doesn't exist or any error, return empty list
        return jsonify([])
    finally:
        if client:
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
            base_query = """
                SELECT * FROM (
                    SELECT subreddit, author, title, selftext, created_utc, id FROM reddit_submissions
                    UNION ALL
                    SELECT subreddit, author, '(Comment)' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments
                ) AS combined
            """
        elif option == "reddit_submissions":
            base_query = """
                SELECT subreddit, author, title, selftext, created_utc, id FROM reddit_submissions
            """
        else:
            base_query = """
                SELECT subreddit, author, '(Comment)' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments
            """

        conditions = ["author != 'AutoModerator'"]
        params = {}

        if subreddit:
            conditions.append("subreddit = %(subreddit)s")
            params["subreddit"] = subreddit

        if search_value:
            conditions.append("selftext LIKE %(search)s")
            params["search"] = f"%{search_value}%"

        if start_date:
            conditions.append("created_utc >= toDateTime64(%(start)s, 3)")
            params["start"] = start_date.replace("T", " ").split(".")[0]

        if end_date:
            conditions.append("created_utc <= toDateTime64(%(end)s, 3)")
            params["end"] = end_date.replace("T", " ").split(".")[0]

        query = base_query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_utc DESC LIMIT 9999999999999 OFFSET 0"


        client = get_pooled_client()
        if client is None:
            return jsonify({"error": "Failed to get ClickHouse client."}), 50

        # Use query_arrow to get an Arrow Table directly.
        start_time = time.time()
        table = client.query_arrow(query, parameters=params, use_strings=True)
        query_arrow_time = time.time() - start_time
        print(f"Query Arrow time: {query_arrow_time:.4f} seconds", flush=True)

        # Serialize the Arrow Table into a binary stream.
        start_time = time.time()
        stream = io.BytesIO()
        with ipc.new_stream(stream, table.schema) as writer:
            writer.write_table(table)
        serialization_time = time.time() - start_time
        print(f"Arrow serialization time: {serialization_time:.4f} seconds", flush=True)

        stream.seek(0)

        return Response(
            stream.getvalue(),
            mimetype='application/vnd.apache.arrow.stream',
            headers={"Content-Disposition": "attachment; filename=data.arrow"}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_client(client)


@clickHouse_BP.route("/api/export_data", methods=["GET"])
def export_data():
    client = None
    try:
        option = request.args.get('option', default='reddit_submissions')
        subreddit = request.args.get('subreddit', '', type=str)
        # Read our search parameter from a simpler key.
        search_value = request.args.get('search_value', '', type=str)
        start_date = request.args.get('startDate', None, type=str)
        end_date = request.args.get('endDate', None, type=str)
        export_format = request.args.get('format', default='csv')


        if ',' in option:
            base_query = """
                SELECT * FROM (
                    SELECT subreddit, title, selftext, created_utc, id FROM reddit_submissions
                    UNION ALL
                    SELECT subreddit, '(Comment)' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments
                ) AS combined
            """
        elif option == "reddit_submissions":
            base_query = "SELECT subreddit, title, selftext, created_utc, id FROM reddit_submissions"
        else:
            base_query = "SELECT subreddit, '(Comment)' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments"

        conditions = []
        params = {}

        if subreddit:
            conditions.append("subreddit = %(subreddit)s")
            params["subreddit"] = subreddit

        if search_value:
            conditions.append("selftext LIKE %(search)s")
            params["search"] = f"%{search_value}%"

        if start_date:
            conditions.append("created_utc >= toDateTime64(%(start)s, 3)")
            params["start"] = start_date.replace("T", " ").split(".")[0]

        if end_date:
            conditions.append("created_utc <= toDateTime64(%(end)s, 3)")
            params["end"] = end_date.replace("T", " ").split(".")[0]

        query = base_query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_utc DESC"

        client = get_pooled_client()
        table = client.query_arrow(query, parameters=params, use_strings=True)

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
