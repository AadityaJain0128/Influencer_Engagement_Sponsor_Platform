from flask import Blueprint, redirect, render_template, url_for, flash, request
from flask_login import current_user, login_required
from .models import Influencer, Sponsor, Campaign, Category, Rating, User, Admin, Transaction, Request
from . import db
from werkzeug.security import generate_password_hash


admin = Blueprint("admin", __name__)


@admin.route("/")
@admin.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    users = User.query
    user_labels = ["Admin", "Sponsor", "Influencer"]
    user_values = [len(users.filter_by(role="admin").all()), len(users.filter_by(role="sponsor").all()), len(users.filter_by(role="influencer").all())]

    campaigns = Campaign.query
    active_campaigns = campaigns.filter(Campaign.completed == False, Campaign.influencer_id.isnot(None)).all()
    pending_campaigns = campaigns.filter(Campaign.completed == False, Campaign.influencer_id.is_(None)).all()
    completed_campaigns = campaigns.filter_by(completed=True).all()
    campaign_labels = ["Active Campaigns", "Pending Campaigns", "Completed Campaigns"]
    campaign_values = [len(active_campaigns), len(pending_campaigns), len(completed_campaigns)]

    campaign_ids = [c.id for c in Campaign.query.filter_by(paid=True).all()]
    transactions = Transaction.query.filter(Transaction.campaign_id.in_(campaign_ids)).all()
    transaction_labels = [t.campaign.name for t in transactions]
    transaction_values = [t.amount for t in transactions]

    flagged_labels = ["Flagged Campaigns", "UnFlagged Campaigns"]
    flagged_values = [len(campaigns.filter_by(flagged=True).all()), len(campaigns.filter_by(flagged=False).all())]

    categories = Category.query.all()
    category_labels = [c.name for c in categories]

    i = Influencer.query
    i_values = [len(i.filter_by(niche=c.name).all()) for c in categories]

    s = Sponsor.query
    s_values = [len(s.filter_by(industry=c.name).all()) for c in categories]

    req = Request.query
    request_labels = ["Influencer", "Sponsor"]
    request_values = [len(req.filter_by(sent_by="influencer").all()), len(req.filter_by(sent_by="sponsor").all())]

    status_labels = ["Public", "Private"]
    status_values = [len(campaigns.filter_by(visibility="public").all()), len(campaigns.filter_by(visibility="private").all())]

    return render_template("admin_dashboard.html", user_labels=user_labels, user_values=user_values, campaign_labels=campaign_labels, campaign_values=campaign_values, transaction_labels=transaction_labels, transaction_values=transaction_values, flagged_labels=flagged_labels, flagged_values=flagged_values, category_labels=category_labels, i_values=i_values, s_values=s_values, request_labels=request_labels, request_values=request_values, status_labels=status_labels, status_values=status_values, Sponsor=Sponsor, Influencer=Influencer)


@admin.route("/campaigns/<int:id>")
@login_required
def campaign_view(id):
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaign = Campaign.query.filter_by(id=id).first()
    if not campaign:
        flash("This Campaign does not exists !", category="danger")
        return redirect(url_for("admin.dashboard"))
    
    return render_template("admin_campaign_view.html", campaign=campaign, Influencer=Influencer)


@admin.route("/campaigns/<int:id>/delete", methods=['POST'])
@login_required
def campaign_delete(id):
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaign = Campaign.query.filter_by(id=id).first()
    if not campaign:
        flash("This Campaign does not exists !", category="danger")
        return redirect(url_for("admin.dashboard"))
    
    for r in campaign.requests:
        db.session.delete(r)
    db.session.delete(campaign)
    db.session.commit()

    flash("Campaign Deleted !", category="success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/find/campaigns")
@login_required
def find_campaigns():
    if current_user.role != "admin":
        return redirect("/")

    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    cname = request.args.get("cname", "")
    sname = request.args.get("sname", "")

    campaigns = Campaign.query.filter_by(completed=False, flagged=False)
    if cname:
        campaigns = campaigns.filter(Campaign.name.contains(cname))
    if sname:
        campaigns = campaigns.filter(Campaign.sponsor.has(Sponsor.name.contains(sname)) | Campaign.sponsor.has(Sponsor.username.contains(sname)))
    
    campaigns = campaigns.all()
    return render_template("admin_find_campaigns.html", campaigns=campaigns, cname=cname, sname=sname, Influencer=Influencer)


