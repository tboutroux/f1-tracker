from sqlalchemy import Column, Integer, ForeignKey
from models.base import Base


class Standing(Base):
    """
    Represents the standings of drivers and teams in a given season.
    Each entry corresponds to a driver or team and their points and position in the championship.
    Attributes:
    - id: Primary key, unique identifier for each standing entry.
    - season_id: Foreign key referencing the season for which the standing is recorded.
    - driver_id: Foreign key referencing the driver associated with the standing (nullable for team standings).
    - team_id: Foreign key referencing the team associated with the standing (nullable for driver standings).
    - points: The total points accumulated by the driver or team in the season.
    - position: The current position of the driver or team in the championship standings.
    - victories: The number of victories achieved by the driver or team in the season.
    - podiums: The number of podium finishes achieved by the driver or team in the season.
    """
    __tablename__ = 'standing'
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey('season.id'), nullable=False)
    driver_id = Column(Integer, ForeignKey('driver.id'))
    team_id = Column(Integer, ForeignKey('team.id'))
    points = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    victories = Column(Integer, nullable=False)
    podiums = Column(Integer, nullable=False)