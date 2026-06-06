from openai import AsyncOpenAI
from typing import AsyncGenerator
from app.dependencies import AiConfig
import logging
import random

logger = logging.getLogger(__name__)

COUNTRY_CENTROIDS: dict[str, list[float]] = {
    "USA": [-98.0, 38.0], "CHN": [104.0, 35.0], "RUS": [90.0, 61.0],
    "DEU": [10.0, 51.0], "FRA": [2.0, 46.0], "GBR": [-2.0, 54.0],
    "JPN": [138.0, 37.0], "IND": [78.0, 22.0], "BRA": [-51.0, -14.0],
    "CAN": [-96.0, 60.0], "AUS": [133.0, -25.0], "KOR": [128.0, 37.0],
    "MEX": [-102.0, 23.0], "IDN": [118.0, -2.0], "SAU": [45.0, 24.0],
    "TUR": [35.0, 39.0], "ITA": [12.0, 43.0], "ESP": [-3.0, 40.0],
    "ARG": [-64.0, -34.0], "ZAF": [25.0, -29.0], "IRN": [53.0, 32.0],
    "ISR": [35.0, 31.0], "PRK": [127.0, 40.0], "UKR": [32.0, 49.0],
    "POL": [20.0, 52.0], "NLD": [5.0, 52.0], "CHE": [8.0, 47.0],
    "SWE": [18.0, 62.0], "NOR": [10.0, 65.0], "PAK": [70.0, 30.0],
    "NGA": [8.0, 10.0], "EGY": [30.0, 27.0], "VNM": [106.0, 16.0],
    "PHL": [122.0, 13.0], "COL": [-73.0, 4.0], "VEN": [-66.0, 8.0],
    "IRQ": [44.0, 33.0], "SYR": [38.0, 35.0], "ARE": [54.0, 24.0],
    "QAT": [51.0, 25.0], "CUB": [-79.0, 22.0], "KAZ": [68.0, 48.0],
    "THA": [101.0, 15.0], "MYS": [110.0, 3.0], "ETH": [40.0, 9.0],
    "GRC": [22.0, 39.0], "CZE": [15.0, 50.0], "HUN": [19.0, 47.0],
    "ROU": [25.0, 46.0],
}


def _poi_coordinates(country_id: str) -> list[float]:
    base = COUNTRY_CENTROIDS.get(country_id, [0.0, 0.0])
    return [
        round(base[0] + random.uniform(-4, 4), 2),
        round(base[1] + random.uniform(-3, 3), 2),
    ]


def _client(config: AiConfig) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)


def _build_kwargs(messages: list[dict]) -> dict:
    """Convert chat-style messages to Responses API format.
    socle.ai ignores `instructions`, so system context is injected
    into the first user message as a [CONTEXTE] block.
    """
    system = ""
    conversation = []
    for msg in messages:
        if msg["role"] == "system":
            system = (system + "\n\n" + msg["content"]).strip()
        else:
            conversation.append({"role": msg["role"], "content": msg["content"]})

    if system and conversation:
        first = conversation[0]
        if first["role"] == "user":
            conversation[0] = {
                "role": "user",
                "content": f"[CONTEXTE]\n{system}\n\n[MESSAGE]\n{first['content']}",
            }
    elif system:
        conversation = [{"role": "user", "content": system}]

    return {"input": conversation}


async def chat(messages: list[dict], config: AiConfig) -> str:
    kwargs = _build_kwargs(messages)
    response = await _client(config).responses.create(model=config.model, **kwargs)
    return response.output_text or ""


async def stream_chat(messages: list[dict], config: AiConfig) -> AsyncGenerator[str, None]:
    kwargs = _build_kwargs(messages)
    try:
        stream = await _client(config).responses.create(
            model=config.model, stream=True, **kwargs
        )
        async for event in stream:
            if getattr(event, "type", None) == "response.output_text.delta":
                delta = getattr(event, "delta", "")
                if delta:
                    yield delta
    except Exception as e:
        logger.warning("Streaming failed (%s), falling back to non-streaming", e)
        response = await _client(config).responses.create(model=config.model, **kwargs)
        yield response.output_text or ""


