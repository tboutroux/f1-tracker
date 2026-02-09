from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime
from base import Base


class Pitstop(Base):
    """
    Pitstop model representing a pit stop made by a driver during a race.
    Attributes:
    - id: Primary key for the pit stop
    - race_id: Foreign key referencing the race during which the pit stop occurred
    - driver_id: Foreign key referencing the driver who made the pit stop
    - lap: The lap number during which the pit stop was made
    - stop: The sequential number of the pit stop for the driver in the race
    - stop_time: The timestamp when the pit stop occurred
    - duration: The duration of the pit stop in seconds
    """
    __tablename__ = 'pitstop'
    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey('race.id'), nullable=False)
    driver_id = Column(Integer, ForeignKey('driver.id'), nullable=False)
    lap = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)  # Pit stop number in the race
    stop_time = Column(DateTime, nullable=False)  # Timestamp of the pit stop
    duration = Column(Float, nullable=False)  # Time in seconds spent in the pit