from sqlalchemy import Column, Integer, String, Boolean
from models.base import Base


class Status(Base):
    """
    Represents the status of a race or a driver in the Formula 1 tracker database.
    Attributes:
    - id: Primary key, unique identifier for each status
    - label: A descriptive label for the status (e.g., "Scheduled", "Completed", "Retired", "Disqualified")
    - is_race_status: A boolean indicating whether this status is applicable to races
    - is_driver_status: A boolean indicating whether this status is applicable to drivers
    """
    __tablename__ = 'status'
    id = Column(Integer, primary_key=True)
    label = Column(String(20), nullable=False)
    is_race_status = Column(Boolean, nullable=False)
    is_driver_status = Column(Boolean, nullable=False)