async def get_country_response(
    country: dict,
    player_country: dict,
    player_message: str,
    world_context: str,
    diplomatic_history: list[dict],
    config: AiConfig,
) -> AsyncGenerator[str, None]:
    relations_score = country.get("relations", {}).get(player_country["id"], 0)
    traits = ", ".join(country.get("personality_traits", ["diplomatique"]))

    system = f"""Tu es le représentant officiel de {country['name']} dans une simulation géopolitique se déroulant en {world_context}.

Profil de ton pays :
- Gouvernement : {country.get('government_type', 'inconnu')}
- Idéologie : {country.get('ideology', 'pragmatique')}
- Dirigeant : {country.get('leader', 'inconnu')}
- Traits diplomatiques : {traits}
- Relations avec {player_country['name']} : {relations_score}/100 ({_relation_label(relations_score)})
- PIB : {country.get('economy', {}).get('gdp', 0) if country.get('economy') else 0} milliards USD
- Population : {country.get('population', 0):,}
- Alliances : {', '.join(country.get('alliances', [])) or 'aucune'}

Tu dois répondre en restant fidèle aux intérêts nationaux de ton pays, à son idéologie et à ses relations diplomatiques actuelles.
Sois réaliste, concis (2-3 paragraphes) et diplomatiquement crédible. Réponds en français."""

    messages = [{"role": "system", "content": system}]
    for h in diplomatic_history[-6:]:
        if h.get("player"):
            messages.append({"role": "user", "content": h["player"]})
        if h.get("response"):
            messages.append({"role": "assistant", "content": h["response"]})
    messages.append({"role": "user", "content": f"Message de {player_country['name']} : {player_message}"})

    async for chunk in stream_chat(messages, config):
        yield chunk


async def get_advisor_response(
    player_country: dict,
    world_context: str,
    country_state: dict,
    question: str,
    recent_events: list[dict],
    config: AiConfig,
) -> AsyncGenerator[str, None]:
    stability = country_state.get("stability", 50)
    at_war = country_state.get("at_war_with", [])

    events_context = ""
    if recent_events:
        lines = [f"- {e.get('title', '')} ({e.get('type', '')}): {e.get('description', '')}" for e in recent_events[-4:]]
        events_context = "\nÉvénements internes récents :\n" + "\n".join(lines)

    system = f"""Tu es le conseiller politique principal de {player_country['name']} dans une simulation géopolitique.
Nous sommes en {world_context}.

État actuel de {player_country['name']} :
- Gouvernement : {player_country.get('government_type', 'inconnu')}
- Idéologie : {player_country.get('ideology', 'inconnu')}
- Dirigeant : {player_country.get('leader', 'inconnu')}
- Stabilité nationale : {stability}/100
- En guerre avec : {', '.join(at_war) if at_war else 'personne'}
- PIB : {player_country.get('economy', {}).get('gdp', 0) if player_country.get('economy') else 0} milliards USD
- Alliances : {', '.join(player_country.get('alliances', [])) or 'aucune'}{events_context}

Tu fournis des conseils stratégiques réalistes, pragmatiques et bien argumentés.
Tu dois toujours proposer plusieurs options avec leurs avantages et risques.
Réponds en français, de façon structurée et concise."""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

    async for chunk in stream_chat(messages, config):
        yield chunk


