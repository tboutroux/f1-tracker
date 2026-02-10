import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.track import Track
from models.country import Country
from dotenv import load_dotenv
import time
import os
import json # Import json for geojson_data and corners


# Initialize session management
def get_session():
    load_dotenv()
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    return Session()


def get_country_id(session, country_name):
    # Jolpi API for circuits gives country name, so we will use the 'name' field for lookup
    country = session.query(Country).filter(
        (Country.name == country_name) | 
        (Country.alt_spellings.contains(country_name))
    ).first()
    if country:
        return country.id
    return None


def load_tracks(session):
    try:
        offset = 0
        all_circuits = []
        
        while True:
            print(f"📡 Récupération des circuits avec offset {offset}...")
            time.sleep(3) # Be polite to the API and avoid hitting rate limits
            url = f"https://api.jolpi.ca/ergast/f1/circuits?format=json&offset={offset}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()['MRData']
            circuits_data = data['CircuitTable']['Circuits']
            
            if not circuits_data:
                break
                
            all_circuits.extend(circuits_data)
            offset += 30

        print(f"✅ {len(all_circuits)} circuits récupérés. Début de l'insertion...")
        
        for circuit_info in all_circuits:
            circuit_id = circuit_info['circuitId']
            name = circuit_info['circuitName']
            city = circuit_info['Location']['locality']
            country_name = circuit_info['Location']['country']
            # lat = float(circuit_info['Location']['lat'])
            # long = float(circuit_info['Location']['long'])

            country_id = get_country_id(session, country_name)

            if not country_id:
                print(f"❌ Pays '{country_name}' non trouvé pour le circuit '{name}'. Le circuit sera ignoré.")
                continue

            existing_track = session.query(Track).filter_by(name=name, city=city, country_id=country_id).first()

            if existing_track:
                print(f"⚠️ Circuit '{name}' à '{city}, {country_name}' existe déjà. Ignoré.")
                continue

            # Placeholder values for fields not available in the API or requiring external processing
            # These will need to be updated by a separate process or manual entry
            turns_number = 0 
            best_lap = 0.0
            best_lap_driver = -1 # Assuming -1 means 'not set' or 'unknown driver ID'
            timezone = "Unknown/Unknown" # Can be determined using lat/long with external library
            geojson_data = {} # Requires detailed track layout data
            corners = {} # Requires detailed corner information

            new_track = Track(
                name=name,
                city=city,
                country_id=country_id,
                turns_number=turns_number,
                best_lap=best_lap,
                best_lap_driver=best_lap_driver,
                timezone=timezone,
                geojson_data=geojson_data,
                corners=corners,
            )
            session.add(new_track)
        session.commit()
        print("✅ Insertion des circuits terminée.")
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de l'insertion des circuits : {e}")


if __name__ == "__main__":
    session = get_session()
    load_tracks(session)