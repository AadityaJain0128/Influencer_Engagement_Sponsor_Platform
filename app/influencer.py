from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required
from . import db
from .models import Campaign, Sponsor, Request, Influencer, Category, Transaction, Rating
from datetime import datetime
import os


influencer = Blueprint("influencer", __name__)


@influencer.route("/")
@influencer.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "influencer":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    active_campaigns = Campaign.query.filter_by(influencer_id=current_user.influencer.id, completed=False).all()
    recieved_requests = Request.query.filter_by(influencer_id=current_user.influencer.id, sent_by="sponsor", status="pending").all()
    
    avg_rating = []
    ratings = Rating.query.filter_by(influencer_id=current_user.influencer.id).all()
    if ratings:
        avg_rating = [round(sum([r.rating for r in ratings]) / len(ratings), 1), len(ratings)]

    month = datetime.now().strftime("%Y-%m")
    month_earnings = sum([t.amount for t in current_user.influencer.transactions.filter(Transaction.date.contains(month)).all()])
    total_earnings = sum([t.amount for t in current_user.influencer.transactions.all()])

    return render_template("influencer_dashboard.html", active_campaigns=active_campaigns, datetime=datetime, Sponsor=Sponsor, recieved_requests=recieved_requests, Campaign=Campaign, Influencer=Influencer, avg_rating=avg_rating, total_earnings=total_earnings, month_earnings=month_earnings)


@influencer.route("/requests")
@login_required
def requests():
    if current_user.role != "influencer":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    recieved_requests = Request.query.filter_by(influencer_id=current_user.influencer.id, sent_by="sponsor").all()
    sent_requests = Request.query.filter_by(influencer_id=current_user.influencer.id, sent_by="influencer").all()
    return render_template("influencer_requests.html", recieved_requests=recieved_requests, sent_requests=sent_requests)


@influencer.route("/find", methods=['GET', 'POST'])
@login_required
def find():
    if current_user.role != "influencer":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    if request.method == "POST":
        messages = request.form.get("messages", "")
        requirements = request.form.get("requirements", "")
        campaign_id = request.form.get("campaign_id")
        influencer_id = request.form.get("influencer_id")
        req_budget = request.form.get("req_budget")

        req = Request.query.filter_by(campaign_id=campaign_id, influencer_id=influencer_id, sent_by="influencer").first()
        if req:
            status = req.status
            if status == "pending":
                flash(f"Your have already sent the request and is {status} !", category="warning")
            elif status == "rejected":
                flash(f"Your request has been {status} !", category="danger")
            else:
                flash(f"Your request has already been {status} !", category="success")
            return redirect(url_for("influencer.requests", id=campaign_id))
        
        req = Request(messages=messages, requirements=requirements, campaign_id=campaign_id, influencer_id=influencer_id, sent_by="influencer", budget=req_budget)
        db.session.add(req)
        db.session.commit()
        flash("Request Sent !", category="success")
        return redirect(url_for("influencer.requests"))


    cname = request.args.get("cname", "")
    sname = request.args.get("sname", "")

    campaigns = Campaign.query.filter(Campaign.flagged==False, Campaign.visibility=="public", Campaign.completed==False, Campaign.influencer_id.is_(None))
    if cname:
        campaigns = campaigns.filter(Campaign.name.contains(cname))

    if sname:
        sponsors = Sponsor.query.filter(Sponsor.name.contains(sname)).all()
        sponsor_ids = [sponsor.id for sponsor in sponsors]

        campaigns = campaigns.filter(Campaign.sponsor_id.in_(sponsor_ids))

    campaigns = campaigns.all()
    return render_template("influencer_find.html", campaigns=campaigns, sname=sname, cname=cname)


@influencer.route("/request/<int:rid>/accept")
@login_required
def accept_request(rid):
    if current_user.role != "influencer":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    req = Request.query.filter_by(id=rid).first()
    if not req:
        flash("Invalid Request !", category="danger")
        return redirect(url_for("influencer.requests"))
    
    if req.influencer_id != current_user.influencer.id:
        flash("Invalid Request !", category="danger")
        return redirect(url_for("influencer.requests", id=campaign.id))

    campaign = req.campaign
    if campaign.flagged:
        flash("Campaign has been flagged by Admin !", category="danger")
        return redirect(url_for("influencer.requests", id=campaign.id))
    
    if campaign.completed:
        flash("Campaign already completed !", category="danger")
        return redirect(url_for("influencer.requests"))
    
    if campaign.influencer_id:
        flash("Campaign already has an Influencer !", category="danger")
        return redirect(url_for("influencer.requests"))

    for r in campaign.requests:
        r.status = "rejected"

    req.status = "accepted"
    campaign.budget = req.budget
    campaign.influencer_id = req.influencer_id
    db.session.commit()

    flash("Request Accepted !", category="success")
    return redirect(url_for("influencer.requests"))


