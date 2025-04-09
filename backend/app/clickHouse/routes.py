from flask import jsonify, request
from clickhouse_connect import get_client
from dotenv import load_dotenv
from queue import Queue
import os
import json
import pika
from . import clickHouse_BP
from ..rpc_client import TopicModelRpcClient  # Import the RPC client module

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
    connection_pool.put(client)

@clickHouse_BP.route("/api/get_all_click", methods=["GET"])
def get_all_click():
    try:
        length = request.args.get('length', default=9999999999999, type=int)
        start = request.args.get('start', default=0, type=int)
        draw = request.args.get('draw', default=1, type=int)
        option = request.args.get('option', default='reddit_submissions')
        subreddit = request.args.get('subreddit', '', type=str)
        client = get_pooled_client()
        search_value = request.args.get('search[value]', '', type=str)
        sentiment_keywords = request.args.get('sentimentKeywords', '', type=str)
        # Get datetime range from the query parameters (ISO strings)
        start_date = request.args.get('startDate', None, type=str)
        end_date = request.args.get('endDate', None, type=str)

        # Build the base query based on the option.
        if option == "reddit_submissions":
            base_query = "SELECT subreddit, title, selftext, created_utc, id FROM reddit_submissions"
        elif option == "reddit_comments":
            base_query = "SELECT subreddit, '' AS title, body AS selftext, created_utc, parent_id AS id FROM reddit_comments"
        else:
            return jsonify({"error": "Invalid option provided."}), 400

        # Build the conditions.
        conditions = []
        if subreddit:
            conditions.append(f"subreddit = '{subreddit}'")
        if search_value:
            if option == "reddit_submissions":
                conditions.append(f"(subreddit LIKE '%{search_value}%' OR title LIKE '%{search_value}%' OR selftext LIKE '%{search_value}%')")
            else:
                conditions.append(f"(subreddit LIKE '%{search_value}%' OR body LIKE '%{search_value}%')")
        if sentiment_keywords:
            if option == "reddit_submissions":
                conditions.append(f"(title LIKE '%{sentiment_keywords}%' OR selftext LIKE '%{sentiment_keywords}%')")
            else:
                conditions.append(f"(body LIKE '%{sentiment_keywords}%')")
        # Reformat and add date conditions if provided.
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
        query += f" LIMIT {length} OFFSET {start}"

        print("Executing query:", query, flush=True)

        result = client.query(query)
        data = result.result_rows

        # Build the count query.
        if option == "reddit_submissions":
            count_query = "SELECT COUNT(*) FROM reddit_submissions"
        else:
            count_query = "SELECT COUNT(*) FROM reddit_comments"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
        total_result = client.query(count_query)
        total_records = total_result.result_rows[0][0]

        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": data
        })

    except Exception as e:
        print(e, flush=True)
        return jsonify({"error": str(e)}), 500
    finally:
        release_client(client)

@clickHouse_BP.route("/api/run_sentiment", methods=["POST"])
def run_sentiment():
    try:
        # Retrieve parameters from the POST body.
        request_data = request.get_json() or {}
        parameters = {
            "data_source": request_data.get("data_source", "api"),
            "subreddit": request_data.get("subreddit", ""),
            "option": request_data.get("option", "reddit_submissions"),
            "startDate": request_data.get("startDate", ""),   # Passed as ISO string
            "endDate": request_data.get("endDate", "")          # Passed as ISO string
            # Add any additional parameters as needed.
        }
        message = json.dumps(parameters)
        rpc_client = TopicModelRpcClient()
        result = rpc_client.call(message)
        return jsonify({"result": json.loads(result)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
