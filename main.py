from flask_sqlalchemy import SQLAlchemy
import io
import pandas as pd
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker as db_sessionmaker
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy import Numeric
from flask import flash, get_flashed_messages
from flask import Flask, render_template, request, redirect, Response, session
import pdfkit
import win32print
import wmi
import subprocess
from collections import defaultdict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, Float
from sqlalchemy.orm import sessionmaker
import numpy as np
from flask import Flask, redirect, request, session, url_for
import requests
import dropbox
from flask import Flask, render_template, request, jsonify, render_template_string
from weasyprint import HTML
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'C:/Users/james/OneDrive/Documents/Black Line App 2.0/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///riders.db'  # Replace with your database connection URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])  # Move the engine creation here
db = SQLAlchemy(app)
db_session = db_sessionmaker(bind=engine)  # Replace `session` with your chosen name
app.secret_key = 'jb'

Session = sessionmaker(bind=engine)

Base = declarative_base()

app = Flask(__name__)

import os
import pdfkit
import tempfile
import requests
import dropbox
from flask import Flask, request, jsonify, render_template, redirect
from datetime import datetime
import traceback
from functools import wraps

app = Flask(__name__)

from dropbox_auth import new_access_token  # Import the new_access_token

# Initialize Dropbox access token variable
DROPBOX_ACCESS_TOKEN = new_access_token  # Use new_access_token from dropbox_auth.py

# Dropbox OAuth 2.0 Configuration
DROPBOX_APP_KEY = 'sfstnnzzzux4ycr'
DROPBOX_APP_SECRET = '9t2muuwf17vefea'
DROPBOX_REDIRECT_URI = 'http://127.0.0.1:5000/qualifying_results'  # Set your redirect URI here

def cross_origin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST'
        return response
    return decorated_function

@app.route('/callback')
def dropbox_callback():
    print("Callback route triggered")  # Debugging statement
    code = request.args.get('code')
    print(f"Received code: {code}")  # Debugging statement
    
    data = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': DROPBOX_APP_KEY,
        'client_secret': DROPBOX_APP_SECRET,
        'redirect_uri': DROPBOX_REDIRECT_URI
    }

    response = requests.post('https://api.dropbox.com/oauth2/token', data=data)
    data = response.json()

    print("Dropbox OAuth response:", data)  # Debugging statement

    if 'access_token' in data:
        access_token = data['access_token']

        print("Access token:", access_token)  # Debug

        # Store the access token (consider using a more secure method)
        with open('dropbox_access_token.txt', 'w') as token_file:
            token_file.write(access_token)
        
        print("Access token saved to dropbox_access_token.txt")  # Debug

        # Step 2: Upload File to Dropbox
        upload_result = upload_to_dropbox(access_token, 'qualifying_results.pdf')
        
        if upload_result:
            print("Uploaded to Dropbox:", 'qualifying_results.pdf')
            return jsonify({"success": True, "message": "File uploaded successfully"}), 200
        else:
            print("Error uploading to Dropbox")
            return jsonify({"success": False, "message": "Error uploading to Dropbox"}), 500

    else:
        print("Error retrieving access token from Dropbox")
        return jsonify({"success": False, "message": "Error retrieving access token from Dropbox"}), 500

def generate_pdf(data, output_path):
    # Create a PDF document
    pdf = SimpleDocTemplate(
        output_path,
        pagesize=letter
    )
    
    # Set the table style
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    # Create a table from the data
    table = Table(data)
    table.setStyle(table_style)
    
    # Add the table to the PDF document
    elements = []
    elements.append(table)
    
    # Build the PDF
    pdf.build(elements)


def upload_to_dropbox(access_token, pdf_file):
    try:
        if access_token is None:
            print("Not authenticated with Dropbox!")
            return False

        dbx = dropbox.Dropbox(access_token)
        
        # Check if the file already exists in Dropbox
        existing_files = dbx.files_list_folder('').entries
        for entry in existing_files:
            if entry.name == pdf_file:
                # Rename the existing file with a timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{pdf_file.split('.')[0]}_{timestamp}.{pdf_file.split('.')[1]}"
                dbx.files_move(f'/{pdf_file}', f'/{new_name}')

        # Upload the new PDF file
        with open(pdf_file, 'rb') as f:
            dbx.files_upload(f.read(), f'/{pdf_file}', mode=dropbox.files.WriteMode.overwrite)

        print(f"Uploaded to Dropbox: {pdf_file}")
        return True

    except Exception as e:
        print("Error uploading to Dropbox:", e)
        return False



@app.route('/generate_and_upload', methods=['POST'])
def generate_and_upload():
    try:
        data = request.json
        print("Received data:", data)

        if 'male_riders' in data and 'female_riders' in data:
            
            # Render the template with the data
            html_content = render_template('qualifying_results.html', data=data)
        
            # Log the rendered HTML
            print("Rendered HTML:", html_content)

            # Generate PDF from HTML content
            output_path = 'qualifying_results.pdf'
            generate_result = generate_pdf(html_content, output_path)

            if generate_result:
                # Upload to Dropbox
                upload_result = upload_to_dropbox(DROPBOX_ACCESS_TOKEN, 'qualifying_results.pdf')
                
                if upload_result:
                    print("Uploaded to Dropbox:", 'qualifying_results.pdf')
                    return jsonify({"success": True, "message": "File uploaded successfully"}), 200
                else:
                    print("Error uploading to Dropbox")
                    return jsonify({"success": False, "message": "Error uploading to Dropbox"}), 500

            else:
                print("Error generating PDF")
                return jsonify({"success": False, "message": "Error generating PDF"}), 500

        else:
            response_data = {
                "success": False,
                "message": "Invalid data format"
            }
            
            return jsonify(response_data), 400

    except KeyError as ke:
        print("Missing key in data:", ke)
        response_data = {
            "success": False,
            "message": "Missing key in data"
        }
        
        return jsonify(response_data), 400

    except Exception as e:
        traceback.print_exc()
        print("Error:", e)
        
        response_data = {
            "success": False,
            "message": str(e)
        }
        
        return jsonify(response_data), 500


class RidersMale(Base):
    __tablename__ = 'riders_male'

    rider_number = db.Column(db.Integer, primary_key=True)
    rider_name = db.Column(db.String(50))
    rider_club = db.Column(db.String(50))
    signed_on = db.Column(db.String(50), default='No')
    qualifying_time = db.Column(db.Numeric(precision=3, asdecimal=False), nullable=True)
    seeding = db.Column(db.Integer)
    sprint_category = db.Column(db.String(50))
    round_1_pairing = db.Column(db.Integer, nullable=True)
    round_1_seeding = db.Column(db.Integer, nullable=True)
    quarter_final_seeding = db.Column(db.Integer, nullable=True)
    semi_final_seeding = db.Column(db.Integer, nullable=True)
    final_seeding = db.Column(db.Integer, nullable=True)
    final_result = db.Column(db.Integer, nullable=True)

    def __str__(self):
        return self.rider_name
    
    def __init__(self, rider_number, rider_name, rider_club):
        self.rider_number = rider_number
        self.rider_name = rider_name
        self.rider_club = rider_club

class RidersFemale(Base):
    __tablename__ = 'riders_female'

    rider_number = db.Column(db.Integer, primary_key=True)
    rider_name = db.Column(db.String(50))
    rider_club = db.Column(db.String(50))
    signed_on = db.Column(db.String(50), default='No')
    qualifying_time = db.Column(db.Numeric(precision=3, asdecimal=False), nullable=True)
    seeding = db.Column(db.Integer)
    sprint_category = db.Column(db.String(50))
    round_1_pairing = db.Column(db.Integer, nullable=True)
    round_1_seeding = db.Column(db.Integer, nullable=True)
    quarter_final_seeding = db.Column(db.Integer, nullable=True)
    semi_final_seeding = db.Column(db.Integer, nullable=True)
    final_seeding = db.Column(db.Integer, nullable=True)
    final_result = db.Column(db.Integer, nullable=True)

    def __init__(self, rider_number, rider_name, rider_club):
        self.rider_number = rider_number
        self.rider_name = rider_name
        self.rider_club = rider_club

class QualifyingResult(Base):
    __tablename__ = 'qualifying_results'

    id = db.Column(db.Integer, primary_key=True)
    qualifying_position = db.Column(db.Integer)
    rider_name = db.Column(db.String(50))
    rider_team = db.Column(db.String(50))
    qualifying_time = db.Column(db.Float, nullable=True)

    def __init__(self, qualifying_position, rider_name, rider_team, qualifying_time):
        self.qualifying_position = qualifying_position
        self.rider_name = rider_name
        self.rider_team = rider_team
        self.qualifying_time = qualifying_time

class FinalResults(Base):
    __tablename__ = 'final_results'

    id = db.Column(db.Integer, primary_key=True)
    final_result = db.Column(db.Integer)
    rider_name = db.Column(db.String(50))
    rider_team = db.Column(db.String(50))
    sprint_category = db.Column(db.String(50))


    def __init__(self, final_result, rider_name, rider_team, qualifying_time):
        self.final_result = final_result
        self.rider_name = rider_name
        self.rider_team = rider_team
        self.rider_final_result = final_result

Base.metadata.bind = engine

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


import pandas as pd
from flask import request, render_template, redirect, url_for, flash
import os

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.secret_key = 'jb'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from flask import session

from werkzeug.utils import secure_filename

