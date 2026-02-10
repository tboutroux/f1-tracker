import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.track import Track
from models.country import Country
from dotenv import load_dotenv
import time
import os
import json # Import json for geojson_data and corners
import fastf1 as ff1 # Changed import statement
from datetime import datetime


# Initialize FastF1 caching
# Using an environment variable for the cache directory, defaulting to /tmp/fastf1_cache
ff1.Cache.enable_cache(os.getenv("FASTF1_CACHE_DIR", "/tmp/fastf1_cache"))

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

def normalize_grand_prix_name(name):
    # Basic normalization for FastF1, which expects specific names
    name_map = {
        "Circuit de Monaco": "Monaco Grand Prix",
        "Circuit de Spa-Francorchamps": "Belgian Grand Prix",
        "Autodromo Nazionale di Monza": "Italian Grand Prix",
        "Silverstone Circuit": "British Grand Prix",
        "Hungaroring": "Hungarian Grand Prix",
        "Circuit Gilles Villeneuve": "Canadian Grand Prix",
        "Red Bull Ring": "Austrian Grand Prix",
        "Circuit de Barcelona-Catalunya": "Spanish Grand Prix",
        "Baku City Circuit": "Azerbaijan Grand Prix",
        "Miami International Autodrome": "Miami Grand Prix",
        "Jeddah Corniche Circuit": "Saudi Arabian Grand Prix",
        "Bahrain International Circuit": "Bahrain Grand Prix",
        "Albert Park Circuit": "Australian Grand Prix",
        "Suzuka Circuit": "Japanese Grand Prix",
        "Shanghai International Circuit": "Chinese Grand Prix",
        "Circuit of the Americas": "United States Grand Prix",
        "Autódromo Hermanos Rodríguez": "Mexico City Grand Prix",
        "Interlagos": "Sao Paulo Grand Prix",
        "Yas Marina Circuit": "Abu Dhabi Grand Prix",
        "Las Vegas Strip Circuit": "Las Vegas Grand Prix",
        "Losail International Circuit": "Qatar Grand Prix",
        "Hockenheimring": "German Grand Prix", # Example for older tracks
        "Nürburgring": "Eifel Grand Prix", # Example for older tracks (specific event name)
        "Istanbul Park": "Turkish Grand Prix",
        "Portimão Circuit": "Portuguese Grand Prix",
        "Mugello Circuit": "Tuscan Grand Prix",
        # Add more mappings as needed
    }
    # Check if the name is in the map, otherwise try to append "Grand Prix"
    return name_map.get(name, f"{name.replace(' Circuit', '')} Grand Prix" if "Circuit" in name else f"{name} Grand Prix")


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
        
        # Use a recent year for FastF1 data retrieval, as circuit layouts don't change drastically every year
        # We can try a few recent years if one fails, or pick a fixed one for consistency
        reference_year = 2023 # Using a fixed recent year

        for circuit_info in all_circuits:
            circuit_id = circuit_info['circuitId']
            name = circuit_info['circuitName']
            city = circuit_info['Location']['locality']
            country_name = circuit_info['Location']['country']
            country_id = get_country_id(session, country_name)

            turns_number = 0
            best_lap = 0.0
            best_lap_driver = -1 
            geojson_data = {} 
            corners_data = {} # Renamed to avoid conflict with `circuit_info.corners` DataFrame

            # Use FastF1 to attempt to get more detailed track information like turns number, and corners
            try:
                grand_prix_name = normalize_grand_prix_name(name)
                print(f"DEBUG: Normalized Grand Prix Name for '{name}': '{grand_prix_name}'")
                
                # Attempt to get a session for the reference year. If it fails, try previous years.
                _session = None
                for year_offset in range(3): # Try current year and 2 previous years
                    try_year = reference_year - year_offset
                    print(f"DEBUG: Attempting to get FastF1 session for {grand_prix_name} ({try_year})...")
                    try:
                        _session = ff1.get_session(try_year, grand_prix_name, 'R')
                        print(f"DEBUG: FastF1 session object obtained for {grand_prix_name} ({try_year}): {_session}")
                        _session.load(laps=False, telemetry=False, weather=False, messages=False, livedata=False)
                        print(f"DEBUG: Session loaded successfully for {grand_prix_name} ({try_year}).")
                        break
                    except Exception as fastf1_session_e:
                        print(f"DEBUG: Failed to get/load FastF1 session for {grand_prix_name} ({try_year}): {fastf1_session_e}")
                        _session = None # Ensure _session is None if an exception occurred

                if _session:
                    circuit_details = _session.get_circuit_info()
                    print(f"DEBUG: Circuit details from FastF1: {circuit_details}")
                    if circuit_details is not None:
                        # turns_number: number of corners
                        turns_number = len(circuit_details.corners)
                        print(f"DEBUG: Turns number found: {turns_number}")
                        
                        # corners: convert DataFrame to dict for storage
                        # Each corner has 'Number', 'X', 'Y'
                        print(f"DEBUG: Raw corners DataFrame: \n{circuit_details.corners[['Number', 'X', 'Y']]}")
                        corners_data = circuit_details.corners[['Number', 'X', 'Y']].set_index('Number').transpose().to_dict('dict')
                        print(f"DEBUG: Processed corners data: {corners_data}")

                        # GeoJSON data is not directly available from circuit_info in this format
                        # Best lap data is also session-specific, not track-specific global record
                        # Keeping defaults for these as FastF1 does not provide them easily at track level
                        # The 'best_lap' and 'best_lap_driver' from the old Circuit object were likely
                        # tied to a specific session's fastest lap, not a global track record.
                        # For now, we keep them as default values until a clear source is identified.
                    else:
                        print(f"⚠️ FastF1 {grand_prix_name} ({try_year}).")
                else:
                    print(f"⚠️ FastF1 {grand_prix_name}")

            except Exception as e:
                print(f"⚠️ FastF1'{name}': {e}")
                # Defaults are already set above, so no need to reset them here unless we want different defaults on error.

            if not country_id:
                print(f"❌ {country_name} {name}")
                continue

            existing_track = session.query(Track).filter_by(name=name, city=city, country_id=country_id).first()

            if existing_track:
                print(f"⚠️ 電路'{name}'在'{city},{country_name}'已經存在。跳過。")
                continue

            new_track = Track(
                name=name,
                city=city,
                country_id=country_id,
                turns_number=turns_number,
                best_lap=best_lap,
                best_lap_driver=best_lap_driver,
                geojson_data=geojson_data, # Will be empty dict if not found
                corners=corners_data, # Will be empty dict if not found
            )
            session.add(new_track)
        session.commit()
        print("✅ 電路插入完成。")
    except Exception as e:
        session.rollback()
        print(f"❌ 電路插入時發生錯誤: {e}")


if __name__ == "__main__":
    session = get_session()
    load_tracks(session)