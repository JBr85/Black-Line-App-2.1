from flask import Flask, request
from werkzeug.utils import secure_filename
import pandas as pd
from sqlalchemy import create_engine

app = Flask(__name__)
engine = create_engine('sqlite:///riders.db')  # Create a SQLAlchemy engine. Change connection string as needed.

@app.route('/upload', methods=['POST'])
def upload_files():
    male_file = request.files['male_csv']
    female_file = request.files['female_csv']

    if male_file and female_file:
        male_df = pd.read_csv(male_file)
        female_df = pd.read_csv(female_file)

        # Assuming 'riders_male' and 'riders_female' are the names of your tables.
        male_df.to_sql('riders_male', engine, if_exists='replace')
        female_df.to_sql('riders_female', engine, if_exists='replace')

        return 'Files successfully uploaded and stored in database'
    else:
        return 'Missing files'