@influencer.route("/request/<int:rid>/reject")
@login_required
def reject_request(rid):
    if current_user.role != "influencer":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    req = Request.query.filter_by(id=rid).first()
    if not req:
        flash("Invalid Request !", category="danger")
        return redirect(url_for("influencer.requests"))
    
    if req.influencer_id != current_user.influencer.id:
        flash("Invalid Request !", category="danger")
        return redirect(url_for("influencer.requests"))

    req.status = "rejected"
    db.session.commit()

    flash("Request Rejected !", category="success")
    return redirect(url_for("influencer.requests"))


@influencer.route("/completed_campaigns")
@login_required
def completed_campaigns():
    if current_user.role != "influencer":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    completed_campaigns = Campaign.query.filter_by(influencer_id=current_user.influencer.id, completed=True).all()
    return render_template("influencer_completed_campaigns.html", completed_campaigns=completed_campaigns, Transaction=Transaction, Rating=Rating)


@influencer.route("/stats")
@login_required
def stats():
    if current_user.role != "influencer":
        return redirect("/")

    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaigns = Campaign.query.filter_by(influencer_id=current_user.influencer.id)
    active_campaigns = campaigns.filter(Campaign.completed == False).all()
    completed_campaigns = campaigns.filter_by(completed=True).all()
    campaign_labels = ["Active Campaigns", "Completed Campaigns"]
    campaign_values = [len(active_campaigns), len(completed_campaigns)]

    transactions = Transaction.query.filter_by(influencer_id=current_user.influencer.id).all()
    transaction_labels = [t.campaign.name for t in transactions]
    transaction_values = [t.amount for t in transactions]

    return render_template("influencer_stats.html", campaign_labels=campaign_labels, campaign_values=campaign_values, transaction_labels=transaction_labels, transaction_values=transaction_values)


@influencer.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != "influencer":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    if request.method == "POST":
        current_user.influencer.name = request.form.get("name")
        current_user.influencer.niche = request.form.get("niche")

        for social in ["facebook", "instagram", "linkedin", "twitter", "youtube"]:
            current_user.influencer.socials[social] = request.form.get(social, default=0, type=int)
        current_user.influencer.calculate_reach()

        db.session.commit()
        flash("Profile Updated !", category="success")
        return redirect(url_for("influencer.profile"))
    
    avg_rating = []
    ratings = Rating.query.filter_by(influencer_id=current_user.influencer.id).all()
    if ratings:
        avg_rating = [round(sum([r.rating for r in ratings]) / len(ratings), 1), len(ratings)]
    earnings = sum([t.amount for t in current_user.influencer.transactions.all()])

    categories = Category.query.all()
    return render_template("influencer_profile.html", categories=categories, avg_rating=avg_rating, earnings=earnings)


@influencer.route("/profile/update_profile_picture", methods=['POST'])
@login_required
def picture_update():
    if current_user.influencer.profile_picture != "profile_pictures/default_profile_picture.png":
        os.remove(rf"app/static/{current_user.influencer.profile_picture}")
        current_user.influencer.profile_picture = "profile_pictures/default_profile_picture.png"
        db.session.commit()

    profile_pic = request.files.get("profile_pic")
    ext = profile_pic.filename.split(".")[-1]

    if ext.lower() not in ["png", "jpg", "jpeg", "webp", "svg", "gif"]:
        flash("File format not supported !", category="danger")
        return redirect(url_for("influencer.profile"))
    
    path = rf"profile_pictures/{current_user.username}.{ext}"
    profile_pic.save(os.path.join('app/static', path))
    current_user.influencer.profile_picture = path
    db.session.commit()

    flash("Profile Picture Updated !", category="success")
    return redirect(url_for("influencer.profile"))


@influencer.route("/profile/remove_profile_picture")
@login_required
def picture_remove():
    if current_user.role != "influencer":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    if current_user.influencer.profile_picture == "profile_pictures/default_profile_picture.png":
        return redirect(url_for("views.profile"))
    
    path = current_user.influencer.profile_picture
    current_user.influencer.profile_picture = "profile_pictures/default_profile_picture.png"
    os.remove(rf"app/static/{path}")
    db.session.commit()

    flash("Profile Picture Removed !", category="success")
    return redirect(url_for("influencer.profile"))