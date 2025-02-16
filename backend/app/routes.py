from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user
from datetime import datetime, timezone

from app.models import Users, SearchHistory
from app.extensions import db

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    #when using the website the search query will also use the pullRedditData.py here?
    search_query = []

    if request.method == "POST":
        search_query = request.form['search_query']
        user = Users.query.filter_by(username=current_user.username).first()

        if user:
            search = SearchHistory(user_id=current_user.user_id, search_query=search_query, created_utc=datetime.now(timezone.utc))
            db.session.add(search)
            db.session.commit()

            #call search
        else:
            #call search without adding to search history
            flash('not done')

    return render_template("index.html")

#add remove search history functions
#link search history query to the search itself
@main.route("/profile")
@login_required
def profile():
    user = Users.query.filter_by(username=current_user.username).first()
    
    if user:
        #cant get full list of searches
        search_history = db.session.query(SearchHistory).join(Users).filter(SearchHistory.user_id == current_user.user_id).order_by(SearchHistory.created_utc.desc()).all()
        return render_template('profile.html', username=current_user.username, search_history=search_history, search_history_count=current_user.user_id)
    else:
        search_history = []
        flash("User is not logged in.", "warning")
        return redirect(url_for("main.index"))

#remove a search, and remove all searches?
#def removeSearch():