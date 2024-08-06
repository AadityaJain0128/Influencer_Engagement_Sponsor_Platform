from flask import Flask, Blueprint, redirect, render_template, request, url_for, flash, send_from_directory, send_file, current_app
from flask_login import current_user, login_required
from . import db
from .models import Campaign, Influencer, Category, Request, Sponsor, Transaction, Rating, User
from datetime import datetime
import csv
import os


sponsor = Blueprint("sponsor", __name__)


@sponsor.route("/")
@sponsor.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    active_campaigns = Campaign.query.filter(Campaign.sponsor_id==current_user.sponsor.id, Campaign.completed == False, Campaign.influencer_id.isnot(None)).all()

    campaign_ids = Campaign.query.filter(Campaign.sponsor_id==current_user.sponsor.id, Campaign.influencer_id.is_(None)).with_entities(Campaign.id)
    recieved_requests = Request.query.filter(Request.campaign_id.in_(campaign_ids), Request.sent_by=="influencer", Request.status=="pending").all()

    return render_template("sponsor_dashboard.html", active_campaigns=active_campaigns, recieved_requests=recieved_requests, datetime=datetime, Influencer=Influencer, Campaign=Campaign)


@sponsor.route("/campaigns", methods=['GET', 'POST'])
@login_required
def campaigns():
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description", "")
        start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
        end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d")
        budget = float(request.form.get("budget"))
        visibility = request.form.get("visibility")

        campaign = Campaign(name=name, description=description, start_date=start_date, end_date=end_date, budget=budget, visibility=visibility, sponsor_id=current_user.sponsor.id)
        db.session.add(campaign)
        db.session.commit()
        flash("Campaign has been added !", category="success")
        return redirect(url_for("sponsor.campaigns"))

    campaigns = Campaign.query.filter_by(sponsor_id=current_user.sponsor.id)
    active_campaigns = campaigns.filter(Campaign.completed == False, Campaign.influencer_id.isnot(None)).all()
    pending_campaigns = campaigns.filter(Campaign.completed == False, Campaign.influencer_id.is_(None)).all()
    completed_campaigns = campaigns.filter_by(completed=True).all()

    return render_template("sponsor_campaigns.html", active_campaigns=active_campaigns, pending_campaigns=pending_campaigns, completed_campaigns=completed_campaigns, datetime=datetime, Influencer=Influencer)


@sponsor.route("/campaigns/<int:id>")
@login_required
def campaign_view(id):
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaign = Campaign.query.filter_by(id=id, sponsor_id=current_user.sponsor.id).first()
    if not campaign:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    recieved_requests = Request.query.filter_by(campaign_id=id, sent_by="influencer").all()
    sent_requests = Request.query.filter_by(campaign_id=id, sent_by="sponsor").all()

    return render_template("sponsor_campaign_view.html", campaign=campaign, recieved_requests=recieved_requests, sent_requests=sent_requests, Influencer=Influencer, Campaign=Campaign, Rating=Rating)


@sponsor.route("/campaigns/<int:id>/edit", methods=['POST'])
@login_required
def campaign_edit(id):
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaign = Campaign.query.filter_by(id=id, sponsor_id=current_user.sponsor.id).first()
    if not campaign:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.flagged:
        flash("Campaign has been flagged by Admin !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))
    
    campaign.name = request.form.get("name")
    campaign.description = request.form.get("description", "")
    campaign.start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
    campaign.end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d")
    campaign.budget = float(request.form.get("budget"))
    campaign.visibility = request.form.get("visibility")
    db.session.commit()

    flash("Campaign Edited !", category="success")
    return redirect(url_for("sponsor.campaign_view", id=campaign.id))


@sponsor.route("/campaigns/<int:id>/delete")
@login_required
def campaign_delete(id):
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaign = Campaign.query.filter(Campaign.id==id, Campaign.sponsor_id==current_user.sponsor.id, Campaign.influencer_id.is_(None)).first()
    if not campaign:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))

    for r in campaign.requests:
        db.session.delete(r)
        
    db.session.delete(campaign)
    db.session.commit()

    flash("Campaign Deleted !", category="success")
    return redirect(url_for("sponsor.campaigns"))


