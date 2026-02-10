import requests
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
    print("🚗 Récupération des pilotes via Ergast API...")
    
    try:
        offset = 0
        all_drivers = []
        
        while True:
            time.sleep(1) # Be polite to the API and avoid hitting rate limits
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
            driver_code = driver_info.get('code')
            number = driver_info.get('permanentNumber')
            given_name = driver_info['givenName']
            family_name = driver_info['familyName']
            date_of_birth = driver_info['dateOfBirth']

            nationality = driver_info['nationality']
            
            # Retrieve the country ID from the database
            country_id = get_country_id(session, nationality)

            # Retrieve the team ID from the database using FastF1 matching logic (if available)
            team_name = driver_info.get('team')
            team_id = get_driver_team_id(session, team_name) if team_name else None

            existing_driver = session.query(Driver).filter_by(driver_code=driver_code).first()

            if existing_driver:
                print(f"⚠️ Pilote {given_name} {family_name} ({driver_code}) existe déjà en base de données. Ignoré.")
                continue

            new_driver = Driver(
                given_name=given_name,
                family_name=family_name,
                date_of_birth=date_of_birth,
                birth_country=country_id,
                team_id=team_id,
                driver_code=driver_code,
                number=number,
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