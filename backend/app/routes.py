from flask import Blueprint, request, render_template, redirect, url_for, flash
from datetime import datetime, timezone
#will be needed when implmenting search history table, work with firebase user table
from app.models import SearchHistory
from app.extensions import db

main = Blueprint("main", __name__)

#Search History Table Functions
@main.route("/api/get_search", methods=["GET"])
def getSearch():
    return {"temp"}, 404

#<int:search_id>
@main.route("/api/remove_search/<int:search_id>", methods=['DELETE'])
def removeSearch():
    return {"temp"}, 404

@main.route("/api/clear_all", methods=["DELETE"])
def clearAll():
    return {"temp"}, 404
