Access datex-node at NRPA:
1. Get api call access:
-   Check mail from Kåre, get username and password
-   email from: <Datex@vegvesen.no>
2. Get api key:
-   Install python-dotenv via terminal (make sure you are in venv):
-   pip install python-dotenv
-   username/password is found in the email.
3.  Make an ".env" file, and write:
-   brukernavn="angitt brukernavn"
-   passord="angitt passord"

Populate the database with ferries:
python manage.py get_transit_info.py