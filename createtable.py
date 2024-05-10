from sqlalchemy import create_engine

engine = create_engine('sqlite:///riders.db')  # Replace with your database connection string

# Clear entries in male_riders_signedon table
delete_male_query = "DELETE FROM male_riders_signedon"
engine.execute(delete_male_query)

# Clear entries in female_riders_signedon table
delete_female_query = "DELETE FROM female_riders_signedon"
engine.execute(delete_female_query)
