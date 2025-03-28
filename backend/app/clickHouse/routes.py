from flask import Blueprint, jsonify, request
from clickhouse_connect import get_client
from dotenv import load_dotenv
import os
import json
import pika
from . import clickHouse_BP
from ..rpc_client import TopicModelRpcClient  # Import the RPC client module


load_dotenv()
client = get_client(
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
        length = int(request.args.get('length', 10))
        start = int(request.args.get('start', 0))
        draw = int(request.args.get('draw', 1))
        #search_value = request.args.get('search[value]', '')
        #do we want to search on this data table, yes

        #add in link with id later
        query = f"""
            SELECT subreddit, title, selftext, created_utc
            FROM reddit_submissions
            LIMIT {length} OFFSET {start}
        """
        result = client.query(query)
        data = result.result_rows
        count_query = "SELECT COUNT(*) FROM reddit_submissions"
        total_result = client.query(count_query)
        total_records = total_result.result_rows[0][0]

        return jsonify({
            "draw": draw, 
            "recordsTotal": total_records,  
            "recordsFiltered": total_records, 
            "data": data 
        })

    except Exception as e:
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