@app.route('/upload_logo', methods=['POST'])
def upload_logo():
    if 'logo' in request.files:
        logo = request.files['logo']
        if logo.filename != '':
            filename = secure_filename('logo.png')
            logo.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))
            session['logo_filename'] = filename
    return redirect(url_for('home'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_printer = request.form.get('printer')
        session['selected_printer'] = selected_printer
        return render_template('home.html', selected_printer=selected_printer)
    else:
        logo_filename = request.args.get('logo_filename')
        selected_printer = session.get('selected_printer')
        printers = get_printer_names()
        return render_template('home.html', logo_filename=logo_filename, selected_printer=selected_printer, printers=printers)

    
def get_printer_names():
    printer_names = []
    for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
        printer_names.append(printer[2])
    return printer_names

@app.route('/set_printer', methods=['POST'])
def set_printer():
    selected_printer = request.form.get('printer')
    session['selected_printer'] = selected_printer
    return redirect(url_for('index'))

from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_logo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def get_printer_list():
    printer_list = []
    c = wmi.WMI()
    printers = c.Win32_Printer()
    for printer in printers:
        printer_name = printer.Name
        printer_list.append(printer_name)
    return printer_list

@app.route('/submit', methods=['POST'])
def submit():
    with session_scope() as session:
        #stat code here
        if 'male_csv' in request.files:
            male_csv = request.files['male_csv']
            if male_csv.filename != '':
                male_df = pd.read_csv(io.BytesIO(male_csv.read()), encoding='utf8')

                # Remove leading spaces from all cells in the DataFrame
                male_df = male_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

                # Existing column checks
                if 'qualifying_time' in male_df.columns:
                    male_df['qualifying_time'] = male_df['qualifying_time'].astype(np.int64, errors='ignore')
                else:
                    male_df['qualifying_time'] = 0  # Default value
                
                if 'seeding' not in male_df.columns:
                    male_df['seeding'] = 0  # Default value
                
                if 'sprint_category' not in male_df.columns:
                    male_df['sprint_category'] = 'Unknown'  # Default value
                
                if 'signed_on' not in male_df.columns:
                    male_df['signed_on'] = 'Yes'  # Default value

                # New column checks
                if 'rider_club' not in male_df.columns:
                    male_df['rider_club'] = 'Unknown'  # Default value

                # For columns that might be missing and should be set to null
                for col in ['rider_number', 'rider_name', 'round_1_pairing', 'round_1_seeding', 
                            'quarter_final_seeding', 'semi_final_seeding', 'final_seeding', 'final_result']:
                    if col not in male_df.columns:
                        male_df[col] = np.nan

                # Type casting columns to ensure correct data types
                for col in ['rider_number', 'qualifying_time', 'seeding', 'round_1_pairing', 'round_1_seeding', 
                            'quarter_final_seeding', 'semi_final_seeding', 'final_seeding', 'final_result']:
                    male_df[col] = male_df[col].astype(np.int64, errors='ignore')

                male_df.to_sql('riders_male', engine, if_exists='replace', index=False)


        if 'female_csv' in request.files:
            female_csv = request.files['female_csv']
            if female_csv.filename != '':
                female_df = pd.read_csv(io.BytesIO(female_csv.read()), encoding='utf8')

                # Remove leading spaces from all cells in the DataFrame
                female_df = female_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

                # Existing column checks
                if 'qualifying_time' in female_df.columns:
                    female_df['qualifying_time'] = female_df['qualifying_time'].astype(np.int64, errors='ignore')
                else:
                    female_df['qualifying_time'] = 0  # Default value
                
                if 'seeding' not in female_df.columns:
                    female_df['seeding'] = 0  # Default value
                
                if 'sprint_category' not in female_df.columns:
                    female_df['sprint_category'] = 'Unknown'  # Default value
                
                if 'signed_on' not in female_df.columns:
                    female_df['signed_on'] = 'Yes'  # Default value

                # New column checks
                if 'rider_club' not in female_df.columns:
                    female_df['rider_club'] = 'Unknown'  # Default value

                # For columns that might be missing and should be set to null
                for col in ['rider_number', 'rider_name', 'round_1_pairing', 'round_1_seeding', 
                            'quarter_final_seeding', 'semi_final_seeding', 'final_seeding', 'final_result']:
                    if col not in female_df.columns:
                        female_df[col] = np.nan

                # Type casting columns to ensure correct data types
                for col in ['rider_number', 'qualifying_time', 'seeding', 'round_1_pairing', 'round_1_seeding', 
                            'quarter_final_seeding', 'semi_final_seeding', 'final_seeding', 'final_result']:
                    female_df[col] = female_df[col].astype(np.int64, errors='ignore')

                female_df.to_sql('riders_female', engine, if_exists='replace', index=False)

    return redirect('/signon_male')


@app.route('/signon_male', methods=['GET', 'POST'])
def signon_male():
    if request.method == 'POST':
        form_data = request.form.to_dict()

        with session_scope() as session:
            riders_male = session.query(RidersMale).all()
            signon_male = {rider.rider_number: 'No' for rider in riders_male}

            for k, v in form_data.items():
                try:
                    rider_number = int(k.split('[')[1].split(']')[0])
                except (ValueError, IndexError):
                    continue  # Skip this key if it can't be parsed into an integer

                if 'male_riders_signon' in k:
                    signon_male[rider_number] = v

            for rider_number, signed_on in signon_male.items():
                rider = session.query(RidersMale).filter_by(rider_number=rider_number).first()
                if rider:
                    rider.signed_on = signed_on

            session.commit()

        return redirect('/signon_female')
    else:
        with session_scope() as session:
            male_riders = pd.read_sql('SELECT rider_number AS "Rider Number", rider_name AS "Rider Name", rider_club AS "Rider Club", "" AS "Signed_On" FROM riders_male ORDER BY rider_number DESC', engine)
        return render_template('male_signon.html', male_riders=male_riders.to_dict('records'))


@app.route('/signon_female', methods=['GET', 'POST'])
def signon_female():
    if request.method == 'POST':
        form_data = request.form.to_dict()

        with session_scope() as session:
            riders_female = session.query(RidersFemale).all()
            signon_female = {rider.rider_number: 'No' for rider in riders_female}

        for k, v in form_data.items():
            try:
                rider_number = int(k.split('[')[1].split(']')[0])
            except (ValueError, IndexError):
                continue  # Skip this key if it can't be parsed into an integer

            if 'female_riders_signon' in k:
                signon_female[rider_number] = v

        for rider_number, signed_on in signon_female.items():
            rider = session.query(RidersFemale).filter_by(rider_number=rider_number).first()
            if rider:
                rider.signed_on = signed_on

        session.commit()

        return redirect('/qualifying')
    else:
        female_riders = pd.read_sql('SELECT rider_number AS "Rider Number", rider_name AS "Rider Name", rider_club AS "Rider Club", "" AS "Signed_On" FROM riders_female', engine)
        female_riders.sort_values(by='Rider Number', ascending=False, inplace=True)
        return render_template('female_signon.html', female_riders=female_riders.to_dict('records'))

def assign_sprint_categories(num_riders):
    sprint_categories = {
        'A': 0,
        'B': 0,
        'C': 0,
        'D': 0,
        'E': 0
    }

    if num_riders <= 17:
        sprint_categories['A'] = num_riders
    elif num_riders <= 29:
        sprint_categories['A'] = 12
        sprint_categories['B'] = num_riders - 12
    elif num_riders <= 41:
        sprint_categories['A'] = 12
        sprint_categories['B'] = 12
        sprint_categories['C'] = num_riders - 24
    elif num_riders <= 53:
        sprint_categories['A'] = 12
        sprint_categories['B'] = 12
        sprint_categories['C'] = 12
        sprint_categories['D'] = num_riders - 36
    else:  # 54-60 riders
        sprint_categories['A'] = 12
        sprint_categories['B'] = 12
        sprint_categories['C'] = 12
        sprint_categories['D'] = 12
        sprint_categories['E'] = num_riders - 48

    return sprint_categories

from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from flask import render_template
from flask import Flask, render_template
from jinja2 import Environment

@app.template_filter('format_float')
def format_float(value):
    return "{:.3f}".format(value)

from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker

@app.route('/qualifying')
def qualifying():
    with db_session() as db:  # Replace `session` with your chosen name

        riders_male_signedon = db.query(RidersMale).filter(RidersMale.signed_on == "Yes").order_by(desc(RidersMale.rider_number)).all()
        riders_female_signedon = db.query(RidersFemale).filter(RidersFemale.signed_on == "Yes").order_by(desc(RidersFemale.rider_number)).all()

    return render_template('qualifying.html', male_riders_signedon=riders_male_signedon, female_riders_signedon=riders_female_signedon)

from sqlalchemy import text
from flask import request

@app.route('/update_qualifying_times_males', methods=['POST'])
def update_qualifying_times_males():
    with engine.connect() as connection:
        for key, time in request.form.items():
            if key.startswith('qualifying_time_males'):
                rider_number = key.split('[')[1].split(']')[0]
                if time:  # Check if time is not empty
                    connection.execute(
                        text("UPDATE riders_male SET qualifying_time = :time WHERE rider_number = :rider_number AND signed_on = 'Yes'"),
                        {"time": float(time), "rider_number": rider_number}
                    )
                else:
                    connection.execute(
                        text("UPDATE riders_male SET qualifying_time = NULL, seeding = NULL, sprint_category = NULL WHERE rider_number = :rider_number AND signed_on = 'Yes'"),
                        {"rider_number": rider_number}
                    )

        # Update the seedings based on qualifying times for signed-on male riders
        connection.execute(
            text("""
            UPDATE riders_male
            SET seeding = (
                SELECT COUNT(*) + 1
                FROM riders_male AS r
                WHERE r.qualifying_time < riders_male.qualifying_time AND r.signed_on = 'Yes'
            )
            WHERE signed_on = 'Yes' AND qualifying_time IS NOT NULL
            """
            )
        )

        # Count the number of riders who have signed on and have a qualifying time
        result = connection.execute(text("SELECT COUNT(*) FROM riders_male WHERE signed_on = 'Yes' AND qualifying_time IS NOT NULL"))
        num_riders = result.scalar()  # get the first column of the first result row

        # Initialize sprint_category with a default value outside of the if statement
        sprint_category = ""

        if num_riders > 0:
            # Call the function to get the sprint category distribution
            distribution = assign_sprint_categories(num_riders)

            # Now assign each rider to a category based on their seeding position
            seeding = 0
            for category, num_riders in distribution.items():
                connection.execute(
                    text("""
                    UPDATE riders_male
                    SET sprint_category = :category
                    WHERE seeding > :start AND seeding <= :end AND signed_on = 'Yes' AND qualifying_time IS NOT NULL
                    """),
                    {"category": category, "start": seeding, "end": seeding + num_riders}
                )
                seeding += num_riders  # update the seeding range for the next category

        # Commit the changes
        connection.commit()

    return "Qualifying times and round 1 heats for male riders updated successfully"

from sqlalchemy.orm import sessionmaker

def gather_rider_summary(sprint_category):
    summary = []

    # Determine the appropriate model based on the sprint category
    if sprint_category == "male":
        riders_model = RidersMale
    elif sprint_category == "female":
        riders_model = RidersFemale
    else:
        # Handle the case where 'sprint_category' is not provided or invalid
        return summary

    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Query riders based on the selected model
        riders = session.query(riders_model).all()

        for rider in riders:
            summary.append({
                "Rider Number": rider.rider_number,
                "Rider Name": rider.rider_name,
                "Qualifying Time": rider.qualifying_time,
                "Seeding": rider.seeding,
                "Round 1 Heat": rider.round_1_pairing,
            })

    finally:
        session.close()  # Close the session when done

    return summary

@app.route('/update_qualifying_times_females', methods=['POST'])
def update_qualifying_times_females():
    with engine.connect() as connection:
        for key, time in request.form.items():
            if key.startswith('qualifying_time_females'):
                rider_number = key.split('[')[1].split(']')[0]
                if time:  # Check if time is not empty
                    connection.execute(
                        text("UPDATE riders_female SET qualifying_time = :time WHERE rider_number = :rider_number AND signed_on = 'Yes'"),
                        {"time": float(time), "rider_number": rider_number}
                    )
                else:
                    connection.execute(
                        text("UPDATE riders_female SET qualifying_time = NULL, seeding = NULL, sprint_category = NULL WHERE rider_number = :rider_number AND signed_on = 'Yes'"),
                        {"rider_number": rider_number}
                    )

        # Update the seedings based on qualifying times for signed-on female riders
        connection.execute(
            text("""
            UPDATE riders_female
            SET seeding = (
                SELECT COUNT(*) + 1
                FROM riders_female AS r
                WHERE r.qualifying_time < riders_female.qualifying_time AND r.signed_on = 'Yes'
            )
            WHERE signed_on = 'Yes' AND qualifying_time IS NOT NULL
            """
            )
        )

        # Count the number of riders who have signed on and have a qualifying time
        result = connection.execute(text("SELECT COUNT(*) FROM riders_female WHERE signed_on = 'Yes' AND qualifying_time IS NOT NULL"))
        num_riders = result.scalar()  # get the first column of the first result row

        # Call the function to get the sprint category distribution
        distribution = assign_sprint_categories(num_riders)

        # Now assign each rider to a category based on their seeding position
        seeding = 0
        for category, num_riders in distribution.items():
            connection.execute(
                text("""
                UPDATE riders_female
                SET sprint_category = :category
                WHERE seeding > :start AND seeding <= :end AND signed_on = 'Yes' AND qualifying_time IS NOT NULL
                """),
                {"category": category, "start": seeding, "end": seeding + num_riders}
            )
            seeding += num_riders  # update the seeding range for the next category

        # Commit the changes
        connection.commit()

    return "Qualifying times for female riders updated successfully"

from flask import render_template
from sqlalchemy import text

@app.route('/complete_qualifying', methods=['GET'])
def complete_qualifying():
    # Add your logic here to complete qualifying times for both males and females
    # ...

    return redirect('/qualifying_results')

from flask import session
from models import RidersMale  # Replace 'main' with the actual file name if different

# Route for printing the table
@app.route('/complete_male_qualifying', methods=['GET', 'POST'])
def complete_male_qualifying():
    if request.method == 'POST':
        selected_printer = request.form.get('printer')
        if not selected_printer:
            return "Printer not selected"
        
        with Session() as session:
            male_riders_signedon = session.query(RidersMale).filter_by(signed_on='Yes').all()
            
            # Generate HTML table with the latest data
            table_html = "<table>"
            table_html += "<tr><th>Rider Number</th><th>Rider Name</th><th>Rider Club</th></tr>"
            for rider in male_riders_signedon:
                table_html += f"<tr><td>{rider.rider_number}</td><td>{rider.rider_name}</td><td>{rider.rider_club}</td></tr>"
            table_html += "</table>"
            
            # Configure PDF options
            options = {
                'page-size': 'A4',
                'orientation': 'portrait',
                'encoding': 'UTF-8',
                'no-outline': None
            }
            
            # Convert HTML table to PDF
            pdf_file = pdfkit.from_string(table_html, False, options=options)
            
            # Send PDF to printer
            print_command = f'print /D:"{selected_printer}" "{pdf_file}"'
            subprocess.run(print_command, shell=True)
            
            return Response('Printing complete', mimetype='text/plain')
    else:
        # Handle GET request if needed
        return "Method Not Allowed"

@app.route('/complete_female_qualifying', methods=['GET', 'POST'])
def complete_female_qualifying():
    if request.method == 'POST':
        selected_printer = request.form.get('printer')
        if not selected_printer:
            return "Printer not selected"
        
        with Session() as session:
            female_riders_signedon = session.query(RidersFemale).filter_by(signed_on='Yes').all()
            
            # Generate HTML table with the latest data
            table_html = "<table>"
            table_html += "<tr><th>Rider Number</th><th>Rider Name</th><th>Rider Club</th></tr>"
            for rider in female_riders_signedon:
                table_html += f"<tr><td>{rider.rider_number}</td><td>{rider.rider_name}</td><td>{rider.rider_club}</td></tr>"
            table_html += "</table>"
            
            # Configure PDF options
            options = {
                'page-size': 'A4',
                'orientation': 'portrait',
                'encoding': 'UTF-8',
                'no-outline': None
            }
            
            # Convert HTML table to PDF
            pdf_file = pdfkit.from_string(table_html, False, options=options)
            
            # Send PDF to printer
            print_command = f'print /D:"{selected_printer}" "{pdf_file}"'
            subprocess.run(print_command, shell=True)
            
            return Response('Printing complete', mimetype='text/plain')
    else:
        # Handle GET request if needed
        return "Method Not Allowed"

from sqlalchemy import asc

from flask import request

@app.route('/qualifying_results')
def qualifying_results():
    output_format = request.args.get('format', 'html')  # Get the output format from query parameter, default to 'html'

    with db_session() as db:

        male_riders_signedon = db.query(RidersMale).filter(
            RidersMale.signed_on == "Yes",
            RidersMale.qualifying_time.isnot(None),
            RidersMale.qualifying_time > 0
        ).order_by(RidersMale.seeding).all()
    
        female_riders_signedon = db.query(RidersFemale).filter(
            RidersFemale.signed_on == "Yes",
            RidersFemale.qualifying_time.isnot(None),
            RidersFemale.qualifying_time > 0
        ).order_by(RidersFemale.seeding).all()

        if output_format == 'pdf':
            # Generate PDF
            pdf_content = pdfkit.from_string(
                render_template(
                    'qualifying_results.html',
                    male_riders_signedon=male_riders_signedon,
                    female_riders_signedon=female_riders_signedon
                ), 
                False
            )
            
            with open('qualifying_results.pdf', 'wb') as f:
                f.write(pdf_content)

            # Upload to Dropbox
            upload_result = upload_to_dropbox(DROPBOX_ACCESS_TOKEN, 'qualifying_results.pdf')
            
            if upload_result:
                print("Uploaded to Dropbox:", 'qualifying_results.pdf')
                return jsonify({"success": True, "message": "File uploaded successfully"}), 200
            else:
                print("Error uploading to Dropbox")
                return jsonify({"success": False, "message": "Error uploading to Dropbox"}), 500

        elif output_format == 'html':
            # Render HTML
            return render_template(
                'qualifying_results.html',
                male_riders_signedon=male_riders_signedon,
                female_riders_signedon=female_riders_signedon
            )
        
        else:
            return jsonify({"success": False, "message": "Invalid format"}), 400


from flask import render_template
from models import RidersMale  # Replace 'main' with the actual file name if different
from collections import defaultdict

def generate_round1_pairings(riders, sprint_categories):
    riders_by_category = defaultdict(list)

    # Group riders by sprint category
    for rider in riders:
        riders_by_category[rider.sprint_category].append(rider)

    pairings = {}

    # Generate pairings for each sprint category
    for category, riders_in_category in riders_by_category.items():
        if category not in sprint_categories:
            continue

        num_riders = len(riders_in_category)
        num_pairings = sprint_categories[category]

        if num_riders < num_pairings:
            # Add "BYE" pairings for the remaining slots
            bye_count = num_pairings - num_riders
            riders_in_category.extend(["BYE"] * bye_count)
            riders_in_category = [rider for rider in riders_in_category if rider != "BYE"]
            print(f"Riders in category '{category}':", [rider.rider_name if isinstance(rider, RidersMale) else rider for rider in riders_in_category])

        # Sort riders in the category by seeding
        riders_in_category.sort(key=lambda rider: int(rider.seeding) if rider.seeding else float('inf'))

        # Generate pairings based on seeding
        pairings_category = []

        if num_riders == 6:
            pairings_category = generate_pairings_6(riders_in_category)
        elif num_riders == 7:
            pairings_category = generate_pairings_7(riders_in_category)
        elif num_riders == 8:
            pairings_category = generate_pairings_8(riders_in_category)
        elif num_riders == 9:
            pairings_category = generate_pairings_9(riders_in_category)
        elif num_riders == 10:
            pairings_category = generate_pairings_10(riders_in_category)
        elif num_riders == 11:
            pairings_category = generate_pairings_11(riders_in_category)
        elif num_riders == 12:
            pairings_category = generate_pairings_12(riders_in_category)
        elif num_riders == 13:
            pairings_category = generate_pairings_13(riders_in_category)
        elif num_riders == 14:
            pairings_category = generate_pairings_14(riders_in_category)
        elif num_riders == 15:
            pairings_category = generate_pairings_15(riders_in_category)
        elif num_riders == 16:
            pairings_category = generate_pairings_16(riders_in_category)
        elif num_riders == 17:
            pairings_category = generate_pairings_17(riders_in_category)

        # Extract rider names for each pairing
        pairings_category_with_names = []
        for pairing in pairings_category:
            transformed_pairing = [rider.rider_name if isinstance(rider, RidersMale) else rider for rider in pairing]
            print("Transformed:", transformed_pairing)
            pairing_with_names = {
                'pairing': transformed_pairing,
                'category': category
            }    
            pairings_category_with_names.append(pairing_with_names)


        pairings[category] = pairings_category_with_names


    for category, pairings_category in pairings.items():
        print(f"Sprint {category} Pairings:")
        for idx, pairing in enumerate(pairings_category, start=1):
            pairing_str = ', '.join(pairing['pairing'])
            print(f"{idx}. {pairing_str}")


    from sqlalchemy import text

    with engine.connect() as connection:
        for category, pairings_category in pairings.items():
            for index, pairing in enumerate(pairings_category, 1):
                for rider in pairing['pairing']:
                    if rider != "BYE":
                        rider_name = rider.rider_name if isinstance(rider, RidersMale) else rider
                        update_statement = text("""
                            UPDATE Riders_Male
                            SET round_1_pairing = :pairing_num
                            WHERE rider_name = :rider_name
                        """)
                        connection.execute(update_statement, {"pairing_num": index, "rider_name": rider_name})

        connection.commit()


    return pairings

from collections import defaultdict
from flask import render_template
from models import RidersFemale  # Replace 'main' with the actual file name if different

def generate_round1_pairings_female(riders, sprint_categories):
    riders_by_category = defaultdict(list)

    # Group riders by sprint category
    for rider in riders:
        riders_by_category[rider.sprint_category].append(rider)

    pairings = {}

    # Generate pairings for each sprint category
    for category, riders_in_category in riders_by_category.items():
        if category not in sprint_categories:
            continue

        num_riders = len(riders_in_category)
        num_pairings = sprint_categories[category]

        if num_riders < num_pairings:
            # Add "BYE" pairings for the remaining slots
            bye_count = num_pairings - num_riders
            riders_in_category.extend(["BYE"] * bye_count)
            riders_in_category = [rider for rider in riders_in_category if rider != "BYE"]
            print(f"Riders in category '{category}':", [rider.rider_name if isinstance(rider, RidersFemale) else rider for rider in riders_in_category])

        # Sort riders in the category by seeding
        riders_in_category.sort(key=lambda rider: int(rider.seeding) if rider.seeding else float('inf'))

        # Generate pairings based on seeding
        pairings_category = []

        if num_riders == 6:
            pairings_category = generate_pairings_6(riders_in_category)
        elif num_riders == 7:
            pairings_category = generate_pairings_7(riders_in_category)
        elif num_riders == 8:
            pairings_category = generate_pairings_8(riders_in_category)
        elif num_riders == 9:
            pairings_category = generate_pairings_9(riders_in_category)
        elif num_riders == 10:
            pairings_category = generate_pairings_10(riders_in_category)
        elif num_riders == 11:
            pairings_category = generate_pairings_11(riders_in_category)
        elif num_riders == 12:
            pairings_category = generate_pairings_12(riders_in_category)
        elif num_riders == 13:
            pairings_category = generate_pairings_13(riders_in_category)
        elif num_riders == 14:
            pairings_category = generate_pairings_14(riders_in_category)
        elif num_riders == 15:
            pairings_category = generate_pairings_15(riders_in_category)
        elif num_riders == 16:
            pairings_category = generate_pairings_16(riders_in_category)
        elif num_riders == 17:
            pairings_category = generate_pairings_17(riders_in_category)

        # Extract rider names for each pairing
        pairings_category_with_names = []
        for pairing in pairings_category:
            transformed_pairing = [rider.rider_name if isinstance(rider, RidersFemale) else rider for rider in pairing]
            print("Transformed:", transformed_pairing)
            pairing_with_names = {
                'pairing': transformed_pairing,
                'category': category
            }    
            pairings_category_with_names.append(pairing_with_names)


        pairings[category] = pairings_category_with_names


    for category, pairings_category in pairings.items():
        print(f"Sprint {category} Pairings:")
        for idx, pairing in enumerate(pairings_category, start=1):
            pairing_str = ', '.join(pairing['pairing'])
            print(f"{idx}. {pairing_str}")


    from sqlalchemy import text

    with engine.connect() as connection:
        for category, pairings_category in pairings.items():
            for index, pairing in enumerate(pairings_category, 1):
                for rider in pairing['pairing']:
                    if rider != "BYE":
                        rider_name = rider.rider_name if isinstance(rider, RidersFemale) else rider
                        update_statement = text("""
                            UPDATE Riders_Female
                            SET round_1_pairing = :pairing_num
                            WHERE rider_name = :rider_name
                        """)
                        connection.execute(update_statement, {"pairing_num": index, "rider_name": rider_name})

        connection.commit()


    return pairings

def generate_pairings_6(riders):
    pairings = []
    pairing_1 = [riders[0], riders[5]]
    pairing_2 = [riders[1], riders[4]]
    pairing_3 = [riders[2], riders[3]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    return pairings

def generate_pairings_7(riders):
    pairings = []
    pairing_1 = [riders[0], riders[6]]
    pairing_2 = [riders[1], riders[5]]
    pairing_3 = [riders[2], riders[3], riders[4]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    return pairings

def generate_pairings_8(riders):
    pairings = []
    pairing_1 = [riders[0], riders[7]]
    pairing_2 = [riders[1], riders[6]]
    pairing_3 = [riders[2], riders[5]]
    pairing_4 = [riders[3], riders[4]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    return pairings

def generate_pairings_9(riders):
    pairings = []
    pairing_1 = [riders[0], "BYE"]
    pairing_2 = [riders[1], "BYE"]
    pairing_3 = [riders[2], "BYE"]
    pairing_4 = [riders[3], riders[8]]
    pairing_5 = [riders[4], riders[7]]
    pairing_6 = [riders[5], riders[6]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

def generate_pairings_10(riders):
    pairings = []
    pairing_1 = [riders[0], "BYE"]
    pairing_2 = [riders[1], "BYE"]
    pairing_3 = [riders[2], riders[9]]
    pairing_4 = [riders[3], riders[8]]
    pairing_5 = [riders[4], riders[7]]
    pairing_6 = [riders[5], riders[6]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

def generate_pairings_11(riders):
    pairings = []
    pairing_1 = [riders[0], "BYE"]
    pairing_2 = [riders[1], riders[10]]
    pairing_3 = [riders[2], riders[9]]
    pairing_4 = [riders[3], riders[8]]
    pairing_5 = [riders[4], riders[7]]
    pairing_6 = [riders[5], riders[6]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

def generate_pairings_12(riders):
    pairings = []
    pairing_1 = [riders[0], riders[11]]
    pairing_2 = [riders[1], riders[10]]
    pairing_3 = [riders[2], riders[9]]
    pairing_4 = [riders[3], riders[8]]
    pairing_5 = [riders[4], riders[7]]
    pairing_6 = [riders[5], riders[6]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

def generate_pairings_13(riders):
    pairings = []
    pairing_1 = [riders[0], riders[12]]
    pairing_2 = [riders[1], riders[11]]
    pairing_3 = [riders[2], riders[10]]
    pairing_4 = [riders[3], riders[9]]
    pairing_5 = [riders[4], riders[8]]
    pairing_6 = [riders[5], riders[6], riders[7]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

def generate_pairings_14(riders):
    pairings = []
    pairing_1 = [riders[0], riders[13]]
    pairing_2 = [riders[1], riders[12]]
    pairing_3 = [riders[2], riders[11]]
    pairing_4 = [riders[3], riders[10]]
    pairing_5 = [riders[4], riders[9], riders[8]]
    pairing_6 = [riders[5], riders[7], riders[6]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

def generate_pairings_15(riders):
    pairings = []
    pairing_1 = [riders[0], riders[14]]
    pairing_2 = [riders[1], riders[13]]
    pairing_3 = [riders[2], riders[12]]
    pairing_4 = [riders[3], riders[11], riders[8]]
    pairing_5 = [riders[4], riders[10], riders[7]]
    pairing_6 = [riders[5], riders[9], riders[6]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

def generate_pairings_16(riders):
    pairings = []
    pairing_1 = [riders[0], riders[15]]
    pairing_2 = [riders[1], riders[14]]
    pairing_3 = [riders[2], riders[13], riders[9]]
    pairing_4 = [riders[3], riders[12], riders[8]]
    pairing_5 = [riders[4], riders[11], riders[7]]
    pairing_6 = [riders[5], riders[10], riders[6]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

def generate_pairings_17(riders):
    pairings = []
    pairing_1 = [riders[0], riders[16]]
    pairing_2 = [riders[1], riders[15], riders[10]]
    pairing_3 = [riders[2], riders[14], riders[9]]
    pairing_4 = [riders[3], riders[13], riders[8]]
    pairing_5 = [riders[4], riders[12], riders[7]]
    pairing_6 = [riders[5], riders[11], riders[6]]
    pairings.append(pairing_1)
    pairings.append(pairing_2)
    pairings.append(pairing_3)
    pairings.append(pairing_4)
    pairings.append(pairing_5)
    pairings.append(pairing_6)
    return pairings

    # Commit all changes to the database outside the loop
    db.session.commit()

    return "Round 1 heats updated successfully"

from flask import render_template
from models import RidersMale
from main import db_session

def get_nth_selected_rider(data, nth=1):
    """Get the nth selected rider."""
    riders = [key for key in data.keys() if key.startswith('selectedRider')]

    # Filter out entries without a number attached (like 'BYE')
    valid_riders = [rider for rider in riders if re.search(r'(\d+)$', data[rider])]

    # Get the nth selected rider based on the numbering system
    nth_selected_rider = sorted(valid_riders, key=lambda x: int(re.search(r'(\d+)$', data[x]).group()))[nth-1]
    
    return clean_rider_name(data[nth_selected_rider])

def get_riders_count_in_category(category):
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM riders_male WHERE sprint_category = :category"),
            {"category": category}
        )
        count = result.scalar()
    print(f"Total riders in {category}: {count}")  # Debug Print
    return count

def get_riders_count_in_category_female(category):
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM riders_female WHERE sprint_category = :category"),
            {"category": category}
        )
        count = result.scalar()
    print(f"Total riders in {category}: {count}")  # Debug Print
    return count


@app.route('/round1')
def round1():
    Session = sessionmaker(bind=engine)
    session = Session()

    riders = session.query(RidersMale).all()

    # Assign sprint categories
    sprint_categories = assign_sprint_categories(len(riders))

    pairings = generate_round1_pairings(riders, sprint_categories)

    global round1_heat_to_positions  # Declare as global
    if not round1_heat_to_positions:
        # Assuming you have a default category for round 1
        category = "default_category"  # Replace with your actual logic to determine category
        total_riders_in_category = get_riders_count_in_category(category)
        round1_heat_to_positions = get_round1_heat_to_positions(total_riders_in_category)

    return render_template('round_1.html', pairings=pairings, sprint_categories=sprint_categories)


@app.route('/round1_female')
def round1_female():
    Session = sessionmaker(bind=engine)
    session = Session()

    riders = session.query(RidersFemale).all()

    # Assign sprint categories
    sprint_categories = assign_sprint_categories(len(riders))

    pairings = generate_round1_pairings_female(riders, sprint_categories)

    global round1_heat_to_positions  # Declare as global
    if not round1_heat_to_positions:
        # Assuming you have a default category for round 1 female
        category = "default_category_female"  # Replace with your actual logic to determine category
        total_riders_in_category = get_riders_count_in_category_female(category)
        round1_heat_to_positions = get_round1_heat_to_positions(total_riders_in_category)

    return render_template('round_1_female.html', pairings=pairings, sprint_categories=sprint_categories)

from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from models import RidersMale

def clean_rider_name(name):
    return name.split("\n")[0].strip()

def get_round1_heat_to_positions(total_riders_in_category):
    if total_riders_in_category == 17:
        return {
            'Heat 1': (1, 17),
            'Heat 2': (2, 11, 16),
            'Heat 3': (3, 10, 15),
            'Heat 4': (4, 9, 14),
            'Heat 5': (5, 8, 13),
            'Heat 6': (6, 7, 12)
        }
    elif total_riders_in_category == 16:
        return {
            'Heat 1': (1, 16),
            'Heat 2': (2, 15),
            'Heat 3': (3, 10, 14),
            'Heat 4': (4, 9, 13),
            'Heat 5': (5, 8, 12),
            'Heat 6': (6, 7, 11)
        }
    elif total_riders_in_category == 15:
        return {
            'Heat 1': (1, 15),
            'Heat 2': (2, 14),
            'Heat 3': (3, 13),
            'Heat 4': (4, 9, 12),
            'Heat 5': (5, 8, 11),
            'Heat 6': (6, 7, 10)
        }
    elif total_riders_in_category == 14:
        return {
            'Heat 1': (1, 14),
            'Heat 2': (2, 13),
            'Heat 3': (3, 12),
            'Heat 4': (4, 11),
            'Heat 5': (5, 9, 10),
            'Heat 6': (6, 7, 8)
        }
    elif total_riders_in_category == 13:
        return {
            'Heat 1': (1, 13),
            'Heat 2': (2, 12),
            'Heat 3': (3, 11),
            'Heat 4': (4, 10),
            'Heat 5': (5, 9),
            'Heat 6': (6, 7, 8)
        }
    elif total_riders_in_category == 12:
        return {
            'Heat 1': (1, 12),
            'Heat 2': (2, 11),
            'Heat 3': (3, 10),
            'Heat 4': (4, 9),
            'Heat 5': (5, 8),
            'Heat 6': (6, 7)
        }
    elif total_riders_in_category == 11:
        return {
            'Heat 1': (1,),
            'Heat 2': (2, 11),
            'Heat 3': (3, 10),
            'Heat 4': (4, 9),
            'Heat 5': (5, 8),
            'Heat 6': (6, 7)
        }
    elif total_riders_in_category == 10:
        return {
            'Heat 1': (1,),
            'Heat 2': (2,),
            'Heat 3': (3, 10),
            'Heat 4': (4, 9),
            'Heat 5': (5, 8),
            'Heat 6': (6, 7)
        }
    elif total_riders_in_category == 9:
        return {
            'Heat 1': (1,),
            'Heat 2': (2,),
            'Heat 3': (3,),
            'Heat 4': (4, 9),
            'Heat 5': (5, 8),
            'Heat 6': (6, 7)
        }
    elif total_riders_in_category == 8:
        return {
            'Heat 1': (1, 8),
            'Heat 2': (2, 7),
            'Heat 3': (3, 6),
            'Heat 4': (4, 5)
        }
    elif total_riders_in_category == 7:
        return {
            'Heat 1': (1, 7),
            'Heat 2': (2, 6),
            'Heat 3': (3, 4, 5),
        }
    elif total_riders_in_category == 6:
        return {
            'Heat 1': (1, 6),
            'Heat 2': (2, 5),
            'Heat 3': (3, 4)
        }

import re
from flask import request, jsonify

round1_heat_to_positions = {}

@app.route('/update_round1_seeding', methods=['POST'])
def update_round1_seeding():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Try fetching category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_male WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided riders.")
                total_riders = get_riders_count_in_category(category) 
        seeding_structure = get_round1_heat_to_positions(total_riders)
        
        heat = data['heatNumber']
        
        # Ensure heat is in the seeding structure
        if heat not in seeding_structure:
            raise ValueError(f"No seeding structure defined for {heat}.")
        
        heat_positions = seeding_structure[heat]

        with engine.connect() as connection:
            for index, seed in enumerate(heat_positions):
                rider_name = get_nth_selected_rider(data, index + 1)
                if rider_name:  
                    print(f"Rider Name for seed {seed}: {rider_name}")

                    # Update the rider's seeding in round 1 seeding column
                    connection.execute(
                        text("UPDATE Riders_Male SET round_1_seeding = :seed WHERE rider_name = :rider_name"),
                        {"rider_name": rider_name, "seed": seed}
                    )

                    # Update Quarter Final Seeding for the winner
                    if seed == heat_positions[0]:  # Only update for the winner
                        connection.execute(
                            text("UPDATE Riders_Male SET quarter_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )

                        # Update Semi Final Seeding for the winner if applicable
                        if total_riders in range(6, 10):
                            connection.execute(
                                text("UPDATE Riders_Male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )

            connection.commit()

        return jsonify({"success": True, "message": "Round 1 seeding updated successfully"}), 200

    except Exception as e:
        # Handle exceptions here
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/update_round1_seeding_female', methods=['POST'])
def update_round1_seeding_female():
    data = request.json
    print(f"Incoming data: {data}")
    incoming_data = request.form
    app.logger.debug("Incoming data: %s", incoming_data)

    # Extract and order riders based on selection
    riders_data = [{"name": clean_rider_name(data['selectedRider1']), "order": int(re.search(r'(\d+)', data['selectedRider1']).group())}]

    # Check if there's a second rider
    if 'selectedRider2' in data and data['selectedRider2'] != "BYE":
        riders_data.append({"name": clean_rider_name(data['selectedRider2']), "order": int(re.search(r'(\d+)', data['selectedRider2']).group())})

    riders_data.sort(key=lambda x: x['order'])

    # Handle the winner-loser assignment
    winner = riders_data[0]['name']
    loser = riders_data[1]['name'] if len(riders_data) > 1 else None

    # Debug Print: Data received and cleaned names
    print(f"Heat Number: {data['heatNumber']} | Winner: {winner} | Loser: {loser if loser else 'BYE'}")

    heat_number = data['heatNumber']

    with engine.connect() as connection:
        try:
            # Debug Print: Data received and cleaned names
            print(f"Heat Number: {heat_number} | Rider1: {winner} | Rider2: {loser if loser else 'BYE'}")

            if heat_number not in heat_to_positions:
                return jsonify({"success": False, "message": "Invalid heat number"}), 400

            rider = connection.execute(
                text("SELECT * FROM riders_female WHERE rider_name = :selected_rider"),
                {"selected_rider": winner}
            ).fetchone()

            if not rider:
                return jsonify({"success": False, "message": f"Invalid rider name {winner}"}), 400

            sprint_category = rider.sprint_category
            total_riders_in_category = connection.execute(
                text("SELECT COUNT(*) FROM riders_female WHERE sprint_category = :sprint_category"),
                {"sprint_category": sprint_category}
            ).scalar()

            # Debug Print: Sprint Category and Total riders in that category
            print(f"Sprint Category: {sprint_category} | Total Riders: {total_riders_in_category}")



            if total_riders_in_category == 17:
                heat_to_positions.update({
                    'Heat 1': (1, 17),
                    'Heat 2': (2, 11, 16),
                    'Heat 3': (3, 10, 15),
                    'Heat 4': (4, 9, 14),
                    'Heat 5': (5, 8, 13),
                    'Heat 6': (6, 7, 12)
                })
            elif total_riders_in_category == 16:
                heat_to_positions.update({
                    'Heat 1': (1, 16),
                    'Heat 2': (2, 15),
                    'Heat 3': (3, 10, 14),
                    'Heat 4': (4, 9, 13),
                    'Heat 5': (5, 8, 12),
                    'Heat 6': (6, 7, 11)
                })
            elif total_riders_in_category == 15:
                heat_to_positions.update({
                    'Heat 1': (1, 15),
                    'Heat 2': (2, 14),
                    'Heat 3': (3, 13),
                    'Heat 4': (4, 9, 12),
                    'Heat 5': (5, 8, 11),
                    'Heat 6': (6, 7, 10)
                })                
            elif total_riders_in_category == 14:
                heat_to_positions.update({
                    'Heat 1': (1, 14),
                    'Heat 2': (2, 13,),
                    'Heat 3': (3, 12),
                    'Heat 4': (4, 11),
                    'Heat 5': (5, 9, 10),
                    'Heat 6': (6, 7, 8)
                })
            elif total_riders_in_category == 13:
                heat_to_positions.update({
                    'Heat 1': (1, 13),
                    'Heat 2': (2, 12),
                    'Heat 3': (3, 11),
                    'Heat 4': (4, 10),
                    'Heat 5': (5, 9),
                    'Heat 6': (6, 7, 8)
                })                
            elif total_riders_in_category == 12:
                heat_to_positions.update({
                    'Heat 1': (1, 12),
                    'Heat 2': (2, 11),
                    'Heat 3': (3, 10),
                    'Heat 4': (4, 9),
                    'Heat 5': (5, 8),
                    'Heat 6': (6, 7)
                })    
            elif total_riders_in_category == 11:
                heat_to_positions.update({
                    'Heat 1': (1),
                    'Heat 2': (2, 11),
                    'Heat 3': (3, 10),
                    'Heat 4': (4, 9),
                    'Heat 5': (5, 8),
                    'Heat 6': (6, 7)
                })
            elif total_riders_in_category == 10:
                heat_to_positions.update({
                    'Heat 1': (1),
                    'Heat 2': (2),
                    'Heat 3': (3, 10),
                    'Heat 4': (4, 9),
                    'Heat 5': (5, 8),
                    'Heat 6': (6, 7)
                })
            elif total_riders_in_category == 9:
                heat_to_positions.update({
                    'Heat 1': (1),
                    'Heat 2': (2),
                    'Heat 3': (3),
                    'Heat 4': (4, 9),
                    'Heat 5': (5, 8),
                    'Heat 6': (6, 7)
                })
            elif total_riders_in_category == 8:
                heat_to_positions.update({
                    'Heat 1': (1, 8),
                    'Heat 2': (2, 7),
                    'Heat 3': (3, 6),
                    'Heat 4': (4, 5)
                })
            elif total_riders_in_category == 7:
                heat_to_positions.update({
                    'Heat 1': (1, 7),
                    'Heat 2': (2, 6),
                    'Heat 3': (3, 4, 5),
                })
            elif total_riders_in_category == 6:
                heat_to_positions.update({
                    'Heat 1': (1, 6),
                    'Heat 2': (2, 5),
                    'Heat 3': (3, 4)
                })    

            # Assign based on the user's clicks, `winner` is the selected winner and `loser` is the selected loser
            positions = heat_to_positions[heat_number]
            if isinstance(positions, int):
                winner_position = positions
                loser_position = None
            elif len(positions) == 1:
                winner_position = positions[0]
                loser_position = None
            else:
                winner_position, loser_position = positions[:2]



            rider_data_for_db = [{"position": winner_position, "rider_name": winner}]
            if loser and loser != "BYE":
                rider_data_for_db.append({"position": loser_position, "rider_name": loser})


            connection.execute(
                text("UPDATE riders_female SET round_1_seeding = :position WHERE rider_name = :rider_name"),
                rider_data_for_db
            )

            # Update Quarter Final Seeding for the winner (assuming you have a quarter_final_seeding column)
            connection.execute(
                text("UPDATE riders_female SET quarter_final_seeding = :position WHERE rider_name = :rider_name"),
                {"position": heat_to_positions[heat_number][0], "rider_name": winner}
                )

            # If there are 6, 7, or 8 riders, update Semi Final Seeding for the winner as well
            if total_riders_in_category in [6, 7, 8]:
                connection.execute(
                    text("UPDATE riders_female SET semi_final_seeding = :position WHERE rider_name = :rider_name"),
                    {"position": heat_to_positions[heat_number][0], "rider_name": winner}
                )

            # Non-Selected Rider Logic
            if loser and len(heat_to_positions[heat_number]) == 3:
                non_selected_rider = connection.execute(
                    text("SELECT rider_name FROM riders_female WHERE sprint_category = :sprint_category AND round_1_pairing = :pairing AND rider_name NOT IN (:winner, :loser)"),
                    {"sprint_category": sprint_category, "pairing": heat_number.split(' ')[1], "winner": winner, "loser": loser}
                ).scalar()


                print(f"Non-Selected Rider: {non_selected_rider}")
                print(f"Seeding for Non-Selected Rider: {heat_to_positions[heat_number][2]}")

                connection.execute(
                    text("UPDATE riders_female SET round_1_seeding = :position WHERE rider_name = :rider_name"),
                    {"position": heat_to_positions[heat_number][2], "rider_name": non_selected_rider}
                )


            connection.commit()
            return jsonify({"success": True, "message": "Seeding updated successfully"}), 200

        except Exception as e:
            print("Error:", str(e))
            return jsonify({"success": False, "message": str(e)}), 500

@app.route('/rep1')
def rep():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_male WHERE round_1_seeding IS NOT NULL")
        ).fetchall()
        
        all_rep_pairings = {}
        
        for category in sprint_categories:
            riders_for_reps = connection.execute(
                text("SELECT rider_name, round_1_seeding FROM riders_male WHERE sprint_category = :sprint_category AND signed_on = 'Yes' ORDER BY round_1_seeding DESC"),
                {"sprint_category": category[0]}
            ).fetchall()
            print(f"For category {category[0]}, fetched riders: {riders_for_reps}")
            
            total_riders = len(riders_for_reps)
            if total_riders > 0:
                if total_riders == 6:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [4, 5, 6]]
                    }

                elif total_riders == 7:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [4, 5, 6, 7]]
                    }

                elif total_riders == 8:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [5, 6, 7, 8]]
                    }

                elif total_riders == 9:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 8, 9]]
                    }

                elif total_riders == 10:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 10]],
                        'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9]]
                    }

                elif total_riders == 11:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 11]],
                        'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9, 10]]
                    }

                elif total_riders == 12:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 10, 12]],
                        'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9, 11]]
                    }

                elif total_riders == 13:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 11, 13]],
                        'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9, 10, 12]]
                    }

                elif total_riders == 14:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 12, 13, 14]],
                        'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9, 10, 11]]
                    }

                elif total_riders == 15:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 13, 15]],
                        'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 12, 14]],
                        'Rep Heat 3': [rider[0] for rider in riders_for_reps if rider[1] in [9, 10, 11]]
                    }

                elif total_riders == 16:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 10, 16]],
                        'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 13, 15]],
                        'Rep Heat 3': [rider[0] for rider in riders_for_reps if rider[1] in [9, 11, 12, 14]]
                    }

                elif total_riders == 17:
                    rep_heats = {
                        'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 10, 17]],
                        'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 12, 14, 16]],
                        'Rep Heat 3': [rider[0] for rider in riders_for_reps if rider[1] in [9, 11, 13, 15]]
                    }

                else:
                    rep_heats = {}  # or some default behavior if needed
                print(f"For category {category[0]}, selected riders for repechage: {rep_heats}")
                all_rep_pairings[category[0]] = rep_heats
                print(all_rep_pairings)

        return render_template('rep1.html', rep_pairings=all_rep_pairings)