async def process_player_action(
    player_country: dict,
    action: str,
    year: int,
    month: int,
    world_state: dict,
    config: AiConfig,
) -> dict:
    """Returns structured dict including Game Master domestic events and optional map POI."""
    player_id = player_country["id"]
    countries_summary = [
        f"- {cid}: stabilité {cs.get('stability', 50)}/100"
        for cid, cs in list(world_state.items())[:12]
    ]

    system = f"""Tu es le moteur de simulation géopolitique et maître du jeu de Pax Historia.
Nous sommes en {_format_date(year, month)}.
Le joueur contrôle {player_country['name']} (ID: {player_id}).
Gouvernement : {player_country.get('government_type', 'inconnu')}, idéologie : {player_country.get('ideology', 'inconnu')}.

Contexte mondial :
{chr(10).join(countries_summary)}

Analyse l'action du joueur et réponds UNIQUEMENT en JSON valide, sans texte autour :
{{
  "narrative": "Texte narratif immersif en français (3-4 paragraphes)",
  "applicable": true,
  "relation_changes": {{"{player_id}": {{"COUNTRY_ID": delta_int}}}},
  "stability_delta": int_entre_moins30_et_plus30,
  "economy_delta": float_entre_moins0point1_et_plus0point1,
  "domestic_events": [
    {{
      "title": "Titre de l'événement interne",
      "description": "Description en 2 phrases réalistes",
      "type": "protest|rally|scandal|economic|military|infrastructure|social|cultural",
      "severity": 1,
      "stability_impact": -5
    }}
  ],
  "map_poi": null
}}

Règles générales :
- applicable=false si l'action est irréaliste ou impossible dans le contexte
- relation_changes : ex déclarer la guerre = -60 avec la cible, +10 avec les alliés
- stability_delta : impact sur la stabilité intérieure (-30 à +30)
- economy_delta : facteur multiplicatif sur l'économie (-0.05 à +0.05)

Règles domestic_events (0-2 événements du maître du jeu) :
- protest : manifestations, grèves (décisions impopulaires)
- rally : rassemblements de soutien (décisions populaires)
- scandal : scandales politiques
- economic : crises ou opportunités économiques locales
- military : mobilisation, préparatifs, alertes
- infrastructure : construction, inauguration, destruction
- social : tensions ou cohésion sociale
- cultural : événements culturels, symboles identitaires
- severity : 1=mineur, 2=significatif, 3=majeur
- stability_impact : -15 à +10

Règles map_poi (null OU 1 objet si l'action crée une infrastructure physique tangible) :
- type : "university"|"military_base"|"factory"|"hospital"|"parliament"|"port"|"dam"|"research_center"|"monument"|"embassy"|"airport"|"nuclear_plant"|"cultural_center"|"stadium"
- icon : emoji (🎓 université, ⚔️ base militaire, 🏭 usine, 🏥 hôpital, 🏛️ parlement, ⚓ port, 💧 barrage, 🔬 recherche, 🗿 monument, 🏢 ambassade, ✈️ aéroport, ☢️ nucléaire, 🎭 culture, 🏟️ stade)
- name : nom spécifique en français (ex: "Université de Montréal", "Base navale de Halifax")
- Si applicable=false : domestic_events=[], map_poi=null"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Action de {player_country['name']} : {action}"},
    ]
    raw = await chat(messages, config)
    return _parse_action_json(raw, player_id)


def _parse_action_json(raw: str, player_id: str) -> dict:
    import json, re
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            poi_data = data.get("map_poi")
            poi = None
            if poi_data and isinstance(poi_data, dict) and poi_data.get("name"):
                poi = {
                    "name": poi_data.get("name", "Point d'intérêt"),
                    "type": poi_data.get("type", "monument"),
                    "icon": poi_data.get("icon", "📍"),
                    "coordinates": _poi_coordinates(player_id),
                    "country_id": player_id,
                }
            domestic = []
            for de in (data.get("domestic_events") or [])[:2]:
                if isinstance(de, dict) and de.get("title"):
                    domestic.append({
                        "title": de.get("title", "Événement interne"),
                        "description": de.get("description", ""),
                        "type": de.get("type", "social"),
                        "severity": max(1, min(3, int(de.get("severity", 1)))),
                        "stability_impact": max(-15, min(10, int(de.get("stability_impact", 0)))),
                    })
            return {
                "narrative": data.get("narrative", raw),
                "applicable": bool(data.get("applicable", True)),
                "relation_changes": data.get("relation_changes", {}),
                "stability_delta": int(data.get("stability_delta", 0)),
                "economy_delta": float(data.get("economy_delta", 0.0)),
                "domestic_events": domestic,
                "map_poi": poi,
            }
    except Exception:
        pass
    return {
        "narrative": raw, "applicable": True, "relation_changes": {},
        "stability_delta": 0, "economy_delta": 0.0, "domestic_events": [], "map_poi": None,
    }


async def generate_turn_events(
    year: int,
    month: int,
    world_state: dict,
    player_country_id: str,
    config: AiConfig,
) -> list[dict]:
    system = f"""Tu es le moteur d'événements mondiaux de Pax Historia.
Nous sommes en {_format_date(year, month)}.

Génère 2-3 événements mondiaux crédibles qui surviennent ce mois-ci, sans lien direct avec les actions du joueur.
Ces événements doivent refléter la géopolitique réaliste de cette période.
Réponds UNIQUEMENT avec un JSON valide, sans texte autour :
[
  {{
    "title": "Titre de l'événement",
    "description": "Description (2-3 phrases)",
    "affected_countries": ["USA", "RUS"],
    "relation_changes": {{"USA": {{"RUS": -5}}}}
  }}
]"""

    messages = [{"role": "system", "content": system}]
    raw = await chat(messages, config)
    return _parse_events_json(raw)


def _parse_events_json(raw: str) -> list[dict]:
    import json, re
    try:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return []


def _relation_label(score: int) -> str:
    if score >= 70: return "allié"
    if score >= 30: return "ami"
    if score >= -10: return "neutre"
    if score >= -50: return "hostile"
    return "ennemi"


def _format_date(year: int, month: int) -> str:
    months = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    return f"{months[month - 1]} {year}"
