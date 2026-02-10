import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.country import Country # Ton modèle SQLAlchemy


def insert_country(session, name, iso_code, flag_url=None, timezone=None, alt_spellings=None, female_demonym=None, male_demonym=None):
    try:
        exists = session.query(Country).filter_by(iso_code=iso_code).first()
        
        if not exists:
            new_country = Country(name=name, iso_code=iso_code, flag_url=flag_url, timezone=timezone, alt_spellings=alt_spellings, female_demonym=female_demonym, male_demonym=male_demonym)
            session.add(new_country)
            session.commit()
            print(f"✅ Pays {name} ({iso_code}) inséré en base de données.")
        else:
            print(f"⚠️ Pays {name} ({iso_code}) existe déjà en base de données. Ignoré.")
    
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de l'insertion du pays {name} ({iso_code}) : {e}")


def fetch_and_seed_countries():
    # 1. Configuration de la connexion
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()

    print("🌍 Récupération des pays via Rest Countries API...")
    
    try:
        # 2. Appel à l'API (on demande uniquement le nom commun, le code ISO alpha-3 et les drapeaux)
        response = requests.get("https://restcountries.com/v3.1/all?fields=name,cca3,flags,altSpellings,timezones,demonyms")
        response.raise_for_status()
        countries_data = response.json()

        print(f"✅ {len(countries_data)} pays récupérés. Début de l'insertion...")

        for country_info in countries_data:
            name = country_info['name']['common']
            iso_code = country_info['cca3']
            flag_url = country_info.get('flags', {}).get('png')  # Récupère l'URL du drapeau si disponible
            timezone = country_info.get('timezones', [None])[0]  # Récupère le premier fuseau horaire si disponible
            alt_spellings = ", ".join(country_info.get('altSpellings', []))  # Concatène les orthographes alternatives
            female_demonym = country_info.get('demonyms', {}).get('eng', {}).get('f')  # Récupère le gentilé féminin en anglais
            male_demonym = country_info.get('demonyms', {}).get('eng', {}).get('m')  # Récupère le gentilé masculin en anglais

            # 3. Vérification si le pays existe déjà (idempotence)
            exists = session.query(Country).filter_by(iso_code=iso_code).first()
            
            if not exists:
                insert_country(session, name, iso_code, flag_url, timezone, alt_spellings, female_demonym, male_demonym)

        session.commit()
        print("🏁 Tous les pays ont été synchronisés en base de données !")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'appel API : {e}")
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de l'insertion : {e}")
    finally:
        session.close()

if __name__ == "__main__":
    fetch_and_seed_countries()