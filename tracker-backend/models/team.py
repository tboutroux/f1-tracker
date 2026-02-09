from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from base import Base


class Team(Base):
    """
    Represents a Formula 1 team in the database, with attributes such as name, country, manager, and engine constructor details.
    Attributes:
    - id: Primary key, unique identifier for each team.
    - name: The name of the team.
    - country_id: Foreign key referencing the country where the team is based.
    - team_manager: The name of the team's manager.
    - is_engine_constructor: A boolean indicating whether the team is also an engine constructor.
    - engine_constructor: The name of the engine constructor if the team is not an engine constructor itself.
    - main_color: The main color associated with the team, typically used for branding and visual representation.
    - drivers: A relationship to the Driver model, allowing access to the drivers associated with the team
    """
    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    country_id = Column(Integer, ForeignKey('country.id'))
    team_manager = Column(String(100), nullable=False)
    is_engine_constructor = Column(Boolean, nullable=False)
    engine_constructor = Column(String(100), nullable=False)
    main_color = Column(String(7))
    drivers = relationship("Driver", back_populates="team")