@app.route('/rep1_female')
def rep_female():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_female WHERE round_1_seeding IS NOT NULL")
        ).fetchall()
        
        all_rep_pairings = {}
        
        for category in sprint_categories:
            riders_for_reps = connection.execute(
                text("SELECT rider_name, round_1_seeding FROM riders_female WHERE sprint_category = :sprint_category ORDER BY round_1_seeding DESC"),
                {"sprint_category": category[0]}
            ).fetchall()
            print(f"For category {category[0]}, fetched riders: {riders_for_reps}")
            

            total_riders = len(riders_for_reps)
            
            if total_riders == 6:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [4, 5, 6]]
                }

            elif total_riders == 7:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [4, 5, 6, 7]]
                }

            elif total_riders == 8:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [5, 6, 7, 8]]
                }

            elif total_riders == 9:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 8, 9]]
                }

            elif total_riders == 10:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 10]],
                    'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9]]
                }

            elif total_riders == 11:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 11]],
                    'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9, 10]]
                }

            elif total_riders == 12:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 10, 12]],
                    'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9, 11]]
                }

            elif total_riders == 13:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 11, 13]],
                    'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9, 10, 12]]
                }

            elif total_riders == 14:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 12, 13, 14]],
                    'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 9, 10, 11]]
                }

            elif total_riders == 15:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 13, 15]],
                    'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 12, 14]],
                    'Rep Heat 3': [rider[0] for rider in riders_for_reps if rider[1] in [9, 10, 11]]
                }

            elif total_riders == 16:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 10, 16]],
                    'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 13, 15]],
                    'Rep Heat 3': [rider[0] for rider in riders_for_reps if rider[1] in [9, 11, 12, 14]]
                }

            elif total_riders == 17:
                rep_heats = {
                    'Rep Heat 1': [rider[0] for rider in riders_for_reps if rider[1] in [7, 10, 17]],
                    'Rep Heat 2': [rider[0] for rider in riders_for_reps if rider[1] in [8, 12, 14, 16]],
                    'Rep Heat 3': [rider[0] for rider in riders_for_reps if rider[1] in [9, 11, 13, 15]]
                }

            else:
                rep_heats = {}  # or some default behavior if needed
            print(f"For category {category[0]}, selected riders for repechage: {rep_heats}")
            all_rep_pairings[category[0]] = rep_heats
            print(all_rep_pairings)

        
        return render_template('rep1_female.html', rep_pairings=all_rep_pairings)