@admin.route("/find/sponsors")
@login_required
def find_sponsors():
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    name = request.args.get("name", "")
    industry = request.args.get("industry", "")

    sponsors = Sponsor.query.filter(Sponsor.user.has(User.flagged==False))
    if name:
        sponsors = sponsors.filter(Sponsor.name.contains(name) | Sponsor.username.contains(name))
    if industry:
        sponsors = sponsors.filter_by(industry=industry)

    sponsors = sponsors.all()
    categories = Category.query.all()
    return render_template("admin_find_sponsors.html", sponsors=sponsors, name=name, industry=industry, categories=categories, Campaign=Campaign)


@admin.route("/find/influencers")
@login_required
def find_influencers():
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    name = request.args.get("name", "")
    niche = request.args.get("niche", "")

    influencers = Influencer.query.filter(Influencer.user.has(User.flagged==False))
    if name:
        influencers = influencers.filter(Influencer.name.contains(name) | Influencer.username.contains(name))
    if niche:
        influencers = influencers.filter_by(niche=niche)

    influencers = influencers.all()
    avg_ratings = {}
    for i in influencers:
        ratings = Rating.query.filter_by(influencer_id=i.id).all()
        if ratings:
            avg_ratings[i] = [round(sum([r.rating for r in ratings]) / len(ratings), 1), len(ratings)]

    categories = Category.query.all()
    return render_template("admin_find_influencers.html", influencers=influencers, name=name, niche=niche, categories=categories, avg_ratings=avg_ratings)


@admin.route("/users/flagged")
@login_required
def flagged_users():
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    username = request.args.get("username", "")
    role = request.args.get("role", "")
    users = User.query.filter_by(flagged=True)
    if username:
        users = users.filter(User.username.contains(username))
    if role:
        users = users.filter_by(role=role)

    users = users.all()
    return render_template("admin_flagged_users.html", users=users, username=username, role=role)


@admin.route("/users/flagged/add/<username>", methods=['POST'])
@login_required
def flag_user(username):
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    user = User.query.filter_by(username=username).first()
    user.flagged = True
    db.session.commit()

    flash("User has been Flagged !", category="success")
    return redirect(url_for("admin.flagged_users"))


@admin.route("/users/flagged/remove/<username>", methods=['POST'])
@login_required
def unflag_user(username):
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    user = User.query.filter_by(username=username).first()
    user.flagged = False
    db.session.commit()

    flash("User has been UnFlagged !", category="success")
    return redirect(url_for("admin.flagged_users"))


@admin.route("/campaigns/flagged")
@login_required
def flagged_campaigns():
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    cname = request.args.get("cname", "")
    sname = request.args.get("sname", "")
    campaigns = Campaign.query.filter_by(flagged=True)
    if cname:
        campaigns = campaigns.filter(Campaign.name.contains(cname))
    if sname:
        campaigns = campaigns.filter(Campaign.sponsor.has(Sponsor.name.contains(sname)) | Campaign.sponsor.has(Sponsor.username.contains(sname)))
    
    campaigns = campaigns.all()
    return render_template("admin_flagged_campaigns.html", campaigns=campaigns, cname=cname, sname=sname, Influencer=Influencer)


@admin.route("/campaigns/flagged/add/<int:id>", methods=['POST'])
@login_required
def flag_campaign(id):
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaign = Campaign.query.filter_by(id=id).first()
    campaign.flagged = True
    db.session.commit()

    flash("Campaign has been Flagged !", category="success")
    return redirect(url_for("admin.flagged_campaigns"))


@admin.route("/campaigns/flagged/remove/<int:id>", methods=['POST'])
@login_required
def unflag_campaign(id):
    if current_user.role != "admin":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaign = Campaign.query.filter_by(id=id).first()
    campaign.flagged = False
    db.session.commit()

    flash("Campaign has been UnFlagged !", category="success")
    return redirect(url_for("admin.flagged_campaigns"))


@admin.route("/all_admins", methods=['GET', 'POST'])
@login_required
def all_admins():
    if current_user.role != "admin" and current_user.username != "aaditya01":
        return redirect("/")
    
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already exists !", category="danger")
            return render_template("admin_all_admins.html", name=name, username=username, email=email)
        
        if User.query.filter_by(email=email).first():
            flash("Email ID already exists !", category="danger")
            return render_template("admin_all_admins.html", name=name, username=username, email=email)

        user = User(username=username, email=email, password=generate_password_hash(password), role="admin")
        admin = Admin(username=username, name=name)
        db.session.add(user)
        db.session.add(admin)
        db.session.commit()

        flash("Admin added !", category="success")
        return redirect(url_for("admin.all_admins"))

    admins = Admin.query.filter(Admin.username.isnot("aaditya01"), Admin.user.has(User.flagged==False)).all()
    return render_template("admin_all_admins.html", admins=admins)