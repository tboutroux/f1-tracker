from sqlalchemy import Column, Integer, String, ForeignKey, Float, JSON
from models.base import Base


class Track(Base):
    """
    Track model representing a Formula 1 track in the database.
    Attributes:
    - id: Primary key, unique identifier for each track.
    - name: The name of the track.
    - city: The city where the track is located.
    - country_id: Foreign key referencing the country where the track is located.
    - turns_number: The number of turns in the track.
    - best_lap: The best lap time recorded on the track.
    - best_lap_driver: The driver who holds the record for the best lap time on the track.
    - timezone: The timezone of the track location.
    - geojson_data: The GeoJSON data representing the track layout and location.
    - corners: The JSON data representing the corners of the track, including their names and locations.
    """
    __tablename__ = 'track'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    city = Column(String(50), nullable=False)
    country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    turns_number = Column(Integer, nullable=False)
    best_lap = Column(Float, nullable=False)
    best_lap_driver = Column(Integer, nullable=False)
    geojson_data = Column(JSON, nullable=False)
    corners = Column(JSON, nullable=False)