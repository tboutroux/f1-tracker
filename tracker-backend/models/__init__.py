# Importe l'objet Base commun
from .base import Base 

# Importe explicitement chaque modèle pour qu'ils s'enregistrent dans Base.metadata
from .country import Country
from .track import Track
from .team import Team
from .driver import Driver
from .race import Race
from .status import Status
from .season import Season
from .result import Result
from .pitstop import Pitstop
from .standing import Standing

# On exporte Base pour qu'il soit accessible facilement
__all__ = ["Base"]