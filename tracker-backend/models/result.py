from sqlalchemy import Column, Integer, ForeignKey, Float
from base import Base


class Result(Base):
    """
    Represents the result of a driver in a specific race, including their starting position, finishing position, best lap time, points earned, and status.
    Attributes:
    - race_id: Foreign key referencing the race in which the result was recorded
    - driver_id: Foreign key referencing the driver associated with the result
    - team_id: Foreign key referencing the team associated with the result
    - start_position: The starting position of the driver in the race
    - finish_position: The finishing position of the driver in the race (Nullable if the driver did not finish)
    - best_lap_time: The best lap time achieved by the driver during the race (Nullable if the driver did not finish)
    - points: The number of points earned by the driver for this result
    - status_id: Foreign key referencing the status of the result (e.g., finished, retired, disqualified)
    """
    __tablename__ = 'result'
    race_id = Column(Integer, ForeignKey('race.id'), primary_key=True)
    driver_id = Column(Integer, ForeignKey('driver.id'), primary_key=True)
    team_id = Column(Integer, ForeignKey('team.id'), primary_key=True)
    start_position = Column(Integer, nullable=False)
    finish_position = Column(Integer)
    best_lap_time = Column(Float)
    points = Column(Float, nullable=False)
    status_id = Column(Integer, ForeignKey('status.id'), nullable=False)

