from flask import Blueprint, jsonify, request
from datetime import datetime, timezone, date
from app.models import SearchHistory
from app.extensions import db

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