@sponsor.route("/request/<int:rid>/accept")
@login_required
def accept_request(rid):
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    req = Request.query.filter_by(id=rid).first()
    if not req:
        flash("Invalid Request !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    campaign = req.campaign
    if campaign.sponsor_id != current_user.sponsor.id:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.flagged:
        flash("Campaign has been flagged by Admin !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))
    
    if campaign.completed:
        flash("Campaign already completed !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))
    
    if campaign.influencer_id:
        flash("Campaign already has an Influencer !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))

    for r in campaign.requests:
        r.status = "rejected"

    req.status = "accepted"
    campaign.budget = req.budget
    campaign.influencer_id = req.influencer_id

    db.session.commit()
    return redirect(url_for("sponsor.campaign_view", id=campaign.id))


@sponsor.route("/request/<int:rid>/reject")
@login_required
def reject_request(rid):
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    req = Request.query.filter_by(id=rid).first()
    if not req:
        flash("Invalid Request !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    campaign = req.campaign
    if campaign.sponsor_id != current_user.sponsor.id:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.flagged:
        flash("Campaign has been flagged by Admin !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))

    req.status = "rejected"
    db.session.commit()
    return redirect(url_for("sponsor.campaign_view", id=campaign.id))


@sponsor.route("/campaigns/<int:id>/payment", methods=['GET', 'POST'])
def payment_gateway(id):
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    campaign = Campaign.query.filter_by(id=id).first()
    if not campaign:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.sponsor_id != current_user.sponsor.id:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.flagged:
        flash("Campaign has been flagged by Admin !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))
    
    if not campaign.influencer_id:
        flash("Campaign does not have an Influencer !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.paid:
        return redirect(url_for("sponsor.campaign_complete", id=campaign.id))

    if campaign.completed:
        flash("Campaign already completed !", category="warning")
        return redirect(url_for("sponsor.campaigns"))
    
    if request.method == "POST":
        campaign.paid = True
        db.session.commit()
        return redirect(url_for("sponsor.campaign_complete", id=id))
    
    return render_template("sponsor_payment_gateway.html")


@sponsor.route("/campaigns/<int:id>/mark_completed")
@login_required
def campaign_complete(id):
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    campaign = Campaign.query.filter_by(id=id).first()
    if not campaign:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.sponsor_id != current_user.sponsor.id:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.flagged:
        flash("Campaign has been flagged by Admin !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))
    
    if not campaign.influencer_id:
        flash("Campaign does not have an Influencer !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))
        
    if not campaign.paid:
        flash("You have to pay to Influencer first !", category="warning")
        return redirect(url_for("sponsor.payment_gateway", id=campaign.id))

    if campaign.completed:
        flash("Campaign already completed !", category="warning")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))

    influencer = Influencer.query.filter_by(id=campaign.influencer_id).first()
    # influencer.earnings += campaign.budget
    transaction = Transaction(influencer_id=influencer.id, campaign_id=campaign.id, amount=campaign.budget, date=datetime.now())
    campaign.completed = True
    db.session.add(transaction)
    db.session.commit()

    flash("Campaign marked as Completed !", category="success")
    return redirect(url_for("sponsor.campaign_view", id=id))


@sponsor.route("campaigns/<int:id>/rating")
def rating(id):
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    campaign = Campaign.query.filter_by(id=id).first()
    if not campaign:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.sponsor_id != current_user.sponsor.id:
        flash("Invalid Campaign !", category="danger")
        return redirect(url_for("sponsor.campaigns"))
    
    if campaign.flagged:
        flash("Campaign has been flagged by Admin !", category="danger")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))
    
    if not campaign.completed:
        flash("Campaign not completed yet !", category="warning")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))
    
    r = Rating.query.filter_by(influencer_id=campaign.influencer_id, campaign_id=campaign.id).first()
    if r:
        flash("You have already rated the Influencer !", category="warning")
        return redirect(url_for("sponsor.campaign_view", id=campaign.id))

    rating = request.args.get("r", type=float)
    rate = Rating(campaign_id=campaign.id, influencer_id=campaign.influencer_id, rating=rating)
    db.session.add(rate)
    db.session.commit()

    flash(f"Rating Submitted !", category="success")
    return redirect(url_for("sponsor.campaign_view", id=id))

    
@sponsor.route("/find", methods=['GET', 'POST'])
@login_required
def find():
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    if request.method == "POST":
        messages = request.form.get("messages", "")
        requirements = request.form.get("requirements", "")
        campaign_id = request.form.get("campaign_id")
        influencer_id = request.form.get("influencer_id")

        req = Request.query.filter_by(campaign_id=campaign_id, influencer_id=influencer_id, sent_by="sponsor").first()
        if req:
            status = req.status
            if status == "pending":
                flash(f"Your have already sent the request and is {status} !", category="warning")
            elif status == "rejected":
                flash(f"Your request has been {status} !", category="danger")
            else:
                flash(f"Your request has already been {status} !", category="success")
            return redirect(url_for("sponsor.campaign_view", id=campaign_id))
        
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        req = Request(messages=messages, requirements=requirements, campaign_id=campaign.id, influencer_id=influencer_id, sent_by="sponsor", budget=campaign.budget)
        db.session.add(req)
        db.session.commit()
        flash("Request Sent !", category="success")
        return redirect(url_for("sponsor.campaign_view", id=campaign_id))


    name = request.args.get("name", "")
    niche = request.args.get("niche", "")

    categories = Category.query.all()
    influencers = Influencer.query.filter(Influencer.user.has(User.flagged==False))
    if name:
        influencers = influencers.filter(Influencer.username.contains(name) | Influencer.name.contains(name))
    if niche:
        influencers = influencers.filter(Influencer.niche.contains(niche))
    influencers = influencers.order_by(Influencer.reach.desc()).all()

    avg_ratings = {}
    for i in influencers:
        ratings = Rating.query.filter_by(influencer_id=i.id).all()
        if ratings:
            avg_ratings[i] = [round(sum([r.rating for r in ratings]) / len(ratings), 1), len(ratings)]

    campaigns = Campaign.query.filter(Campaign.sponsor_id==current_user.sponsor.id, Campaign.completed == False, Campaign.influencer_id.is_(None)).all()

    return render_template("sponsor_find.html", categories=categories, influencers=influencers, name=name, niche=niche, campaigns=campaigns, avg_ratings=avg_ratings)


@sponsor.route("/transactions", methods=['GET', 'POST'])
@login_required
def transactions():
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    campaign_ids = Campaign.query.filter(Campaign.sponsor_id==current_user.sponsor.id).with_entities(Campaign.id)
    transactions = Transaction.query.filter(Transaction.campaign_id.in_(campaign_ids)).all()

    if request.method == "POST":
        with open(os.path.join(current_app.root_path, "static", "transactions_csv", f"{current_user.username}.csv"), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Transaction ID", "Campaign Name", "Influencer Username", "Pay Amount", "Date", "Time"])
            
            for t in transactions:
                writer.writerow([t.id, t.campaign.name, t.influencer.username, "INR " + str(t.amount), t.date.strftime("%d %b, %Y"), t.date.strftime("%H:%M:%S")])
        
        return send_from_directory(os.path.join(current_app.root_path, "static", "transactions_csv"), f"{current_user.username}.csv")

    return render_template("sponsor_transactions.html", transactions=transactions)


@sponsor.route("/stats")
@login_required
def stats():
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))

    campaigns = Campaign.query.filter_by(sponsor_id=current_user.sponsor.id)
    active_campaigns = campaigns.filter(Campaign.completed == False, Campaign.influencer_id.isnot(None)).all()
    pending_campaigns = campaigns.filter(Campaign.completed == False, Campaign.influencer_id.is_(None)).all()
    completed_campaigns = campaigns.filter_by(completed=True).all()
    campaign_labels = ["Active Campaigns", "Pending Campaigns", "Completed Campaigns"]
    campaign_values = [len(active_campaigns), len(pending_campaigns), len(completed_campaigns)]

    campaign_ids = [c.id for c in current_user.sponsor.campaigns.filter_by(paid=True).all()]
    transactions = Transaction.query.filter(Transaction.campaign_id.in_(campaign_ids)).all()
    transaction_labels = [t.campaign.name for t in transactions]
    transaction_values = [t.amount for t in transactions]

    return render_template("sponsor_stats.html", campaign_labels=campaign_labels, campaign_values=campaign_values, transaction_labels=transaction_labels, transaction_values=transaction_values)


@sponsor.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != "sponsor":
        return redirect("/")
    
    if current_user.flagged:
        return redirect(url_for("views.flagged_user"))
    
    if request.method == "POST":
        name = request.form.get("name")
        industry = request.form.get("industry")

        sponsor = Sponsor.query.filter_by(id=current_user.sponsor.id).first()
        sponsor.name = name
        sponsor.industry = industry
        db.session.commit()
        flash("Profile Updated !", category="success")
        return redirect(url_for('sponsor.profile'))

    categories = Category.query.all()
    return render_template("sponsor_profile.html", categories=categories)