from flask import Flask, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
import re

def get_seeding_structure(total_riders):
    if total_riders == 6:
        return {
            'Heat 1': [4, 5, 6]
        }

    elif total_riders == 7:
        return {
            'Heat 1': [4, 5, 6, 7]
        }

    elif total_riders == 8:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 9:
        return {
            'Heat 1': [7, 8, 9]
        }

    elif total_riders == 10:
        return {
            'Heat 1': [7, 10],
            'Heat 2': [8, 9]
        }

    elif total_riders == 11:
        return {
            'Heat 1': [7, 11],
            'Heat 2': [8, 9, 10]
        }

    elif total_riders == 12:
        return {
            'Heat 1': [7, 10, 12],
            'Heat 2': [8, 9, 11]
        }

    elif total_riders == 13:
        return {
            'Heat 1': [7, 11, 13],
            'Heat 2': [8, 9, 10, 12]
        }

    elif total_riders == 14:
        return {
            'Heat 1': [7, 10, 12, 14],
            'Heat 2': [8, 9, 11, 13]
        }
    
    elif total_riders == 15:
        return {
            'Heat 1': [7, 12, 15],
            'Heat 2': [8, 11, 14],
            'Heat 3': [9, 10, 13]
        }

    elif total_riders == 16:
        return {
            'Heat 1': [7, 12, 15],
            'Heat 2': [8, 11, 14],
            'Heat 3': [9, 10, 13, 16]
        }

    elif total_riders == 17:
        return {
            'Heat 1': [7, 10, 15],
            'Heat 2': [8, 12, 14, 17],
            'Heat 3': [9, 11, 13, 16]
        }
    else:
        return None

