from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
from app.models import SearchHistory
from app.extensions import db

main = Blueprint("main", __name__)

#Search Query Functions
#This should interact with the other code
#Test interaction with clickhouse database
@main.route("/api/add_search", methods=["POST"])
def addSearch():
    data = request.get_json()

    search_query = data.get("search_query")
    email = data.get("email")

    new_search = SearchHistory(
        email=email,
        search_query=search_query,
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
                "search_query": item.search_query,
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