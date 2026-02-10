import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.season import Season
from dotenv import load_dotenv
import os


# Initialize session management
def get_session():
    load_dotenv()
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    return Session()


def insert_status(session: sessionmaker, status_label: str, status_type: str = "race" | "driver"):
    """
    Inserts a new race status into the database if it does not already exist.
    Args:
        session: SQLAlchemy session object
        status_label: The label for the race status (e.g., "Scheduled", "Completed")
        status_type: The type of status (e.g., "race" or "driver")
    """
    existing_status = session.query(Season).filter_by(label=status_label).first()
    if existing_status:
        print(f"Status '{status_label}' already exists in the database.")
        return
    
    new_status = Season(label=status_label, is_race_status=True, is_driver_status=False)
    session.add(new_status)
    session.commit()
    print(f"Inserted new race status: '{status_label}' into the database.")


if __name__ == "__main__":
    session = get_session()

    insert_status(session, "Retired", "driver")
    insert_status(session, "Lapped", "driver")
    insert_status(session, "Finished", "driver")

    insert_status(session, "Scheduled", "race")
    insert_status(session, "Completed", "race")
    insert_status(session, "Cancelled", "race")