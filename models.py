from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class RidersMale(Base):
    __tablename__ = 'riders_male'

    rider_number = Column(Integer, primary_key=True)
    rider_name = Column(String(50))
    rider_club = Column(String(50))
    signed_on = Column(String(50), default='No')
    qualifying_time = Column(Numeric(precision=3, asdecimal=False), nullable=True)
    seeding = Column(Integer)
    sprint_category = Column(String(50))
    final_result = Column(Integer)

    def __init__(self, rider_number, rider_name, rider_club):
        self.rider_number = rider_number
        self.rider_name = rider_name
        self.rider_club = rider_club

class RidersFemale(Base):
    __tablename__ = 'riders_female'

    rider_number = Column(Integer, primary_key=True)
    rider_name = Column(String(50))
    rider_club = Column(String(50))
    signed_on = Column(String(50), default='No')
    qualifying_time = Column(Numeric(precision=3, asdecimal=False), nullable=True)
    seeding = Column(Integer)
    sprint_category = Column(String(50))
    final_result = Column(Integer)

    def __init__(self, rider_number, rider_name, rider_club):
        self.rider_number = rider_number
        self.rider_name = rider_name
        self.rider_club = rider_club
