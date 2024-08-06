The objective of the Project was to build a platform to connect sponsors and influencers so that sponsors can get their product / service advertised and Influencer can get Monetary Benefit.


## Technologies Used
  1.  Flask: Python Framework for running server, requests handling and defining routes of Web App.    
  2.  Flask Sqlalchemy: Used for defining Database Models, executing queries and saving changes permanently.    
  3.  Flask Login: Used for secure authentication of the User and manages the login session.    
  4.  Werkzeug Security: Used for generating hash for the passwords to store it in the Database.    
  5.  Jinja: Used for render HTML templates dynamically.    
  6.  OS: Used for storing dynamically generated csv files, etc.


## Features
  Users can sign-up as Sponsor or Influencer, and can log in using username and password.   
  The app determines if a User is a Sponsor or an Influencer.   
     
  ### Sponsors   
    1.  Can create Campaigns and view the details of the Campaigns.   
    2.  Can send or receive the requests from influencer for their Campaigns.   
    3.  Can find the Influencers.   
    4.  Can see the stats of their Campaigns.   
    5.  Can rate the Influencer.   
    6.  Can edit their profile.   
     
  ### Influencers   
    1.  Can send or receive the requests from Sponsors for the Campaigns.   
    2.  Can find the Campaigns.   
    3.  Can see the stats.   
    4.  Can edit his/her profile for better reach.   
     
  ### Admins   
    1.  Can see the Global Stats.   
    2.  Can flag the Sponsors / Influencers or any Campaigns.   
    3.  Can Unflag the User and Campaigns.   
    4.  Can delete the Campaigns.   
    5.  Main/Master Admin can add or flag/unflag other Admins also.


## Project Directory 
  The Project contains an app folder, an instance folder and main.py file.
  App folder contains all .py files and html templates and static files. Instance folder contains the database.db file.
     
  You can run the app using main.py file. 