@app.route('/submit_rep_results', methods=['POST'])
def submit_rep_results():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Try fetching category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_male WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                total_riders = get_riders_count_in_category(category)
        seeding_structure = get_seeding_structure(total_riders)
        
        heat = data['heatNumber']
        
        # Ensure heat is in the seeding structure
        if heat not in seeding_structure:
            raise ValueError(f"No seeding structure defined for {heat}.")
        
        heat_seeding = seeding_structure[heat]

        with engine.connect() as connection:
            for index, seed in enumerate(heat_seeding):
                rider_name = get_nth_selected_rider(data, index + 1)
                if rider_name:  
                    print(f"Rider Name for seed {seed}: {rider_name}")

                    # Update the rider's seeding in quarter_final_seeding column
                    connection.execute(
                        text("UPDATE riders_male SET quarter_final_seeding = :seed WHERE rider_name = :rider_name"),
                        {"rider_name": rider_name, "seed": seed}
                    )

                    # Update semi_final_seeding column if required
                    if total_riders in [6, 7, 8]:
                        connection.execute(
                            text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )

                    elif total_riders == 9 and seed == 9:
                        connection.execute(
                            text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    elif 10 <= total_riders <= 14 and 9 <= seed <= 14:
                        connection.execute(
                            text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    elif 15 <= total_riders <= 17 and 10 <= seed <= 17:
                        connection.execute(
                            text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    connection.commit()

        return jsonify({"success": True, "message": "Quarter final seeding updated successfully for rep round"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/submit_rep_results_female', methods=['POST'])
def submit_rep_results_female():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Try fetching category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_female WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                total_riders = get_riders_count_in_category_female(category)
        seeding_structure = get_seeding_structure(total_riders)
        
        heat = data['heatNumber']
        
        # Ensure heat is in the seeding structure
        if heat not in seeding_structure:
            raise ValueError(f"No seeding structure defined for {heat}.")
        
        heat_seeding = seeding_structure[heat]

        with engine.connect() as connection:
            for index, seed in enumerate(heat_seeding):
                rider_name = get_nth_selected_rider(data, index + 1)
                if rider_name:  
                    print(f"Rider Name for seed {seed}: {rider_name}")

                    # Update the rider's seeding in quarter_final_seeding column
                    connection.execute(
                        text("UPDATE riders_female SET quarter_final_seeding = :seed WHERE rider_name = :rider_name"),
                        {"rider_name": rider_name, "seed": seed}
                    )

                    # Update semi_final_seeding column if required
                    if total_riders in [6, 7, 8]:
                        connection.execute(
                            text("UPDATE riders_female SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )

                    elif total_riders == 9 and seed == 9:
                        connection.execute(
                            text("UPDATE riders_female SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    elif 10 <= total_riders <= 14 and 9 <= seed <= 14:
                        connection.execute(
                            text("UPDATE riders_female SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    elif 15 <= total_riders <= 17 and 10 <= seed <= 17:
                        connection.execute(
                            text("UPDATE riders_female SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    connection.commit()

        return jsonify({"success": True, "message": "Quarter final seeding updated successfully for rep round"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

def get_riders_count_in_category(category):
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM riders_male WHERE sprint_category = :category"),
            {"category": category}
        )
        count = result.scalar()
    print(f"Total riders in {category}: {count}")  # Debug Print
    return count

def get_quarter_final_seeding_structure(total_riders):
    standard_heats = {
        "Heat 1": [1, 8],
        "Heat 2": [2, 7],
        "Heat 3": [3, 6],
        "Heat 4": [4, 5]
    }

    if total_riders in range(6, 9):
        return "Straight to Semi Finals"
    elif total_riders in range(9, 15):
        return standard_heats
    elif total_riders in range(15, 18):
        return {
            "Heat 1": [1, 9],
            "Heat 2": [2, 8],
            "Heat 3": [3, 7],
            "Heat 4": [4, 5, 6]
        }
    else:
        return None  # or raise an error

@app.route('/quarter_finals', methods=['GET', 'POST'])
def quarter_finals():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_male WHERE quarter_final_seeding IS NOT NULL")
        ).fetchall()

        all_quarter_final_pairings = {}

        for category in sprint_categories:
            riders_for_quarter_finals = connection.execute(
                text("SELECT rider_name, quarter_final_seeding FROM riders_male WHERE sprint_category = :sprint_category ORDER BY quarter_final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_quarter_finals)
            
            seeding_structure = get_quarter_final_seeding_structure(total_riders)

            if seeding_structure == "Straight to Semi Finals":
                all_quarter_final_pairings[category[0]] = "Straight to Semi Finals"
            elif seeding_structure is not None:
                quarter_final_heats = {}
                for heat, seeds in seeding_structure.items():
                    quarter_final_heats[heat] = [rider[0] for rider in riders_for_quarter_finals if rider[1] in seeds]

                all_quarter_final_pairings[category[0]] = quarter_final_heats
            else:
                # Handle the case where seeding_structure is None (or another unexpected value), perhaps logging a warning or an error
                pass  # or logging.warning("Seeding structure was unexpected for category %s", category[0])

    return render_template('quarter_final.html', quarter_finals=all_quarter_final_pairings)

@app.route('/quarter_finals_female', methods=['GET', 'POST'])
def quarter_finals_female():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_female WHERE quarter_final_seeding IS NOT NULL")
        ).fetchall()

        all_quarter_final_pairings = {}

        for category in sprint_categories:
            riders_for_quarter_finals = connection.execute(
                text("SELECT rider_name, quarter_final_seeding FROM riders_female WHERE sprint_category = :sprint_category ORDER BY quarter_final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_quarter_finals)
            
            seeding_structure = get_quarter_final_seeding_structure(total_riders)

            if seeding_structure == "Straight to Semi Finals":
                all_quarter_final_pairings[category[0]] = "Straight to Semi Finals"
            elif seeding_structure is not None:
                quarter_final_heats = {}
                for heat, seeds in seeding_structure.items():
                    quarter_final_heats[heat] = [rider[0] for rider in riders_for_quarter_finals if rider[1] in seeds]

                all_quarter_final_pairings[category[0]] = quarter_final_heats
            else:
                # Handle the case where seeding_structure is None (or another unexpected value), perhaps logging a warning or an error
                pass  # or logging.warning("Seeding structure was unexpected for category %s", category[0])

    return render_template('quarter_final_female.html', quarter_finals=all_quarter_final_pairings)

@app.route('/submit_quarter_final_results', methods=['POST'])
def submit_quarter_final_results():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Try fetching category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_male WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                total_riders = get_riders_count_in_category(category)
        seeding_structure = get_quarter_final_seeding_structure(total_riders)
        
        heat = data['heatNumber']
        
        # Ensure heat is in the seeding structure
        if heat not in seeding_structure:
            raise ValueError(f"No seeding structure defined for {heat}.")
        
        heat_seeding = seeding_structure[heat]

        with engine.connect() as connection:
            for index, seed in enumerate(heat_seeding):
                rider_name = get_nth_selected_rider(data, index + 1)
                if rider_name:  
                    print(f"Rider Name for seed {seed}: {rider_name}")

                    # Update the rider's seeding in semi_final_seeding column
                    connection.execute(
                        text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                        {"rider_name": rider_name, "seed": seed}
                    )

                    # Update semi_final_seeding column if required
                    if total_riders in [6, 7, 8]:
                        connection.execute(
                            text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )

                    elif total_riders == 9 and seed == 9:
                        connection.execute(
                            text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    elif 10 <= total_riders <= 14 and 9 <= seed <= 14:
                        connection.execute(
                            text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    elif 15 <= total_riders <= 17 and 10 <= seed <= 17:
                        connection.execute(
                            text("UPDATE riders_male SET semi_final_seeding = :seed WHERE rider_name = :rider_name"),
                            {"rider_name": rider_name, "seed": seed}
                        )
                    connection.commit()

        return jsonify({"success": True, "message": "Quarter final seeding updated successfully"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

def minorfinal1_seeding_structure(total_riders):
    if total_riders == 6:
        return {
            'Heat 1': [5, 6]
        }

    elif total_riders == 7:
        return {
            'Heat 1': [5, 6, 7]
        }

    elif total_riders == 8:
        return {
            'Heat 1': [5, 8],
            'Heat 2': [6, 7]
        }

    elif total_riders == 9:
        return "Straight to Minor Final 2"

    elif total_riders == 10:
        return {
            'Heat 1': [9, 10]
        }

    elif total_riders == 11:
        return {
            'Heat 1': [9, 10, 11]
        }

    elif total_riders == 12:
        return {
            'Heat 1': [9, 10, 11, 12]
        }

    elif total_riders == 13:
        return {
            'Heat 1': [9, 10, 11],
            'Heat 2': [12, 13]
        }

    elif total_riders == 14:
        return {
            'Heat 1': [9, 10],
            'Heat 2': [11, 12],
            'Heat 3': [13, 14]
        }
    
    elif total_riders == 15:
        return {
            'Heat 1': [10, 11, 12],
            'Heat 2': [13, 14, 15]
        }

    elif total_riders == 16:
        return {
            'Heat 1': [10, 11, 12],
            'Heat 2': [13, 14, 15, 16]
        }

    elif total_riders == 17:
        return {
            'Heat 1': [10, 11, 12],
            'Heat 2': [13, 14, 15],
            'Heat 3': [16, 17]
        }
    else:
        return None

def minorfinal1_seeding_structure_female(total_riders):
    if total_riders == 6:
        return {
            'Heat 1': [5, 6]
        }

    elif total_riders == 7:
        return {
            'Heat 1': [5, 6, 7]
        }

    elif total_riders == 8:
        return {
            'Heat 1': [5, 8],
            'Heat 2': [6, 7]
        }

    elif total_riders == 9:
        return "Straight to Minor Final 2"

    elif total_riders == 10:
        return {
            'Heat 1': [9, 10]
        }

    elif total_riders == 11:
        return {
            'Heat 1': [9, 10, 11]
        }

    elif total_riders == 12:
        return {
            'Heat 1': [9, 10, 11, 12]
        }

    elif total_riders == 13:
        return {
            'Heat 1': [9, 10, 11],
            'Heat 2': [12, 13]
        }

    elif total_riders == 14:
        return {
            'Heat 1': [9, 10],
            'Heat 2': [11, 12],
            'Heat 3': [13, 14]
        }
    
    elif total_riders == 15:
        return {
            'Heat 1': [10, 11, 12],
            'Heat 2': [13, 14, 15]
        }

    elif total_riders == 16:
        return {
            'Heat 1': [10, 11, 12],
            'Heat 2': [13, 14, 15, 16]
        }

    elif total_riders == 17:
        return {
            'Heat 1': [10, 11, 12],
            'Heat 2': [13, 14, 15],
            'Heat 3': [16, 17]
        }
    else:
        return None

@app.route('/minorfinals1', methods=['GET', 'POST'])
def minorfinals1():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_male WHERE semi_final_seeding IS NOT NULL")
        ).fetchall()

        all_minor_final_pairings = {}

        for category in sprint_categories:
            riders_for_minor_finals1 = connection.execute(
                text("SELECT rider_name, semi_final_seeding FROM riders_male WHERE sprint_category = :sprint_category ORDER BY semi_final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_minor_finals1)
            
            seeding_structure = minorfinal1_seeding_structure(total_riders)
            
            if seeding_structure == "Straight to Minor Final 2":
                all_minor_final_pairings[category[0]] = "Straight to Minor Final 2"
            elif seeding_structure:  # checking if seeding_structure is not None
                minor_finals1_heats = {}
                for heat, seeds in seeding_structure.items():
                    minor_finals1_heats[heat] = [rider[0] for rider in riders_for_minor_finals1 if rider[1] in seeds]

                all_minor_final_pairings[category[0]] = minor_finals1_heats
            else:
                # Handle the case where seeding_structure is None (or another unexpected value), perhaps logging a warning or an error
                pass  # or logging.warning(f"Seeding structure was unexpected for category {category[0]} with {total_riders} riders")

    return render_template('minorfinals1.html', minor_finals1=all_minor_final_pairings)

@app.route('/minorfinals1_female', methods=['GET', 'POST'])
def minorfinals1_female():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_female WHERE semi_final_seeding IS NOT NULL")
        ).fetchall()

        all_minor_final_pairings = {}

        for category in sprint_categories:
            riders_for_minor_finals1_female = connection.execute(
                text("SELECT rider_name, semi_final_seeding FROM riders_female WHERE sprint_category = :sprint_category ORDER BY semi_final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_minor_finals1_female)
            
            seeding_structure = minorfinal1_seeding_structure_female(total_riders)
            
            if seeding_structure == "Straight to Minor Final 2":
                all_minor_final_pairings[category[0]] = "Straight to Minor Final 2"
            elif seeding_structure:  # checking if seeding_structure is not None
                minor_finals1_heats = {}
                for heat, seeds in seeding_structure.items():
                    minor_finals1_heats[heat] = [rider[0] for rider in riders_for_minor_finals1_female if rider[1] in seeds]

                all_minor_final_pairings[category[0]] = minor_finals1_heats
            else:
                # Handle the case where seeding_structure is None (or another unexpected value), perhaps logging a warning or an error
                pass  # or logging.warning(f"Seeding structure was unexpected for category {category[0]} with {total_riders} riders")

    return render_template('minorfinals1_female.html', minor_finals1=all_minor_final_pairings)

#need to contune editing here as this is where I've gotten up to!

@app.route('/submitminorfinals1', methods=['POST'])
def submitminorfinals1():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Fetch category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_male WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                
        # Based on the category and the number of riders, get the quarter-final seeding structure
        total_riders = get_riders_count_in_category(category)
        minor_final_1_structure = minorfinal1_seeding_structure(total_riders)
        
        # If it's "Straight to Minor Final 2", then no need to update seeding
        if minor_final_1_structure == "Straight to Minor Final 2":
            return jsonify({"success": True, "message": "Riders go straight to Minor Finals 2"}), 200
        
        # Update the semi-final seeding
        with engine.connect() as connection:
            for heat, heat_seeding in minor_final_1_structure.items():
                # Only continue if the current heat matches the submitted heat
                if heat == data['heatNumber']:
                    for index, seed in enumerate(heat_seeding):
                        rider_name = clean_rider_name(get_nth_selected_rider(data, index + 1))
                        if rider_name:
                            # Adjust the below SQL command according to your database structure and requirement
                            connection.execute(
                                text("UPDATE riders_male SET final_seeding = :seed, final_result = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )
                            connection.commit()  # Committing the transaction
                    break  # Exit loop once the matching heat is processed
                
            return jsonify({"success": True, "message": "Semi-final seeding updated successfully for quarter-final results"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/submitminorfinals1_female', methods=['POST'])
def submitminorfinals1_female():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Fetch category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_female WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                
        # Based on the category and the number of riders, get the quarter-final seeding structure
        total_riders = get_riders_count_in_category(category)
        minor_final_1_structure_female = minorfinal1_seeding_structure_female(total_riders)
        
        # If it's "Straight to Minor Final 2", then no need to update seeding
        if minor_final_1_structure_female == "Straight to Minor Final 2":
            return jsonify({"success": True, "message": "Riders go straight to Minor Finals 2"}), 200
        
        # Update the semi-final seeding
        with engine.connect() as connection:
            for heat, heat_seeding in minor_final_1_structure_female.items():
                # Only continue if the current heat matches the submitted heat
                if heat == data['heatNumber']:
                    for index, seed in enumerate(heat_seeding):
                        rider_name = clean_rider_name(get_nth_selected_rider(data, index + 1))
                        if rider_name:
                            # Adjust the below SQL command according to your database structure and requirement
                            connection.execute(
                                text("UPDATE riders_female SET final_seeding = :seed, final_result = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )
                            connection.commit()  # Committing the transaction
                    break  # Exit loop once the matching heat is processed
                
            return jsonify({"success": True, "message": "Semi-final seeding updated successfully for quarter-final results"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

def semifinal_seeding_structure(total_riders):
    # Since all conditions return the same seeding structure, you can simply check if total_riders is within the expected range.
    if 6 <= total_riders <= 17:
        return {
            'Heat 1': [1, 4],
            'Heat 2': [2, 3]
        }
    else:
        return None  # or you might want to handle this differently if total_riders is not within the expected range

def semifinal_seeding_structure_female(total_riders):
    # Since all conditions return the same seeding structure, you can simply check if total_riders is within the expected range.
    if 6 <= total_riders <= 17:
        return {
            'Heat 1': [1, 4],
            'Heat 2': [2, 3]
        }
    else:
        return None  # or you might want to handle this differently if total_riders is not within the expected range

@app.route('/semifinal', methods=['GET', 'POST'])
def semifinal():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_male WHERE semi_final_seeding IS NOT NULL")
        ).fetchall()

        all_semi_final_pairings = {}

        for category in sprint_categories:
            riders_for_semi_finals = connection.execute(
                text("SELECT rider_name, semi_final_seeding FROM riders_male WHERE sprint_category = :sprint_category ORDER BY semi_final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_semi_finals)
            
            seeding_structure = semifinal_seeding_structure(total_riders)
            
            if seeding_structure:  # checking if seeding_structure is not None
                semi_final_heats = {}
                for heat, seeds in seeding_structure.items():
                    semi_final_heats[heat] = [rider[0] for rider in riders_for_semi_finals if rider[1] in seeds]

                all_semi_final_pairings[category[0]] = semi_final_heats
            else:
                # Handle the case where seeding_structure is None (or another unexpected value), perhaps logging a warning or an error
                pass  # or logging.warning(f"Seeding structure was unexpected for category {category[0]} with {total_riders} riders")

    return render_template('semifinal.html', semifinals=all_semi_final_pairings)

@app.route('/semifinal_female', methods=['GET', 'POST'])
def semifinal_female():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_female WHERE semi_final_seeding IS NOT NULL")
        ).fetchall()

        all_semi_final_pairings = {}

        for category in sprint_categories:
            riders_for_semi_finals = connection.execute(
                text("SELECT rider_name, semi_final_seeding FROM riders_female WHERE sprint_category = :sprint_category ORDER BY semi_final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_semi_finals)
            
            seeding_structure = semifinal_seeding_structure_female(total_riders)
            
            if seeding_structure:  # checking if seeding_structure is not None
                semi_final_heats = {}
                for heat, seeds in seeding_structure.items():
                    semi_final_heats[heat] = [rider[0] for rider in riders_for_semi_finals if rider[1] in seeds]

                all_semi_final_pairings[category[0]] = semi_final_heats
            else:
                # Handle the case where seeding_structure is None (or another unexpected value), perhaps logging a warning or an error
                pass  # or logging.warning(f"Seeding structure was unexpected for category {category[0]} with {total_riders} riders")

    return render_template('semifinal_female.html', semifinals=all_semi_final_pairings)

@app.route('/submit_semi_final', methods=['GET', 'POST'])
def submit_semi_final():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Fetch category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_male WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                
        # Based on the category and the number of riders, get the quarter-final seeding structure
        total_riders = get_riders_count_in_category(category)
        semi_final_structure = semifinal_seeding_structure(total_riders)
        
        # Update the semi-final seeding
        with engine.connect() as connection:
            for heat, heat_seeding in semi_final_structure.items():
                # Only continue if the current heat matches the submitted heat
                if heat == data['heatNumber']:
                    for index, seed in enumerate(heat_seeding):
                        rider_name = clean_rider_name(get_nth_selected_rider(data, index + 1))
                        if rider_name:
                            # Adjust the below SQL command according to your database structure and requirement
                            connection.execute(
                                text("UPDATE riders_male SET final_seeding = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )
                            connection.commit()  # Committing the transaction
                    break  # Exit loop once the matching heat is processed
                
            return jsonify({"success": True, "message": "Semi-final seeding updated successfully for Semi-Final results"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/submit_semi_final_female', methods=['GET', 'POST'])
def submit_semi_final_female():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Fetch category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_female WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                
        # Based on the category and the number of riders, get the quarter-final seeding structure
        total_riders = get_riders_count_in_category(category)
        semi_final_structure = semifinal_seeding_structure_female(total_riders)
        
        # Update the semi-final seeding
        with engine.connect() as connection:
            for heat, heat_seeding in semi_final_structure.items():
                # Only continue if the current heat matches the submitted heat
                if heat == data['heatNumber']:
                    for index, seed in enumerate(heat_seeding):
                        rider_name = clean_rider_name(get_nth_selected_rider(data, index + 1))
                        if rider_name:
                            # Adjust the below SQL command according to your database structure and requirement
                            connection.execute(
                                text("UPDATE riders_female SET final_seeding = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )
                            connection.commit()  # Committing the transaction
                    break  # Exit loop once the matching heat is processed
                
            return jsonify({"success": True, "message": "Semi-final seeding updated successfully for Semi-Final results"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

def minorfinal2_seeding_structure(total_riders):
    if total_riders == 6:
        return "Completed in Minor Final 1"

    elif total_riders == 7:
        return "Completed in Minor Final 1"

    elif total_riders == 8:
        return {
            'Heat 1': [7, 8],
            'Heat 2': [5, 6]
        }

    elif total_riders == 9:
        return {
            'Heat 1': [5, 6, 7, 8, 9]
        }

    elif total_riders == 10:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 11:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 12:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 13:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 14:
        return {
            'Heat 1': [5, 6, 7, 8]
        }
    
    elif total_riders == 15:
        return {
            'Heat 1': [5, 6, 7, 8, 9]
        }

    elif total_riders == 16:
        return {
            'Heat 1': [5, 6, 7, 8, 9]
        }

    elif total_riders == 17:
        return {
            'Heat 1': [5, 6, 7, 8, 9]
        }
    else:
        return None

def minorfinal2_seeding_structure_female(total_riders):
    if total_riders == 6:
        return "Completed in Minor Final 1"

    elif total_riders == 7:
        return "Completed in Minor Final 1"

    elif total_riders == 8:
        return {
            'Heat 1': [7, 8],
            'Heat 2': [5, 6]
        }

    elif total_riders == 9:
        return {
            'Heat 1': [5, 6, 7, 8, 9]
        }

    elif total_riders == 10:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 11:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 12:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 13:
        return {
            'Heat 1': [5, 6, 7, 8]
        }

    elif total_riders == 14:
        return {
            'Heat 1': [5, 6, 7, 8]
        }
    
    elif total_riders == 15:
        return {
            'Heat 1': [5, 6, 7, 8, 9]
        }

    elif total_riders == 16:
        return {
            'Heat 1': [5, 6, 7, 8, 9]
        }

    elif total_riders == 17:
        return {
            'Heat 1': [5, 6, 7, 8, 9]
        }
    else:
        return None

@app.route('/minorfinals2', methods=['GET', 'POST'])
def minorfinals2():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_male WHERE semi_final_seeding IS NOT NULL")
        ).fetchall()

        all_minor_final2_pairings = {}

        for category in sprint_categories:
            riders_for_minor_finals2 = connection.execute(
                text("SELECT rider_name, semi_final_seeding FROM riders_male WHERE sprint_category = :sprint_category ORDER BY semi_final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_minor_finals2)
            
            seeding_structure = minorfinal2_seeding_structure(total_riders)
            
            if isinstance(seeding_structure, dict):  # checking if seeding_structure is a dictionary
                minor_final2_heats = {}
                for heat, seeds in seeding_structure.items():
                    minor_final2_heats[heat] = [rider[0] for rider in riders_for_minor_finals2 if rider[1] in seeds]
                all_minor_final2_pairings[category[0]] = minor_final2_heats
            else:
                all_minor_final2_pairings[category[0]] = seeding_structure  # this will be a string or None
    
    return render_template('minorfinals2.html', minor_finals2=all_minor_final2_pairings)

@app.route('/minorfinals2_female', methods=['GET', 'POST'])
def minorfinals2_female():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_female WHERE semi_final_seeding IS NOT NULL")
        ).fetchall()

        all_minor_final2_pairings_female = {}

        for category in sprint_categories:
            riders_for_minor_finals2 = connection.execute(
                text("SELECT rider_name, semi_final_seeding FROM riders_female WHERE sprint_category = :sprint_category ORDER BY semi_final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_minor_finals2)
            
            seeding_structure_female = minorfinal2_seeding_structure_female(total_riders)
            
            if isinstance(seeding_structure_female, dict):  # checking if seeding_structure is a dictionary
                minor_final2_heats_female = {}
                for heat, seeds in seeding_structure_female.items():
                    minor_final2_heats_female[heat] = [rider[0] for rider in riders_for_minor_finals2 if rider[1] in seeds]
                all_minor_final2_pairings_female[category[0]] = minor_final2_heats_female
            else:
                all_minor_final2_pairings_female[category[0]] = seeding_structure  # this will be a string or None
    
    return render_template('minorfinals2_female.html', minor_finals2=all_minor_final2_pairings_female)

@app.route('/submitminorfinals2', methods=['POST'])
def submitminorfinals2():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Fetch category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_male WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                
        # Based on the category and the number of riders, get the quarter-final seeding structure
        total_riders = get_riders_count_in_category(category)
        minor_final_2_structure = minorfinal2_seeding_structure(total_riders)
        
        # Update the placing-final seeding
        with engine.connect() as connection:
            for heat, heat_seeding in minor_final_2_structure.items():
                # Only continue if the current heat matches the submitted heat
                if heat == data['heatNumber']:
                    for index, seed in enumerate(heat_seeding):
                        rider_name = clean_rider_name(get_nth_selected_rider(data, index + 1))
                        if rider_name:
                            # Adjust the below SQL command according to your database structure and requirement
                            connection.execute(
                                text("UPDATE riders_male SET final_seeding = :seed, final_result = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )
                            connection.commit()  # Committing the transaction
                    break  # Exit loop once the matching heat is processed
                
            return jsonify({"success": True, "message": "Semi-final seeding updated successfully for quarter-final results"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/submitminorfinals2_female', methods=['POST'])
def submitminorfinals2_female():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Fetch category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_female WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                
        # Based on the category and the number of riders, get the quarter-final seeding structure
        total_riders = get_riders_count_in_category(category)
        minor_final_2_structure_female = minorfinal2_seeding_structure_female(total_riders)
        
        # Update the placing-final seeding
        with engine.connect() as connection:
            for heat, heat_seeding in minor_final_2_structure_female.items():
                # Only continue if the current heat matches the submitted heat
                if heat == data['heatNumber']:
                    for index, seed in enumerate(heat_seeding):
                        rider_name = clean_rider_name(get_nth_selected_rider(data, index + 1))
                        if rider_name:
                            # Adjust the below SQL command according to your database structure and requirement
                            connection.execute(
                                text("UPDATE riders_female SET final_seeding = :seed, final_result = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )
                            connection.commit()  # Committing the transaction
                    break  # Exit loop once the matching heat is processed
                
            return jsonify({"success": True, "message": "Semi-final seeding updated successfully for quarter-final results"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

def final_seeding_structure(total_riders):
    # Since all conditions return the same seeding structure, you can simply check if total_riders is within the expected range.
    if 6 <= total_riders <= 17:
        return {
            'Minor Final': [3, 4],
            'Final': [1, 2]
        }
    else:
        return None  # or you might want to handle this differently if total_riders is not within the expected range

def final_seeding_structure_female(total_riders):
    # Since all conditions return the same seeding structure, you can simply check if total_riders is within the expected range.
    if 6 <= total_riders <= 17:
        return {
            'Minor Final': [3, 4],
            'Final': [1, 2]
        }
    else:
        return None  # or you might want to handle this differently if total_riders is not within the expected range

@app.route('/finals', methods=['GET', 'POST'])
def finals():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_male WHERE final_seeding IS NOT NULL")
        ).fetchall()

        all_final_pairings = {}

        for category in sprint_categories:
            riders_for_finals = connection.execute(
                text("SELECT rider_name, final_seeding FROM riders_male WHERE sprint_category = :sprint_category ORDER BY final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_finals)
            seeding_structure = final_seeding_structure(total_riders)
            
            if seeding_structure:  # checking if seeding_structure is not None
                final_heats = {}
                for index, (heat, seeds) in enumerate(seeding_structure.items()):
                    heat_name = "Final" if index == 1 else "Minor Final"  # Renaming based on index
                    final_heats[heat_name] = [rider[0] for rider in riders_for_finals if rider[1] in seeds]

                all_final_pairings[category[0]] = final_heats
                print(all_final_pairings)
            else:
                # Handle the case where seeding_structure is None (or another unexpected value), perhaps logging a warning or an error
                pass  # or logging.warning(f"Seeding structure was unexpected for category {category[0]} with {total_riders} riders")

    return render_template('finals.html', finals=all_final_pairings)

@app.route('/finals_female', methods=['GET', 'POST'])
def finals_female():
    with engine.connect() as connection:
        sprint_categories = connection.execute(
            text("SELECT DISTINCT sprint_category FROM riders_female WHERE final_seeding IS NOT NULL")
        ).fetchall()

        all_final_pairings = {}

        for category in sprint_categories:
            riders_for_finals_female = connection.execute(
                text("SELECT rider_name, final_seeding FROM riders_female WHERE sprint_category = :sprint_category ORDER BY final_seeding ASC"),
                {"sprint_category": category[0]}
            ).fetchall()
                
            total_riders = len(riders_for_finals_female)
            seeding_structure = final_seeding_structure_female(total_riders)
            
            if seeding_structure:  # checking if seeding_structure is not None
                final_heats = {}
                for index, (heat, seeds) in enumerate(seeding_structure.items()):
                    heat_name = "Final" if index == 1 else "Minor Final"  # Renaming based on index
                    final_heats[heat_name] = [rider[0] for rider in riders_for_finals_female if rider[1] in seeds]

                all_final_pairings[category[0]] = final_heats
                print(all_final_pairings)
            else:
                # Handle the case where seeding_structure is None (or another unexpected value), perhaps logging a warning or an error
                pass  # or logging.warning(f"Seeding structure was unexpected for category {category[0]} with {total_riders} riders")

    return render_template('finals.html', finals=all_final_pairings)

@app.route('/submit_final', methods=['GET', 'POST'])
def submit_final():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Fetch category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_male WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                
        # Based on the category and the number of riders, get the quarter-final seeding structure
        total_riders = get_riders_count_in_category(category)
        final_structure = final_seeding_structure(total_riders)
        
        # Update the Final seeding & result
        with engine.connect() as connection:
            for heat, heat_seeding in final_structure.items():
                # Only continue if the current heat matches the submitted heat
                if heat == data['heatNumber']:
                    for index, seed in enumerate(heat_seeding):
                        rider_name = clean_rider_name(get_nth_selected_rider(data, index + 1))
                        if rider_name:
                            # Adjust the below SQL command according to your database structure and requirement
                            connection.execute(
                                text("UPDATE riders_male SET final_seeding = :seed, final_result = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )
                            connection.commit()  # Committing the transaction
                    break  # Exit loop once the matching heat is processed
                
            return jsonify({"success": True, "message": "Final Placing updated successfully for Final results"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/submit_final_female', methods=['GET', 'POST'])
def submit_final_female():
    try:
        data = request.json
        app.logger.debug("Incoming data: %s", data)
        
        # Fetch category from data
        category = data.get('sprint_category')
        
        # If category not provided, fetch it using one of the selected riders
        if not category:
            selected_rider_name = clean_rider_name(data['selectedRider1'])
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT sprint_category FROM riders_female WHERE rider_name = :rider_name"),
                    {"rider_name": selected_rider_name}
                ).fetchone()
                
                category = result[0] if result else None
                if not category:
                    raise ValueError("Cannot determine the sprint category for the provided rider.")
                
        # Based on the category and the number of riders, get the quarter-final seeding structure
        total_riders = get_riders_count_in_category(category)
        final_structure = final_seeding_structure_female(total_riders)
        
        # Update the Final seeding & result
        with engine.connect() as connection:
            for heat, heat_seeding in final_structure.items():
                # Only continue if the current heat matches the submitted heat
                if heat == data['heatNumber']:
                    for index, seed in enumerate(heat_seeding):
                        rider_name = clean_rider_name(get_nth_selected_rider(data, index + 1))
                        if rider_name:
                            # Adjust the below SQL command according to your database structure and requirement
                            connection.execute(
                                text("UPDATE riders_female SET final_seeding = :seed, final_result = :seed WHERE rider_name = :rider_name"),
                                {"rider_name": rider_name, "seed": seed}
                            )
                            connection.commit()  # Committing the transaction
                    break  # Exit loop once the matching heat is processed
                
            return jsonify({"success": True, "message": "Final Placing updated successfully for Final results"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

from flask import render_template
from sqlalchemy import asc

@app.route('/final_results', methods=['GET'])
def final_results():
    try:
        # Create a session
        session = db_session()

        # Fetch and sort male riders' final results from the database
        riders_male_final = session.query(RidersMale)\
                                   .filter(RidersMale.final_result.isnot(None))\
                                   .order_by(RidersMale.sprint_category, RidersMale.final_result)\
                                   .all()

        # Close the session to release resources
        session.close()

        return render_template('final_results.html', riders_male_final=riders_male_final)

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/final_results_female', methods=['GET'])
def final_results_female():
    try:
        # Create a session
        session = db_session()

        # Fetch and sort female riders' final results from the database
        riders_female_final = session.query(RidersFemale)\
                                   .filter(RidersFemale.final_result.isnot(None))\
                                   .order_by(RidersFemale.sprint_category, RidersFemale.final_result)\
                                   .all()

        # Close the session to release resources
        session.close()

        return render_template('final_results.html', riders_female_final=riders_female_final)

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

# Import necessary modules and classes
from flask import render_template
from models import RidersMale  # Import your SQLAlchemy session and RidersMale model

# Placeholder function to determine the format of the Sprint Category (replace with actual logic)
def get_sprint_category_format(sprint_category):
    if sprint_category in ['Men\'s A Sprint', 'Men\'s B Sprint', 'Men\'s C Sprint', 'Men\'s D Sprint', 'Men\'s E Sprint']:
        return 6
    elif sprint_category in ['Women\'s A Sprint', 'Women\'s B Sprint', 'Women\'s C Sprint']:
        return 4
    else:
        return 0  # Default value if Sprint Category format is unknown



@app.route('/live')
def live():
    Session = sessionmaker(bind=engine)
    session = Session()

    riders = session.query(RidersMale).all()

    # Assign sprint categories
    sprint_categories = assign_sprint_categories(len(riders))

    pairings = generate_round1_pairings(riders, sprint_categories)

    global round1_heat_to_positions  # Declare as global
    if not round1_heat_to_positions:
        # Assuming you have a default category for round 1
        category = "default_category"  # Replace with your actual logic to determine category
        total_riders_in_category = get_riders_count_in_category(category)
        round1_heat_to_positions = get_round1_heat_to_positions(total_riders_in_category)

    return render_template('live.html', pairings=pairings, sprint_categories=sprint_categories)



if __name__ == '__main__':
    app.run(debug=True)