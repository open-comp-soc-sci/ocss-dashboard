from flask import Blueprint, jsonify, request
from clickhouse_connect import get_client
from dotenv import load_dotenv
import os
from . import clickHouse_BP

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

    try:
        query = f"SELECT subreddit, title, selftext FROM reddit_submissions WHERE subreddit = '{subreddit}' LIMIT 10;"
        result = client.query(query)

        data = result.result_rows
        return jsonify(data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
