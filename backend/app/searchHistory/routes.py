from flask import jsonify, request
from datetime import datetime, timezone
from app.models import SearchHistory
from app.models import ResultData
from app.models import TopicData
from app.extensions import db
from . import searchHistory_BP

#Search Table Functions
@searchHistory_BP.route("/api/add_search", methods=["POST"])
def addSearch():
    data = request.get_json()
    subreddit = data.get("subreddit")
    subreddit = subreddit.lower()
    sentimentKeywords = data.get("sentimentKeywords")
    startDate = data.get("startDate")
    endDate = data.get("endDate")
    option = data.get("option")
    email = data.get("email")

    new_search = SearchHistory(
        email=email,
        subreddit=subreddit,
        sentimentKeywords=sentimentKeywords,
        startDate=startDate,
        endDate=endDate,
        option=option,
        created_utc=datetime.now(timezone.utc)
    )

    db.session.add(new_search)
    db.session.commit()
    return jsonify({"search_id": new_search.id}), 201

#Search History Table Functions
@searchHistory_BP.route("/api/get_search/<string:email>", methods=["GET"])
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
                "option": item.option,
                "created_utc": item.created_utc.strftime("%Y-%m-%d %H:%M:%S")
            }
            for item in search_data
        ]
        return jsonify({"search_history": search_form}), 200
    else:
        return jsonify({"search_history": []}), 200

@searchHistory_BP.route("/api/remove_search/<int:search_id>", methods=['DELETE'])
def removeSearch(search_id):
    search = SearchHistory.query.get(search_id)
    if search:
        db.session.delete(search)
        db.session.commit()
        return jsonify({"message": "Search removed."}), 200
    else:
        return jsonify({"message": "Search remove failed."}), 404

@searchHistory_BP.route("/api/clear_all/<string:email>", methods=["DELETE"])
def clearAll(email):
    search_data = SearchHistory.query.filter_by(email=email).all()

    if search_data:
        for search in search_data:
            db.session.delete(search)
        db.session.commit()
        return jsonify({"message": "Searches cleared."}), 200
    else:
        return jsonify({"message": "Search clear failed."}), 404
    
@searchHistory_BP.route("/api/save_result", methods=["POST"])
def saveResult():
    data = request.get_json()

    try:
        new_result = ResultData(
            email=data["email"],
            subreddit=data["subreddit"],
            startDate=datetime.strptime(data["startDate"], "%Y-%m-%d").date(),
            endDate=datetime.strptime(data["endDate"], "%Y-%m-%d").date()
        )
        db.session.add(new_result)
        db.session.commit()

        groups = data['groups']
        for group in groups:
            topicCluster = TopicData(
                email=data["email"],
                result_id=new_result.id,
                group_number=group['group'],
                topic_label=group['topic_label'],
                topics=group['topics'],
                post_count=group['post_count']
            )
            db.session.add(topicCluster)
        db.session.commit()


        return jsonify({"message": "Saved successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@searchHistory_BP.route("/api/get_result", methods=["GET"])
def getResult():
    try:
        results = ResultData.query.order_by(ResultData.created_utc.desc()).all()

        results_data = []
        for result in results:
             # 3 Highest Post Count Groups
            resultGroups = (
                TopicData.query
                .filter_by(result_id=result.id)
                .order_by(TopicData.post_count.desc())
                .limit(3)
                .all()
            )

            resultLabels = [group.topic_label for group in resultGroups]
            # Some topic clusters may have less than three groups
            while len(resultLabels) < 3:
                resultLabels.append("N/A")

            results_data.append({
                "id": result.id,
                "email": result.email,
                "subreddit": result.subreddit,
                "startDate": result.startDate.isoformat(),
                "endDate": result.endDate.isoformat(),
                "created_utc": result.created_utc.isoformat(),
                "topic1": resultLabels[0],
                "topic2": resultLabels[1],
                "topic3": resultLabels[2],
            })

        return jsonify({"results": results_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@searchHistory_BP.route("/api/get_topics/<int:result_id>", methods=["GET"])
def getTopics(result_id):
    try:
        topics = TopicData.query.filter_by(result_id=result_id).all()

        if not topics:
            return jsonify({"error": "There are no topic clusters for this result."}), 404

        resultTopics = []
        for topic in topics:
            resultTopics.append({
                "id": topic.id,
                "group_number": topic.group_number,
                "topic_label": topic.topic_label,
                "topics": topic.topics,
                "post_count": topic.post_count
            })

        return jsonify({"topics": resultTopics}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@searchHistory_BP.route("/api/remove_result/<int:id>", methods=["DELETE"])
def removeResult(id):
    result = ResultData.query.get(id)

    if result:
        db.session.delete(result)
        db.session.commit()
        return jsonify({"message": "Result removed."}), 200
    else:
        return jsonify({"message": "Result remove failed."}), 404