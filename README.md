# This app 

Access datex-node at NRPA:
Transport Situation Map Application
This application is a Django web application that fetches transit situation data from the Norwegian Public Roads Administration (Statens vegvesen) via the DATEX II API and displays it on an interactive map. The application allows users to:

View current transit situations (such as road closures, traffic incidents, etc.) on a map.
Filter transit situations by county.
See detailed information about each transit situation, including severity, description, and comments.
Draw custom points, lines, and polygons on the map for analysis or planning purposes.

Python 3.x
Virtual Environment (optional but recommended)
Django 5.1.4
Access credentials for the DATEX II API from the Norwegian Public Roads Administration.
Installation
Clone the repository:

git clone https://github.com/yourusername/your-repo.git
cd your-repo
Create a virtual environment (optional but recommended):

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install the required packages:

pip install -r requirements.txt
# Configuration
1. Obtain API Access Credentials
Request access: Email <Datex@vegvesen.no> to request access to the DATEX II API.
Receive credentials: You should receive an email from Kåre with your username and password.
2. Set Up Environment Variables
Install python-dotenv (if not already installed):

pip install python-dotenv
Create a .env file in the root directory of your project:

touch .env
Add your API credentials to the .env file:

USERNAME_DATEX="your_username"
PASSWORD_DATEX="your_password"
Replace "your_username" and "your_password" with the credentials provided in the email.

# Running the Application
1. Apply Migrations
Navigate to your Django project directory and run:

- python manage.py makemigrations map
- python manage.py migrate
2. Fetch Transit Data
Populate the database with transit situation data by running:
- python manage.py transit_info
This command executes the management command that fetches data from the DATEX II API and stores it in your database.

3. Run the Development Server
Start the Django development server:
- python manage.py runserver
4. Access the Application
- Open your web browser and navigate to:

http://127.0.0.1:8000/map/
# Application Structure
Management Command: transit_info

Located in map/management/commands/transit_info.py
Fetches transit situation data from the VTS API.
Processes the XML response and stores the data in the database.
Uses the If-Modified-Since header to optimize network usage.
Models:

TransitInformation: Stores information about each transit situation.
ApiMetadata: Stores metadata such as the last modified date for the API data.
Views:

map: Renders the main map page.

map/: The main page displaying the map.
api/locations/: Endpoint providing location data in GeoJSON format.
Usage
Interactive Map Features
Map Display: Shows a map of Norway with various layers such as roads, forests, water bodies, and more.

Transit Situations:

Transit situations are displayed on the map as points or lines, depending on the data.
Severity levels are indicated by different colors.
Clicking on a point or line displays a popup with detailed information.
County Filter:

A dropdown menu allows users to select a county.
The map and transit situation list update to show data relevant to the selected county.
Drawing Tools:

Users can draw points, lines, and polygons on the map.
Drawn features can be used for planning or analysis.
Coordinates of drawn features are displayed.
Transit List Sidebar:

Displays a list of transit situations.
Users can toggle the visibility of individual transit situations.
Map Controls
Draw Point: Click to draw a point on the map.
Draw Line: Click to draw a line.
Draw Polygon: Click to draw a polygon.
Clear: Removes all drawn features from the map.
Enter Key: Press to exit drawing mode and return to the default map interaction.
Notes
Administration. The application displays data as is, and accuracy is subject to the source.
Security: Keep your API credentials secure. Do not share them publicly or commit them to version control.
# Requirements:

asgiref==3.8.1
Django==5.1.4
django-cors-headers==4.6.0
djangorestframework==3.15.2
sqlparse==0.5.3
typing_extensions==4.12.2
requests==2.31.0
python-dateutil==2.8.2
pyproj==3.6.0

# Credits

Data Source: Norwegian Public Roads Administration (Statens vegvesen) via the DATEX II API.
Map Tiles: Custom vector tiles provided by the specified tile server in the application code.
Developers: Lga239, agu078