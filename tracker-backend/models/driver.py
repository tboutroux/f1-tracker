from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class Driver(Base):
    """
    Driver model representing a Formula 1 driver in the database.
    Attributes:
    - id: Primary key, unique identifier for each driver.
    - team_id: Foreign key referencing the team the driver belongs to.
    - first_name: Driver's first name.
    - last_name: Driver's last name.
    - birth_date: Driver's date of birth.
    - birth_country: Foreign key referencing the country of birth.
    - grid_number: Driver's grid number for the season.
    - code_name: Driver's three-letter code name used in official standings and broadcasts.
    - team: Relationship to the Team model, allowing access to the driver's team information.
    """
    __tablename__ = 'driver'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    birth_date = Column(Date)
    birth_country = Column(Integer, ForeignKey('country.id'))
    code_name = Column(String(3))