from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import uuid, re

from app.extensions import db
from app.models import Users

auth = Blueprint('auth', __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #do we want to include this function to remember the user
        remember = True if request.form.get('remember') else False
        
        #get user
        user = Users.query.filter_by(username=request.form.get('username')).first()

        #check password hash
        if not user or not check_password_hash(user.password, request.form.get('password')):
            flash("Invalid username or password", "error")
            return redirect(url_for("auth.login"))
        else:
           #upon success, login
           login_user(user, remember=remember)
           return redirect(url_for('main.profile'))
        
    return render_template("login.html")

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #email = request.form.get('email')

        #password not entered
        if not request.form["password"]:
            flash('Enter a valid password.')
            return(redirect(url_for('auth.register')))
        
        #password parameters
        password_regex = r'^(?=.*[A-Z])(?=.*[\W_]).{8,}$'

        #display password requirements on frontend?
        if not re.match(password_regex, request.form["password"]):
            flash('8 characters, 1 uppercase letter, 1 special character')
            return redirect(url_for('auth.register'))

        #get user
        user = Users.query.filter_by(username=request.form.get('username')).first()
        if user: 
            flash('Username already exists')
            return redirect(url_for('auth.register'))

        #generate unique uuid
        user_id = uuid.uuid4()
        while Users.query.filter_by(user_id=user_id).first():
            user_id = uuid.uuid4()

        #hash password
        hashed_password = generate_password_hash(request.form["password"])
        new_user = Users(user_id=user_id, username=request.form["username"], password=hashed_password)
        
        #add user to database
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    
    return redirect(url_for("main.index")) 