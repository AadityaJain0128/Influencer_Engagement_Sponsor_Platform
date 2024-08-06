from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import current_user, login_required


views = Blueprint("views", __name__)


@views.route("/")
@login_required
def home():
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif current_user.role == "influencer":
        return redirect(url_for("influencer.dashboard"))
    elif current_user.role == "sponsor":
        return redirect(url_for("sponsor.dashboard"))
    else:
        return "<h1>Not a valid Role !</h1>"
    

@views.route("/flagged")
def flagged_user():
    if not current_user.is_authenticated:
        return redirect("/")
    
    if not current_user.flagged:
        return redirect("/")

    return render_template("flagged_user.html")


@views.errorhandler(404)
def _404_not_found_(e):
    if current_user.is_authenticated:
        flash("Try Logging In Again !")
        return redirect(url_for("auth.logout"))
    flash("Try Logging In !")
    return redirect(url_for("auth.login"))