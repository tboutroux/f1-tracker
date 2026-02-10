from sqlalchemy import Column, Integer, String
from models.base import Base


class Country(Base):
    """
    Country model representing a country in the database by its name and ISO code.
    Attributes:
    - id: Primary key, unique identifier for each country.
    - name: The full name of the country.
    - iso_code: The three-letter ISO code representing the country, which is unique.
    - flag_url: Optional URL to the country's flag image.
    - timezone: Optional timezone information.
    - alt_spellings: Optional alternative spellings of the country name.
    - female_demonym: Optional female demonym in English.
    - male_demonym: Optional male demonym in English.
    """
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    iso_code = Column(String(3), nullable=False, unique=True)
    flag_url = Column(String(255), nullable=True)  # Optional URL to the country's flag image
    timezone = Column(String(50), nullable=True)  # Optional timezone information
    alt_spellings = Column(String(500), nullable=True)  # Optional alternative spellings of the country name
    female_demonym = Column(String(100), nullable=True)  # Optional
    male_demonym = Column(String(100), nullable=True)  # Optional