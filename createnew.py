import csv
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

# Function to create the SQLite database from the uploaded CSV file
def create_database(csv_file):
    conn = sqlite3.connect('riders.db')
    cursor = conn.cursor()

    # Drop the existing table if it exists
    cursor.execute('DROP TABLE IF EXISTS riders')

    # Create table with specified columns and types
    cursor.execute('''CREATE TABLE riders
                      (rider_number INTEGER, rider_name TEXT, rider_club TEXT, signed_on TEXT)''')

    # Read the CSV file and insert data into the database
    with open(csv_file, 'r') as file:
        csv_data = csv.reader(file)
        next(csv_data)  # Skip header row
        cursor.executemany('INSERT INTO riders VALUES (?,?,?,?)', csv_data)

    conn.commit()
    conn.close()

# Define the Flask route for the signon page
@app.route('/signon', methods=['GET', 'POST'])
def display_table():
    if request.method == 'POST':
        # Get the updated data from the form
        updated_data = request.form.getlist('data[]')

        conn = sqlite3.connect('riders.db')
        cursor = conn.cursor()

        # Update the database with the modified data
        for data in updated_data:
            rider_number, rider_name, rider_club, signed_on = data.split(',')
            cursor.execute('''UPDATE riders SET rider_name=?, rider_club=?, signed_on=?
                              WHERE rider_number=?''', (rider_name, rider_club, signed_on, rider_number))

        conn.commit()
        conn.close()

    # Fetch data from the database
    conn = sqlite3.connect('riders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM riders')
    data = cursor.fetchall()
    conn.close()

    return render_template('signon.html', data=data)

if __name__ == '__main__':
    csv_file = (r'C:\Users\james\OneDrive\Documents\Black Line App 2.0\website\riderinfo.csv')  # Replace with your uploaded CSV file
    create_database(csv_file)
    app.run()
