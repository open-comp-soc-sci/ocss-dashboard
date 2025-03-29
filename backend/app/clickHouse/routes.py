from flask import Blueprint, jsonify, request
from clickhouse_connect import get_client
from dotenv import load_dotenv
import os
import json
import pika
from . import clickHouse_BP
from ..rpc_client import TopicModelRpcClient  # Import the RPC client module


load_dotenv()
def get_new_client():
    return get_client(
    host=os.getenv('CH_HOST'),
    port=os.getenv('CH_PORT'),
    database=os.getenv('CH_DATABASE'),
    username=os.getenv('CH_USER'),
    password=os.getenv('CH_PASSWORD')
    
)

@clickHouse_BP.route("/api/get_click", methods=["GET"])
def get_click():
    subreddit = request.args.get('subreddit', None)
    option = request.args.get('option', 'reddit_submissions')

    print('hello')
    print(subreddit)
    client = get_new_client()

    try:
        if option == "reddit_submissions":
            query = (
                f"SELECT id, subreddit, title, selftext, created_utc "
                f"FROM reddit_submissions WHERE subreddit = '{subreddit}' LIMIT 10;"
            )
        elif option == "reddit_comments":
            query = (
                f"SELECT id, parent_id, subreddit, body, created_utc "
                f"FROM reddit_comments WHERE subreddit = '{subreddit}' LIMIT 10;"
            )
        else:
            return jsonify({"error": "Invalid option provided."}), 400

        result = client.query(query)
        data = result.result_rows
        return jsonify(data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@clickHouse_BP.route("/api/get_all_click", methods=["GET"])
def get_all_click():
    try:
        length = request.args.get('length', default=10, type=int)
        start = request.args.get('start', default=0, type=int)
        draw = request.args.get('draw', default=1, type=int)
        option = request.args.get('option', default='reddit_submissions')
        subreddit = request.args.get('subreddit', '', type=str)
        client = get_new_client()
        search_value = request.args.get('search[value]', '', type=str)

        # Build the base query based on the option.
        if option == "reddit_submissions":
            base_query = "SELECT subreddit, title, selftext, created_utc, id FROM reddit_submissions"
        elif option == "reddit_comments":
            base_query = "SELECT subreddit, '' AS title, body AS selftext, created_utc, id FROM reddit_comments"
        else:
            return jsonify({"error": "Invalid option provided."}), 400

        # Build the conditions.
        conditions = []
        if subreddit:
            conditions.append(f"subreddit = '{subreddit}'")
        if search_value:
            conditions.append(f"(subreddit LIKE '%{search_value}%' OR title LIKE '%{search_value}%' OR selftext LIKE '%{search_value}%')")

        query = base_query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        # Add ORDER BY after the WHERE clause
        query += " ORDER BY created_utc DESC"
        query += f" LIMIT {length} OFFSET {start}"

        print("Executing query:", query, flush=True)  # Debug output

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


@clickHouse_BP.route("/api/run_sentiment", methods=["POST"])
def run_sentiment():
    try:
        # Retrieve parameters from the POST body.
        request_data = request.get_json() or {}
        parameters = {
            "subreddit": request_data.get("subreddit", ""),
            "option": request_data.get("option", "reddit_submissions")
            # Add any additional parameters as needed.
        }
        message = json.dumps(parameters)
        rpc_client = TopicModelRpcClient()
        result = rpc_client.call(message)
        return jsonify({"result": json.loads(result)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500