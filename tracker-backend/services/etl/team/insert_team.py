import requests
import fastf1 as ff1
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.team import Team
from models.country import Country
from models.season import Season
from dotenv import load_dotenv
import os
import time


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

def load_teams(session):
    print("Loading teams...")
    ergast_base_url = "https://api.jolpi.ca/ergast/f1/"
    teams_data = {}

    # Retrieve all seasons stored in the database to determine which years to fetch from Ergast
    seasons = session.query(Season).all()
    if not seasons:
        print("No seasons found in the database. Please load seasons before loading teams.")
        return
    
    start_year = min(season.year for season in seasons)
    end_year = max(season.year for season in seasons) + 1

    for year in range(start_year, end_year): # Adjust range as needed
        time.sleep(.5) # Be polite to the API and avoid hitting rate limits
        print(f"Fetching Ergast data for {year}...")
        url = f"{ergast_base_url}/{year}/constructors/?format=json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            constructors = data['MRData']['ConstructorTable']['Constructors']
            for constructor in constructors:
                constructor_id = constructor['constructorId']
                team_name = constructor['name']
                nationality = constructor['nationality']

                # Use constructorId as a more stable key, but store team_name for FastF1 matching
                if constructor_id not in teams_data:
                    teams_data[constructor_id] = {
                        'name': team_name,
                        'ergast_id': constructor_id,
                        'nationality': nationality,
                        'fastf1_data': {} # Placeholder for FastF1 data
                    }
                # If the team already exists, ensure we have the most up-to-date name/nationality
                # This could happen if a team's name changes slightly or a nationality is updated
                else:
                    teams_data[constructor_id]['name'] = team_name
                    teams_data[constructor_id]['nationality'] = nationality
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Ergast data for {year}: {e}")
            continue

    print("Fetching FastF1 data...")
    # FastF1 data for current year for team manager, engine, and colors
    # We only need one recent year to get general team info as it doesn't change much year-to-year
    # for these specific fields (manager, engine, color) compared to, say, driver lineups.
    try:
        current_fastf1_year = end_year -1 # Get data for the most recent completed season
        ff1_cache_dir = os.path.join(os.getenv("TEMP_DIR", "/tmp"), "fastf1_cache") # Use TEMP_DIR from context
        os.makedirs(ff1_cache_dir, exist_ok=True)
        ff1.Cache.enable_cache(ff1_cache_dir)

        # To get constructors, we need to load a session for a race
        # We'll try to get the first race of the season
        schedule = ff1.get_event_schedule(current_fastf1_year)
        if not schedule.empty:
            first_race_event = schedule.iloc[0]
            session_ff1 = ff1.get_session(current_fastf1_year, first_race_event['EventName'])
            session_ff1.load()
            teams_ff1 = session_ff1.constructors
            
            # Map FastF1 teams to Ergast teams
            for ff1_team_id, ff1_team_data in teams_ff1.items():
                ff1_team_name = ff1_team_data['Name']
                
                # Try to find a match based on name, might need more sophisticated matching
                for ergast_constructor_id, ergast_team_data in teams_data.items():
                    ergast_team_name = ergast_team_data['name']
                    # Simple substring match - can be improved if needed
                    if ff1_team_name.lower() in ergast_team_name.lower() or \
                       ergast_team_name.lower() in ff1_team_name.lower():
                        teams_data[ergast_constructor_id]['fastf1_data'] = {
                            'team_manager': ff1_team_data.get('TeamPrincipal'),
                            'is_engine_constructor': ff1_team_data.get('IsPowerUnitManufacturer', False),
                            'engine_constructor': ff1_team_data.get('EngineManufacturer'),
                            'main_color': ff1_team_data.get('TeamColor')
                        }
                        break
        else:
            print(f"No events found for FastF1 year {current_fastf1_year}. Skipping FastF1 data.")

    except Exception as e:
        print(f"Could not load FastF1 data for {current_fastf1_year}: {e}")
        print("Continuing without FastF1 detailed team data.")

    print("Processing teams for database insertion/update...")
    for constructor_id, data in teams_data.items():
        team_name = data['name']
        nationality = data.get('nationality')
        country_id = None
        if nationality:
            country_id = get_country_id(session, nationality)
            if not country_id:
                # Attempt to get country ID from FastF1 nationality if Ergast's wasn't found
                # (FastF1 often provides ISO alpha-3 codes or full names)
                # This requires a more robust country mapping or pre-population of the Country table.
                # For now, if Ergast nationality doesn't map, we'll try to use FastF1's if available
                # or just print a warning.
                print(f"Warning: Could not find country ID for Ergast nationality '{nationality}' for team {team_name}.")

        # If country_id is still None, we might have an issue.
        # Decide whether to skip the team or proceed with a null country_id.
        # For now, I'll allow null and let the DB schema handle nullable constraint.

        existing_team = session.query(Team).filter_by(name=team_name).first()

        fastf1_data = data.get('fastf1_data', {})
        # Ensure 'null' strings from APIs are treated as actual None
        team_manager = fastf1_data.get('team_manager')
        if isinstance(team_manager, str) and team_manager.lower() == 'null':
            team_manager = None
            
        is_engine_constructor = fastf1_data.get('is_engine_constructor', False) # Default to False
        
        engine_constructor = fastf1_data.get('engine_constructor')
        if isinstance(engine_constructor, str) and engine_constructor.lower() == 'null':
            engine_constructor = None
            
        main_color = fastf1_data.get('main_color')
        # FastF1 returns color as a hex string without '#', add it if missing
        if main_color and not main_color.startswith('#'):
            main_color = f"#{main_color}"

        if existing_team:
            # Update existing team
            existing_team.country_id = country_id
            existing_team.team_manager = team_manager
            existing_team.is_engine_constructor = is_engine_constructor
            existing_team.engine_constructor = engine_constructor
            existing_team.main_color = main_color
            print(f"Updated team: {existing_team.name}")
        else:
            # Add new team
            new_team = Team(
                name=team_name,
                country_id=country_id,
                team_manager=team_manager,
                is_engine_constructor=is_engine_constructor,
                engine_constructor=engine_constructor,
                main_color=main_color
            )
            session.add(new_team)
            print(f"Added new team: {new_team.name}")
    
    session.commit()
    print("Team loading complete.")

if __name__ == "__main__":
    session = get_session()
    try:
        load_teams(session)
    finally:
        session.close()