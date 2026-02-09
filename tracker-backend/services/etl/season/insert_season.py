import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.season import Season
from dotenv import load_dotenv
import os


def fetch_and_seed_seasons():
    load_dotenv()
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()

    print("📅 Récupération des saisons via Ergast API...")
    
    try:
        offset = 0
        all_seasons = []
        
        while True:
            url = f"https://api.jolpi.ca/ergast/f1/seasons?format=json&offset={offset}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()['MRData']
            seasons_data = data['SeasonTable']['Seasons']
            
            if not seasons_data:
                break
            
            all_seasons.extend(seasons_data)
            offset += 30
        
        print(f"✅ {len(all_seasons)} saisons récupérées. Début de l'insertion...")
        
        for season_info in all_seasons:
            year = int(season_info['season'])
            
            exists = session.query(Season).filter_by(year=year).first()
            
            if not exists:
                new_season = Season(year=year)
                session.add(new_season)

        session.commit()
        print("🏁 Toutes les saisons ont été synchronisées en base de données !")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'appel API : {e}")
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de l'insertion : {e}")
    finally:
        session.close()


if __name__ == "__main__":
    fetch_and_seed_seasons()