import requests
import fastf1
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.driver import Driver
from models.team import Team
from models.country import Country
from dotenv import load_dotenv
import time
import os


# Initialize session management
def get_session():
    load_dotenv()
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    return Session()


def get_country_id(session, country_name):
    country = session.query(Country).filter_by(male_demonym=country_name).first()
    if country:
        return country.id
    return None


def get_driver_team_id(session, team_name):
    team = session.query(Team).filter_by(name=team_name).first()
    if team:
        return team.id
    return None


def load_drivers(session):
    
    try:
        offset = 0
        all_drivers = []
        
        while True:
            print(f"📡 Récupération des pilotes avec offset {offset}...")

            time.sleep(3) # Be polite to the API and avoid hitting rate limits
            
            url = f"https://api.jolpi.ca/ergast/f1/drivers?format=json&offset={offset}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()['MRData']
            drivers_data = data['DriverTable']['Drivers']
            
            if not drivers_data:
                break
                
            all_drivers.extend(drivers_data)
            offset += 30
        
        print(f"✅ {len(all_drivers)} pilotes récupérés. Début de l'insertion...")
        
        for driver_info in all_drivers:
            code_name = driver_info.get('code')
            number = driver_info.get('permanentNumber')
            first_name = driver_info['givenName']
            last_name = driver_info['familyName']
            date_of_birth = driver_info['dateOfBirth'] if driver_info.get('dateOfBirth') else None

            nationality = driver_info['nationality'] if driver_info.get('nationality') else None
            
            # Retrieve the country ID from the database
            country_id = get_country_id(session, nationality)

            existing_driver = session.query(Driver).filter_by(first_name=first_name, last_name=last_name, code_name=code_name).first()

            if existing_driver:
                print(f"⚠️ Pilote {first_name} {last_name} ({code_name}) existe déjà en base de données. Ignoré.")
                continue

            new_driver = Driver(
                first_name=first_name,
                last_name=last_name,
                birth_date=date_of_birth,
                birth_country=country_id,
                code_name=code_name,
            )
            session.add(new_driver)
        session.commit()
        print("✅ Insertion des pilotes terminée.")
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de l'insertion des pilotes : {e}")


if __name__ == "__main__":
    session = get_session()
    load_drivers(session)