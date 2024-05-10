# Import required modules
import csv
import sqlite3

# Connecting to the geeks database
connection = sqlite3.connect('male_male_riders.db')

# Creating a cursor object to execute
# SQL queries on a database table
cursor = connection.cursor()

# Table Definition
create_table = '''CREATE TABLE IF NOT EXISTS riders(
				rider_number INTEGER,
				rider_name TEXT,
				rider_club TEXT,
				signed_on TEXT);
				'''

# Creating the table into our
# database
cursor.execute(create_table)

# Opening the rider-records.csv file
file = open(r'C:\Users\james\OneDrive\Documents\Black Line App 2.0\website\riderinfo.csv')

# Reading the contents of the
# rider-records.csv file
contents = csv.reader(file)

# SQL query to insert data into the
# rider table
insert_records = "INSERT INTO riders (rider_number, rider_name, rider_club, signed_on) VALUES(?, ?, ?, ?)"

# Importing the contents of the file
# into our rider table
cursor.executemany(insert_records, contents)

# SQL query to retrieve all data from
# the rider table To verify that the
# data of the csv file has been successfully
# inserted into the table
select_all = "SELECT * FROM riders"
rows = cursor.execute(select_all).fetchall()

# Output to the console screen
for r in rows:
	print(r)

# Committing the changes
connection.commit()

# closing the database connection
connection.close()

