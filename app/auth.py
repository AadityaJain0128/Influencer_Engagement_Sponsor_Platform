from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Influencer, Sponsor, Category
from . import db


auth = Blueprint("auth", __name__)


@auth.route("/signup", methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        flash("You are already logged in !", category="warning")
        return redirect("/")
    
    options = Category.query.all()
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")

        flag = True
        if User.query.filter_by(email=email).first():
            flag = False
            flash("This Email ID already exists !", category="danger")
        elif User.query.filter_by(username=username).first():
            flag = False
            flash("This Username is not available !", category="danger")

        role = request.form.get("role")
        password = request.form.get("password")

        if role == "influencer":
            name = request.form.get("full_name")
            niche = request.form.get("niche")
            if not flag:
                return render_template("sign-up.html", full_name=name, niche=niche, role=role, username=username, email=email, options=options)
            
            user = User(username=username, email=email, password=generate_password_hash(password), role=role)
            influencer = Influencer(username=username, name=name, niche=niche)

            db.session.add(user)
            db.session.add(influencer)
            
        else:
            name = request.form.get("company_name")
            industry = request.form.get("industry")
            if not flag:
                return render_template("sign-up.html", company_name=name, industry=industry, role=role, username=username, email=email, options=options)

            user = User(username=username, email=email, password=generate_password_hash(password), role=role)
            sponsor = Sponsor(username=username, name=name, industry=industry)

            db.session.add(user)
            db.session.add(sponsor)


        db.session.commit()
        flash("Account Created Successfully !", category="success")
        return redirect(url_for("auth.login"))
        
    return render_template("sign-up.html", options=options)


@auth.route("/login", methods=['GET', 'POST'])
def login():
    next_page = request.args.get("next", "/")
    if current_user.is_authenticated:
        flash("You are already logged in !", category="warning")
        return redirect(next_page)
    
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("User does not exists with this credentials !", category="danger")
            return render_template("login.html", username=username)
        
        if not check_password_hash(user.password, password):
            flash("Incorrect Password !", category="danger")
            return render_template("login.html", username=username)
        
        flash("Logged In Successfully !", category="success")
        login_user(user, remember=True)
        return redirect(next_page)
    return render_template("login.html")


# @auth.route("/admin/login", methods=['GET', 'POST'])
# def admin_login():
#     next_page = request.args.get("next", "/")
#     if current_user.is_authenticated:
#         flash("You are already logged in !", category="warning")
#         return redirect(next_page)
    
#     if request.method == "POST":
#         username = request.form.get("username", "")
#         password = request.form.get("password", "")
#         user = User.query.filter_by(username=username).first()
#         if not user:
#             flash("User does not exists with this credentials !", category="danger")
#             return render_template("admin_login.html", username=username)
        
#         if not check_password_hash(user.password, password):
#             flash("Incorrect Password !", category="danger")
#             return render_template("admin_login.html", username=username)
        
#         flash("Logged In Successfully !", category="success")
#         login_user(user, remember=True)
#         return redirect("/")
#     return render_template("admin_login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged Out !", category="success")
    return redirect(url_for("auth.login"))