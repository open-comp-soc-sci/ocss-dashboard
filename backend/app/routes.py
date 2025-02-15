from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user

from app.models import Users

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

#get user search history?
#single table with foreign key, store search query and timestamp
@main.route("/profile")
@login_required
def profile():
    user = Users.query.filter_by(username=current_user.username).first()
    
    if user:
        return render_template('profile.html', username=current_user.username)
    else:
        flash("User is not logged in.", "warning")
        return redirect(url_for("main.index"))