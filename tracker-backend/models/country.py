from sqlalchemy import Column, Integer, String
from models.base import Base


class Country(Base):
    """
    Country model representing a country in the database by its name and ISO code.
    Attributes:
    - id: Primary key, unique identifier for each country.
    - name: The full name of the country.
    - iso_code: The three-letter ISO code representing the country, which is unique.
    """
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    iso_code = Column(String(3), nullable=False, unique=True)
    flag_url = Column(String(255), nullable=True)  # Optional URL to the country's flag image