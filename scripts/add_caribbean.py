"""Add Caribbean countries to default_2016.json."""
import json, os

SCENARIO_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'data', 'scenarios', 'default_2016.json')

NEW_COUNTRIES = {
    "HTI": {
        "id": "HTI",
        "name": "Haïti",
        "flag": "🇭🇹",
        "capital": "Port-au-Prince",
        "continent": "Amérique du Nord",
        "population": 10848000,
        "government_type": "semi_présidentiel",
        "ideology": "démocratie_fragile",
        "leader": "Jovenel Moïse",
        "alliances": [],
        "economy": {
            "gdp": 8.7,
            "gdp_per_capita": 800,
            "gdp_growth": 1.2,
            "inflation": 13.8,
            "unemployment": 40.0,
            "debt_pct_gdp": 25.4,
            "currency": "HTG",
            "main_sectors": ["agriculture", "textile", "tourisme", "aide_internationale"],
            "sectors": {"agriculture": 22.0, "industrie": 20.0, "services": 58.0}
        },
        "military": {
            "strength": 1,
            "active_personnel": 1500,
            "nuclear_weapons": False,
            "defense_budget_pct": 0.5,
            "equipment": {"chars_combat": 0, "avions_chasse": 0, "navires_guerre": 0, "sous_marins": 0, "helicopteres": 6, "artillerie": 12}
        },
        "national_stats": {"sovereignty": 30.0, "food_autonomy": 52.0, "energy_autonomy": 18.0, "economic_independence": 18.0},
        "relations": {
            "DOM": -20, "USA": 30, "CAN": 25, "FRA": 35, "BRA": 20, "CUB": 10
        },
        "personality_traits": ["fragile", "dépendant_aide", "instable", "corrompu"],
        "description": "Pays le plus pauvre des Amériques, Haïti reste marqué par le séisme de 2010 et une instabilité politique chronique malgré une reconstruction partielle.",
        "color": "#0F3460"
    },
    "JAM": {
        "id": "JAM",
        "name": "Jamaïque",
        "flag": "🇯🇲",
        "capital": "Kingston",
        "continent": "Amérique du Nord",
        "population": 2813000,
        "government_type": "monarchie_constitutionnelle",
        "ideology": "démocratie_libérale",
        "leader": "Andrew Holness",
        "alliances": [],
        "economy": {
            "gdp": 14.3,
            "gdp_per_capita": 5080,
            "gdp_growth": 1.5,
            "inflation": 3.5,
            "unemployment": 14.0,
            "debt_pct_gdp": 127.8,
            "currency": "JMD",
            "main_sectors": ["tourisme", "bauxite", "agriculture", "textile"],
            "sectors": {"agriculture": 7.0, "industrie": 21.0, "services": 72.0}
        },
        "military": {
            "strength": 1,
            "active_personnel": 2830,
            "nuclear_weapons": False,
            "defense_budget_pct": 0.9,
            "equipment": {"chars_combat": 0, "avions_chasse": 4, "navires_guerre": 2, "sous_marins": 0, "helicopteres": 8, "artillerie": 16}
        },
        "national_stats": {"sovereignty": 55.0, "food_autonomy": 55.0, "energy_autonomy": 22.0, "economic_independence": 38.0},
        "relations": {
            "USA": 55, "GBR": 65, "CAN": 55, "TTO": 45, "CUB": 20, "DOM": 35, "BHS": 40
        },
        "personality_traits": ["pro_occidental", "diplomate", "CARICOM", "économie_ouverte"],
        "description": "Île des Caraïbes anglophones, la Jamaïque est membre du Commonwealth et dépend largement du tourisme et des transferts de la diaspora.",
        "color": "#000000"
    },
    "TTO": {
        "id": "TTO",
        "name": "Trinité-et-Tobago",
        "flag": "🇹🇹",
        "capital": "Port of Spain",
        "continent": "Amérique du Nord",
        "population": 1360000,
        "government_type": "régime_parlementaire",
        "ideology": "démocratie_libérale",
        "leader": "Keith Rowley",
        "alliances": [],
        "economy": {
            "gdp": 27.0,
            "gdp_per_capita": 19900,
            "gdp_growth": -2.3,
            "inflation": 4.8,
            "unemployment": 3.8,
            "debt_pct_gdp": 54.6,
            "currency": "TTD",
            "main_sectors": ["pétrole", "gaz_naturel", "pétrochimie", "industrie"],
            "sectors": {"agriculture": 1.0, "industrie": 48.0, "services": 51.0}
        },
        "military": {
            "strength": 2,
            "active_personnel": 4000,
            "nuclear_weapons": False,
            "defense_budget_pct": 1.3,
            "equipment": {"chars_combat": 0, "avions_chasse": 0, "navires_guerre": 4, "sous_marins": 0, "helicopteres": 12, "artillerie": 30}
        },
        "national_stats": {"sovereignty": 62.0, "food_autonomy": 38.0, "energy_autonomy": 95.0, "economic_independence": 52.0},
        "relations": {
            "USA": 55, "GBR": 60, "VEN": 40, "CAN": 55, "JAM": 45, "GUY": 50, "BRA": 35
        },
        "personality_traits": ["riche_pétrole", "pragmatique", "CARICOM", "pro_occidental"],
        "description": "Île la plus prospère des Caraïbes grâce à ses ressources en pétrole et gaz, Trinité-et-Tobago est le leader économique de la CARICOM mais subit la chute des cours en 2016.",
        "color": "#CE1126"
    },
    "BHS": {
        "id": "BHS",
        "name": "Bahamas",
        "flag": "🇧🇸",
        "capital": "Nassau",
        "continent": "Amérique du Nord",
        "population": 391000,
        "government_type": "monarchie_constitutionnelle",
        "ideology": "démocratie_libérale",
        "leader": "Perry Christie",
        "alliances": [],
        "economy": {
            "gdp": 12.1,
            "gdp_per_capita": 28674,
            "gdp_growth": 0.2,
            "inflation": 1.9,
            "unemployment": 15.0,
            "debt_pct_gdp": 58.3,
            "currency": "BSD",
            "main_sectors": ["tourisme", "finance_offshore", "immobilier", "transport_maritime"],
            "sectors": {"agriculture": 1.0, "industrie": 18.0, "services": 81.0}
        },
        "military": {
            "strength": 1,
            "active_personnel": 1500,
            "nuclear_weapons": False,
            "defense_budget_pct": 0.7,
            "equipment": {"chars_combat": 0, "avions_chasse": 0, "navires_guerre": 3, "sous_marins": 0, "helicopteres": 4, "artillerie": 8}
        },
        "national_stats": {"sovereignty": 58.0, "food_autonomy": 22.0, "energy_autonomy": 15.0, "economic_independence": 42.0},
        "relations": {
            "USA": 72, "GBR": 65, "CAN": 58, "JAM": 40, "CUB": 15, "MEX": 35
        },
        "personality_traits": ["pro_américain", "finance_offshore", "CARICOM", "tourisme_luxe"],
        "description": "Archipel prospère vivant principalement du tourisme et de la finance offshore, les Bahamas entretiennent des liens très étroits avec les États-Unis.",
        "color": "#00778B"
    },
    "BLZ": {
        "id": "BLZ",
        "name": "Belize",
        "flag": "🇧🇿",
        "capital": "Belmopan",
        "continent": "Amérique du Nord",
        "population": 360000,
        "government_type": "monarchie_constitutionnelle",
        "ideology": "démocratie_libérale",
        "leader": "Dean Barrow",
        "alliances": [],
        "economy": {
            "gdp": 1.75,
            "gdp_per_capita": 4850,
            "gdp_growth": 2.8,
            "inflation": 1.1,
            "unemployment": 10.8,
            "debt_pct_gdp": 76.1,
            "currency": "BZD",
            "main_sectors": ["tourisme", "agriculture", "énergie", "pêche"],
            "sectors": {"agriculture": 11.0, "industrie": 21.0, "services": 68.0}
        },
        "military": {
            "strength": 1,
            "active_personnel": 1100,
            "nuclear_weapons": False,
            "defense_budget_pct": 1.2,
            "equipment": {"chars_combat": 0, "avions_chasse": 0, "navires_guerre": 1, "sous_marins": 0, "helicopteres": 4, "artillerie": 10}
        },
        "national_stats": {"sovereignty": 55.0, "food_autonomy": 65.0, "energy_autonomy": 25.0, "economic_independence": 32.0},
        "relations": {
            "USA": 60, "GBR": 65, "MEX": 45, "GTM": -20, "JAM": 35, "CAN": 50
        },
        "personality_traits": ["pro_occidental", "CARICOM", "dispute_territoriale_guatemala", "économie_ouverte"],
        "description": "Seul pays anglophone d'Amérique centrale, le Belize entretient un vieux différend territorial avec le Guatemala et dépend fortement du tourisme et de l'agriculture.",
        "color": "#003F87"
    },
    "GUY": {
        "id": "GUY",
        "name": "Guyana",
        "flag": "🇬🇾",
        "capital": "Georgetown",
        "continent": "Amérique du Sud",
        "population": 774000,
        "government_type": "semi_présidentiel",
        "ideology": "démocratie_libérale",
        "leader": "David Granger",
        "alliances": [],
        "economy": {
            "gdp": 3.5,
            "gdp_per_capita": 4150,
            "gdp_growth": 3.1,
            "inflation": 1.0,
            "unemployment": 11.1,
            "debt_pct_gdp": 52.3,
            "currency": "GYD",
            "main_sectors": ["bauxite", "sucre", "or", "bois", "pétrole_offshore"],
            "sectors": {"agriculture": 19.0, "industrie": 30.0, "services": 51.0}
        },
        "military": {
            "strength": 1,
            "active_personnel": 3400,
            "nuclear_weapons": False,
            "defense_budget_pct": 1.8,
            "equipment": {"chars_combat": 0, "avions_chasse": 2, "navires_guerre": 2, "sous_marins": 0, "helicopteres": 6, "artillerie": 20}
        },
        "national_stats": {"sovereignty": 55.0, "food_autonomy": 75.0, "energy_autonomy": 45.0, "economic_independence": 35.0},
        "relations": {
            "USA": 55, "GBR": 60, "BRA": 45, "VEN": -30, "SUR": 30, "TTO": 50, "CAN": 45
        },
        "personality_traits": ["CARICOM", "dispute_territoriale_venezuela", "ressources_naturelles", "pro_occidental"],
        "description": "Seul pays anglophone d'Amérique du Sud, le Guyana est en plein essor grâce à la découverte de vastes réserves pétrolières offshore par ExxonMobil en 2015.",
        "color": "#009E60"
    },
    "SUR": {
        "id": "SUR",
        "name": "Suriname",
        "flag": "🇸🇷",
        "capital": "Paramaribo",
        "continent": "Amérique du Sud",
        "population": 571000,
        "government_type": "régime_présidentiel",
        "ideology": "semi_démocratique",
        "leader": "Dési Bouterse",
        "alliances": [],
        "economy": {
            "gdp": 5.2,
            "gdp_per_capita": 9100,
            "gdp_growth": -2.7,
            "inflation": 25.0,
            "unemployment": 8.0,
            "debt_pct_gdp": 68.8,
            "currency": "SRD",
            "main_sectors": ["pétrole", "or", "bauxite", "bois"],
            "sectors": {"agriculture": 10.0, "industrie": 36.0, "services": 54.0}
        },
        "military": {
            "strength": 1,
            "active_personnel": 1800,
            "nuclear_weapons": False,
            "defense_budget_pct": 1.4,
            "equipment": {"chars_combat": 0, "avions_chasse": 0, "navires_guerre": 1, "sous_marins": 0, "helicopteres": 5, "artillerie": 15}
        },
        "national_stats": {"sovereignty": 52.0, "food_autonomy": 62.0, "energy_autonomy": 55.0, "economic_independence": 38.0},
        "relations": {
            "NLD": 55, "BRA": 40, "GUY": 30, "TTO": 40, "USA": 35, "FRA": 30
        },
        "personality_traits": ["autoritaire_modéré", "ressources_naturelles", "crise_économique", "CARICOM"],
        "description": "Ancienne colonie néerlandaise riche en pétrole, or et bauxite, le Suriname traverse une grave crise économique en 2016 sous la présidence controversée de Bouterse.",
        "color": "#377E3F"
    }
}

with open(SCENARIO_PATH, encoding='utf-8') as f:
    data = json.load(f)

for cid, country in NEW_COUNTRIES.items():
    data['countries'][cid] = country

with open(SCENARIO_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Added: {', '.join(NEW_COUNTRIES.keys())}")
print(f"Total countries: {len(data['countries'])}")
