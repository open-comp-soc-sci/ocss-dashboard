from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
from clickhouse_connect import get_client
from app.models import SearchHistory
from app.extensions import db
from dotenv import load_dotenv
import os

main = Blueprint("main", __name__)

#Search Query Functions
#This should interact with the other code
#Test interaction with clickhouse database
@main.route("/api/add_search", methods=["POST"])
def addSearch():
    data = request.get_json()

    subreddit = data.get("subreddit")
    sentimentKeywords = data.get("sentimentKeywords")
    startDate = data.get("startDate")
    endDate = data.get("endDate")
    email = data.get("email")

    new_search = SearchHistory(
        email=email,
        subreddit=subreddit,
        sentimentKeywords=sentimentKeywords,
        #temp dates, wait for frontend date selector creation
        startDate=startDate,
        endDate=endDate,
        created_utc=datetime.now(timezone.utc)
    )

    #Could include try here, not sure if any parameters can fail this though
    db.session.add(new_search)
    db.session.commit()
    return jsonify({"search_id": new_search.id}), 201

#Search History Table Functions
@main.route("/api/get_search/<string:email>", methods=["GET"])
def getSearch(email):
    search_data = SearchHistory.query.filter_by(email=email).all()

    if search_data:
        search_form = [
            {
                "search_id": item.id,
                "subreddit": item.subreddit,
                "sentimentKeywords": item.sentimentKeywords,
                "startDate": item.startDate,
                "endDate": item.endDate,
                "created_utc": item.created_utc.strftime("%Y-%m-%d %H:%M:%S")
            }
            for item in search_data
        ]
        return jsonify({"search_history": search_form}), 200
    else:
        return jsonify({"message": "Search history empty."}), 404

@main.route("/api/remove_search/<int:search_id>", methods=['DELETE'])
def removeSearch(search_id):
    return 404

@main.route("/api/clear_all/<string:email>", methods=["DELETE"])
def clearAll(email):
    return 404

load_dotenv()
client = get_client(
    host=os.getenv('CH_HOST'),
    port=os.getenv('CH_PORT'),
    database=os.getenv('CH_DATABASE'),
    username=os.getenv('CH_USER'),
    password=os.getenv('CH_PASSWORD')
    
)

@main.route("/api/get_click", methods=["GET"])
def get_click():
    subreddit = request.args.get('subreddit', None)

    try:
        query = f"SELECT subreddit, title, selftext FROM reddit_submissions WHERE subreddit = '{subreddit}' LIMIT 10;"
        result = client.query(query)

        data = result.result_rows
        return jsonify(data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
