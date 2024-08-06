from flask_login import UserMixin
from . import db
from sqlalchemy.ext.mutable import MutableDict


class User(db.Model, UserMixin):
    username = db.Column(db.String(30), primary_key=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    flagged = db.Column(db.Boolean, default=False)

    def get_id(self):
        return self.username


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), db.ForeignKey("user.username"), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    user = db.relationship("User", backref=db.backref("admin", uselist=False))   # Establish One-to-One Relationship with User Table


class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), db.ForeignKey("user.username"), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    industry = db.Column(db.String(50), db.ForeignKey("category.name"), nullable=False)
    user = db.relationship("User", backref=db.backref("sponsor", uselist=False))
    campaigns = db.relationship("Campaign", backref=db.backref("sponsor"), lazy="dynamic")


class Influencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), db.ForeignKey("user.username"), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    niche = db.Column(db.String(50), db.ForeignKey("category.name"), nullable=False)
    profile_picture = db.Column(db.Text, default="profile_pictures/default_profile_picture.png")
    socials = db.Column(MutableDict.as_mutable(db.JSON), default=dict)
    reach = db.Column(db.Integer)
    user = db.relationship("User", backref=db.backref("influencer", uselist=False))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reach = 0

    def calculate_reach(self):
        self.reach = 0
        for social in self.socials:
            self.reach += self.socials[social]


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(150), default="")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(10), default="public")
    sponsor_id = db.Column(db.Integer, db.ForeignKey("sponsor.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    paid = db.Column(db.Boolean, default=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey("influencer.id"), default=None)
    requests = db.relationship("Request", backref=db.backref("campaign"), lazy="dynamic")
    flagged = db.Column(db.Boolean, default=False)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey("influencer.id"), nullable=False)
    sent_by = db.Column(db.String(15), nullable=False)
    messages = db.Column(db.String(150))
    requirements = db.Column(db.String(150))
    budget = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), default="pending")


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey("influencer.id"), nullable=False)
    rating = db.Column(db.Float, nullable=False)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey("influencer.id"), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    campaign = db.relationship("Campaign", backref=db.backref("transaction", uselist=False))
    influencer = db.relationship("Influencer", backref=db.backref("transactions", lazy="dynamic"))