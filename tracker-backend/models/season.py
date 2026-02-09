from sqlalchemy import Column, Integer, String
from base import Base


class Season(Base):
    """
    Season model representing a Formula 1 season in the database by its year.
    Attributes:
    - id: Primary key, unique identifier for each season.
    - year: The year of the Formula 1 season, which is unique.
    """
    __tablename__ = 'season'
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)