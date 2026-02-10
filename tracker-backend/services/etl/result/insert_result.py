import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import fastf1
from fastf1 import plotting

from models.base import Base
from models.country import Country
from models.driver import Driver
from models.team import Team
from models.status import Status
from models.race import Race
from models.season import Season
from models.track import Track
from models.result import Result

from services.etl.season.insert_season import insert_season
from services.etl.country.insert_country import insert_country


# Load environment variables once at the top
load_dotenv()

# Configure fastf1 cache
fastf1.Cache.enable_cache(os.getenv("FASTF1_CACHE_DIR", "/tmp/fastf1_cache"))


def fetch_and_seed_race_data(year: int, session):

    print(f"🏎️ Récupération des données de course pour l'année {year} via Ergast API...")

    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/results?limit=1000.json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()['MRData']
        
        if int(data['total']) == 0:
            print(f"⚠️ Aucune donnée de course trouvée pour l'année {year}.")
            return

        races_data = data['RaceTable']['Races']

        print(f"✅ {len(races_data)} courses trouvées pour l'année {year}. Début de l'insertion...")

        for race_info in races_data:
            # --- Insert or get Season ---
            season_year = int(race_info['season'])
            season = session.query(Season).filter_by(year=season_year).first()
            if not season:
                insert_season(session, season_year)
                season = session.query(Season).filter_by(year=season_year).first()

            # --- Insert or get Country for Track ---
            track_country_name = race_info['Circuit']['Location']['country']
            track_country = session.query(Country).filter_by(name=track_country_name).first()
            if not track_country:
                track_country = session.query(Country).filter(Country.alt_spellings.contains(track_country_name)).first()
                
                if not track_country:
                    insert_country(session=session, name=track_country_name, iso_code=track_country_name[:3].upper())
                    track_country = session.query(Country).filter_by(name=track_country_name).first()

            # --- Load fastf1 session for team colors and circuit info ---
            f1_session = None # Initialize f1_session to None for each race
            try:
                race_round_number = int(race_info['round']) if race_info['round'] else None
                if race_round_number is not None:
                    # Ergast API 'type' field is not directly available here, so assuming all are main races
                    f1_session = fastf1.get_session(year=year, gp=race_round_number)
                    f1_session.load(telemetry=False, weather=False, messages=False, laps=False, weather_data=False, circuit_info=True)
                    # Ensure the plotting backend is set up
                    plotting.setup_mpl()
            except Exception as e:
                print(f"⚠️ Could not load fastf1 session for {year} Round {race_round_number}: {e}")
                # f1_session remains None, continue without fastf1 data
            
            # --- Insert or get Track ---
            track_name = race_info['Circuit']['circuitName']
            
            # --- Extract track details from fastf1 session if available ---
            track_city_ergast = race_info['Circuit']['Location']['locality'] # From Ergast API

            city = track_city_ergast
            turns_number = 0
            best_lap = 0.0 # Not directly available in fastf1 circuit_info
            best_lap_driver = 0 # Not directly available in fastf1 circuit_info
            timezone = None
            geojson_data = None
            corners_data = []

            if f1_session is not None and hasattr(f1_session, 'circuit_info') and f1_session.circuit_info is not None:
                fastf1_circuit_info = f1_session.circuit_info
                
                if 'Location' in fastf1_circuit_info and not fastf1_circuit_info.Location.empty:
                    if len(fastf1_circuit_info.Location) > 1:
                        timezone = fastf1_circuit_info.Location.iloc[1]

                if 'TotalCorners' in fastf1_circuit_info and not fastf1_circuit_info.TotalCorners.empty:
                    turns_number = int(fastf1_circuit_info.TotalCorners.iloc[0])
                
                if hasattr(fastf1_circuit_info, 'geojson') and fastf1_circuit_info.geojson is not None:
                    geojson_data = fastf1_circuit_info.geojson.to_json() # Convert GeoDataFrame to JSON string
                
                if hasattr(fastf1_circuit_info, 'corners') and fastf1_circuit_info.corners is not None and not fastf1_circuit_info.corners.empty:
                    corners_data = fastf1_circuit_info.corners.to_dict('records') # Convert DataFrame to list of dicts

            track_exists = session.query(Track).filter_by(name=track_name).first()
            if not track_exists:
                track_exists = Track(
                    name=track_name,
                    country_id=track_country.id,
                    city=city,
                    turns_number=turns_number,
                    best_lap=best_lap, # Placeholder
                    best_lap_driver=best_lap_driver, # Placeholder
                    timezone=timezone,
                    geojson_data=geojson_data,
                    corners=corners_data
                )
                session.add(track_exists)
                session.flush()
            else:
                # Update existing track with new data
                track_exists.city = city
                track_exists.turns_number = turns_number
                track_exists.best_lap = best_lap # Placeholder
                track_exists.best_lap_driver = best_lap_driver # Placeholder
                track_exists.timezone = timezone
                track_exists.geojson_data = geojson_data
                track_exists.corners = corners_data

            # --- Insert or get Race Status (Placeholder - assuming 'Completed' for fetched results) ---
            race_status_label = "Completed" # API results are for completed races
            race_status = session.query(Status).filter_by(label=race_status_label, is_race_status=True).first()
            if not race_status:
                race_status = Status(label=race_status_label, is_race_status=True, is_driver_status=False)
                session.add(race_status)
                session.flush()

            # --- Insert or get Race ---
            race_date_str = race_info['date']
            race_time_str = race_info.get('time', '00:00:00Z') # Default to midnight if time is missing
            race_datetime = datetime.fromisoformat(f"{race_date_str}T{race_time_str.replace('Z', '')}")

            race = session.query(Race).filter_by(id=race_info['round']).first()
            if not race:
                race = Race(
                    id=race_info['round'], # Using round as ID for now, adjust if primary key is auto-increment
                    season_id=season.id,
                    track_id=track_exists.id,
                    race_date=race_datetime,
                    first_practice_date=None, # Not available in this API endpoint
                    second_practice_date=None,
                    third_practice_date=None,
                    qualifying_date=None,
                    round=int(race_info['round']),
                    status_id=race_status.id
                )
                session.add(race)
                session.flush()
            else:
                # Update existing race if necessary
                race.season_id = season.id
                race.track_id = track_exists.id
                race.race_date = race_datetime
                race.status_id = race_status.id

            for result_info in race_info['Results']:
                # --- Insert or get Team (Constructor) ---
                team_name = result_info['Constructor']['name']
                team = session.query(Team).filter_by(name=team_name).first()
                
                team_main_color = "#FFFFFF" # Default color
                if f1_session:
                    try:
                        team_main_color = plotting.team_color(team_name)
                    except Exception as e:
                        print(f"⚠️ Could not get team color for {team_name}: {e}")

                if not team:
                    # Constructor country is not directly in the API for constructor, so using a placeholder or default
                    # In a real scenario, you might need another API call or a mapping
                    team_country = session.query(Country).filter_by(name="Unknown").first() # Placeholder
                    if not team_country:
                        team_country = Country(name="Unknown", iso_code="UNK", flag_url=None)
                        session.add(team_country)
                        session.flush()

                    team = Team(
                        name=team_name,
                        country_id=team_country.id, # Placeholder
                        team_manager="Unknown", # Not in API
                        is_engine_constructor=False, # Not in API
                        engine_constructor=team_name, # Assuming constructor is also engine constructor for simplicity
                        main_color=team_main_color
                    )
                    session.add(team)
                    session.flush()
                else:
                    # Update existing team's color if it's still default or different
                    if team.main_color == "#FFFFFF" or team.main_color != team_main_color: 
                        team.main_color = team_main_color

                # --- Get Driver Country ---
                driver_country_name = result_info['Driver']['nationality']
                driver_country = session.query(Country).filter_by(female_demonym=driver_country_name).first()

                # --- Insert or get Driver ---
                driver_code = result_info['Driver'].get('code')
                driver_permanent_number = result_info['Driver'].get('permanentNumber')
                driver_birthdate_str = result_info['Driver'].get('dateOfBirth')
                driver_birthdate = datetime.strptime(driver_birthdate_str, '%Y-%m-%d').date() if driver_birthdate_str else None

                driver = session.query(Driver).filter_by(
                    first_name=result_info['Driver']['givenName'],
                    last_name=result_info['Driver']['familyName']
                ).first()

                if not driver:
                    driver = Driver(
                        team_id=team.id,
                        first_name=result_info['Driver']['givenName'],
                        last_name=result_info['Driver']['familyName'],
                        birth_date=driver_birthdate,
                        birth_country=driver_country.id,
                        grid_number=int(driver_permanent_number) if driver_permanent_number else 0, # Default to 0 if not available
                        code_name=driver_code
                    )
                    session.add(driver)
                    session.flush()
                else:
                    # Update driver's team if it has changed (e.g., driver moved teams)
                    driver.team_id = team.id
                    driver.grid_number = int(driver_permanent_number) if driver_permanent_number else driver.grid_number
                    driver.code_name = driver_code

                # --- Insert or get Driver Status (Result Status) ---
                driver_status_label = result_info['Status']
                driver_status = session.query(Status).filter_by(label=driver_status_label, is_driver_status=True).first()
                if not driver_status:
                    driver_status = Status(label=driver_status_label, is_driver_status=True, is_race_status=False)
                    session.add(driver_status)
                    session.flush()

                # --- Insert or update Result ---
                best_lap_time_str = result_info.get('FastestLap', {}).get('Time', {}).get('time')
                best_lap_time_float = None
                if best_lap_time_str:
                    try:
                        minutes, seconds = map(float, best_lap_time_str.split(':'))
                        best_lap_time_float = minutes * 60 + seconds
                    except ValueError:
                        best_lap_time_float = None

                result = session.query(Result).filter_by(
                    race_id=race.id,
                    driver_id=driver.id,
                    team_id=team.id
                ).first()

                if not result:
                    result = Result(
                        race_id=race.id,
                        driver_id=driver.id,
                        team_id=team.id,
                        start_position=int(result_info['grid']),
                        finish_position=int(result_info['position']) if result_info['position'].isdigit() else None,
                        best_lap_time=best_lap_time_float,
                        points=float(result_info['points']),
                        status_id=driver_status.id
                    )
                    session.add(result)
                else:
                    # Update existing result
                    result.start_position = int(result_info['grid'])
                    result.finish_position = int(result_info['position']) if result_info['position'].isdigit() else None
                    result.best_lap_time = best_lap_time_float
                    result.points = float(result_info['points'])
                    result.status_id = driver_status.id

        session.commit()
        print(f"🏁 Données de course pour l'année {year} synchronisées en base de données !")

    except requests.exceptions.RequestException as e:
        session.rollback()
        print(f"❌ Erreur lors de l'appel API pour l'année {year}: {e}")
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de l'insertion des données de course pour l'année {year}: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    # Example usage: seed data for a specific year
    # Retrieve all years stored in the database and seed data for each year
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        seasons = session.query(Season).all()
        for season in seasons:
            try:
                fetch_and_seed_race_data(season.year, session)
            except Exception as e:
                # This ensures season.year is accessible even if fetch_and_seed_race_data fails
                print(f"❌ Erreur lors du traitement de l'année {season.year} : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des saisons : {e}")
    finally:        
        session.close()