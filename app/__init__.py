from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


db = SQLAlchemy()

def create_app():
    # Initializing App
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "a"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"


    # Database Initialisation
    db.init_app(app)
    # Creating Database if not exists
    create_database(app)


    # Defining Paths for authentication and views
    from .auth import auth
    from .views import views
    from .sponsor import sponsor
    from .influencer import influencer
    from .admin import admin
    app.register_blueprint(auth, url_prefix="/auth/")
    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(admin, url_prefix="/admin/")
    app.register_blueprint(sponsor, url_prefix="/sponsor/")
    app.register_blueprint(influencer, url_prefix="/influencer/")


    # Initializing flask_login for handling authentication
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please login to proceed !"
    login_manager.login_message_category = "warning"

    from .models import User
    @login_manager.user_loader
    def load_user(username):
        return User.query.get(username)


    return app


def create_database(app):
    if not os.path.exists(os.path.join(app.instance_path, "database.db")):
        with app.app_context():
            from .models import User, Admin, Sponsor, Influencer, Category, Campaign, Request, Rating, Transaction
            db.create_all()
            
            categories = ["Technology", "Education", "Entertainment", "Fashion", "Skincare", "Finance", "Healthcare", "Media", "Travel", "Sports", "Gaming"]
            for i in categories:
                c = Category(name=i)
                db.session.add(c)

            from werkzeug.security import generate_password_hash
            user = User(username="aaditya01", email="aadityajain0128@gmail.com", role="admin", password=generate_password_hash("aaditya01"))
            admin = Admin(username="admin", name="Aaditya Jain")
            db.session.add(user)
            db.session.add(admin)

            db.session.commit()