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
    
    new_result = ResultData(
            email=data["email"],
            subreddit=data["subreddit"],
            startDate=datetime.strptime(data["startDate"], "%Y-%m-%d").date(),
            endDate=datetime.strptime(data["endDate"], "%Y-%m-%d").date()
        )
    db.session.add(new_result)
    db.session.commit()

    groups_raw = data["groups"]
    groups = []

    for item in groups_raw:
        if isinstance(item, dict):
            groups.append(item)
        elif isinstance(item, list):
            for subitem in item:
                if isinstance(subitem, dict):
                    groups.append(subitem)
    
    try:
        for group in groups:
            topics = group.get('topics', [])
            print("PROCESSING GROUP:", topics)

            topics_list = [
                {
                    "topicNumber": topic["topicNumber"],
                    "ctfidfKeywords": topic["ctfidfKeywords"],
                    "postCount": topic["postCount"],
                    "topicLabel": topic["topicLabel"]
                }
                for topic in topics
            ]

            example_posts = [
                {
                    "topicNumber": topic["topicNumber"],
                    "samplePost": topic["samplePosts"]
                }
                for topic in topics
            ]

            topicCluster = TopicData(
                email=data["email"],
                result_id=new_result.id,
                group_number=group['group'],
                group_label=group['llmLabel'],
                topics=topics_list,
                example_posts=example_posts
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
                .all()
            )

            topics_info = []
            for group in resultGroups:
                for topic in group.topics:  # Iterate through each topic in the 'topics' JSON
                    topic_info = {
                        "topicNumber": topic.get("topicNumber"),
                        "topicLabel": topic.get("topicLabel"),
                        "postCount": topic.get("postCount"),
                    }
                    topics_info.append(topic_info)

            sorted_topics = sorted(topics_info, key=lambda x: x["postCount"], reverse=True)
            top_3_topics = sorted_topics[:3]

            resultLabels = [top_3_topics[i]["topicLabel"] if i < len(top_3_topics) else "N/A" for i in range(3)]
            resultCounts = [top_3_topics[i]["postCount"] if i < len(top_3_topics) else 0 for i in range(3)]

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
                "topic1Count": resultCounts[0],
                "topic2Count": resultCounts[1],
                "topic3Count": resultCounts[2],
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
           for topic_item in topic.topics:
                resultTopics.append({
                    "id": topic.id,
                    "group_number": topic.group_number,
                    "topic_number": topic_item.get("topicNumber"),
                    "group_label": topic.group_label,
                    "topicLabel": topic_item.get("topicLabel"),
                    "ctfidfKeywords": topic_item.get("ctfidfKeywords"),
                    "postCount": topic_item.get("postCount"),
                    "example_posts": topic.example_posts
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