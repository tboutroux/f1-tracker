from sqlalchemy import Column, Integer, DateTime, ForeignKey
from models.base import Base


class Race(Base):
    """
    Represents a Formula 1 race, including details such as the season, track, date, and practice/qualifying sessions.
    Attributes:
    - id: Primary key, unique identifier for each race
    - season_id: Foreign key referencing the season in which the race takes place
    - track_id: Foreign key referencing the track where the race is held
    - race_date: The date and time of the race
    - first_practice_date: The date and time of the first practice session
    - second_practice_date: The date and time of the second practice session
    - third_practice_date: The date and time of the third practice session (if applicable)
    - qualifying_date: The date and time of the qualifying session
    - round: The round number of the race within the season
    - status_id: Foreign key referencing the status of the race (e.g., scheduled, completed, cancelled)
    """
    __tablename__ = 'race'
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey('season.id'), nullable=False)
    track_id = Column(Integer, ForeignKey('track.id'), nullable=False)
    race_date = Column(DateTime, nullable=False)
    first_practice_date = Column(DateTime)
    second_practice_date = Column(DateTime)
    third_practice_date = Column(DateTime)
    qualifying_date = Column(DateTime)
    round = Column(Integer, nullable=False)
    status_id = Column(Integer, ForeignKey('status.id'), nullable=False)