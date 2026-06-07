from openai import AsyncOpenAI
from typing import AsyncGenerator
from app.dependencies import AiConfig
import logging
import random

logger = logging.getLogger(__name__)

# ─── Socle memory store (previous_response_id chaining) ──────────────────────
# Keys: "advisor:{session_id}" | "diplomacy:{session_id}:{country_id}"
_memory: dict[str, str] = {}

AGENT_NAME = "MJ Phos"
DEFAULT_SOCLE_MODEL = "qwen3-235b-a22b-instruct-2507"

# key: base_url → {"id": "ast_xxx", "model": "llm-name"}
_agent_cache: dict[str, dict] = {}

_MJ_PHOS_INSTRUCTIONS = (
    "Tu es MJ Phos, le maître du jeu d'une simulation géopolitique réaliste. "
    "Tu joues simultanément le rôle de conseiller stratégique, de représentant des pays étrangers, "
    "et de narrateur des événements mondiaux. "
    "Tu es réaliste, cohérent avec le contexte géopolitique, et tu maintiens la mémoire des événements passés."
)


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


def _is_socle(config: AiConfig) -> bool:
    url = config.base_url or ""
    return "socle.ai" in url or "host.docker.internal" in url


# ─── Agent resolution ────────────────────────────────────────────────────────

def _llm_from_config(config: AiConfig) -> str:
    if not config.model or config.model == AGENT_NAME:
        return DEFAULT_SOCLE_MODEL
    return config.model


def _session_from_memory_key(memory_key: str | None) -> str | None:
    """Extract session_id from keys like 'advisor:{sid}' or 'diplomacy:{sid}:{cid}'."""
    if not memory_key:
        return None
    parts = memory_key.split(":")
    return parts[1] if len(parts) >= 2 else None


def _agent_name(session_id: str | None) -> str:
    return f"{session_id}-MJPhos" if session_id else AGENT_NAME


async def _resolve_model(config: AiConfig, session_id: str | None = None) -> str:
    """Return ast_xxx id for the session's MJ Phos agent, creating/updating it as needed."""
    if config.model.startswith("ast_"):
        return config.model

    llm = _llm_from_config(config)
    name = _agent_name(session_id)
    cache_key = f"{config.base_url}:{name}"

    cached = _agent_cache.get(cache_key)
    if cached and cached["model"] == llm:
        return cached["id"]

    client = _client(config)
    agents = await client.beta.assistants.list()
    for agent in agents.data:
        if agent.name == name:
            if getattr(agent, "model", None) != llm:
                await client.beta.assistants.update(agent.id, model=llm)
                logger.info("Updated agent '%s' model → %s", name, llm)
            _agent_cache[cache_key] = {"id": agent.id, "model": llm}
            return agent.id

    agent = await client.beta.assistants.create(
        name=name,
        instructions=_MJ_PHOS_INSTRUCTIONS,
        model=llm,
    )
    _agent_cache[cache_key] = {"id": agent.id, "model": llm}
    logger.info("Created agent '%s' → %s (model: %s)", name, agent.id, llm)
    return agent.id


async def sync_agent(config: AiConfig) -> dict:
    """Force agent re-sync (model update). Called explicitly when settings change."""
    llm = _llm_from_config(config)
    for key in list(_agent_cache.keys()):
        if key.startswith(config.base_url):
            _agent_cache.pop(key, None)
    agent_id = await _resolve_model(config)
    return {"agent_id": agent_id, "model": llm}


# ─── Socle Responses API ──────────────────────────────────────────────────────

def _build_responses_kwargs(messages: list[dict]) -> dict:
    """Convert chat-style messages to Socle Responses API format.
    System content is injected as a [CONTEXTE] block in the first user message.
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


async def _chat_responses(messages: list[dict], config: AiConfig, memory_key: str | None) -> str:
    kwargs = _build_responses_kwargs(messages)
    prev_id = _memory.get(memory_key) if memory_key else None
    if prev_id:
        kwargs["previous_response_id"] = prev_id
    session_id = _session_from_memory_key(memory_key)
    model = await _resolve_model(config, session_id)
    response = await _client(config).responses.create(
        model=model, store=True, **kwargs
    )
    if memory_key:
        _memory[memory_key] = response.id
    return response.output_text or ""


async def _stream_responses(
    messages: list[dict], config: AiConfig, memory_key: str | None
) -> AsyncGenerator[str, None]:
    kwargs = _build_responses_kwargs(messages)
    prev_id = _memory.get(memory_key) if memory_key else None
    if prev_id:
        kwargs["previous_response_id"] = prev_id
    session_id = _session_from_memory_key(memory_key)
    try:
        model = await _resolve_model(config, session_id)
        stream = await _client(config).responses.create(
            model=model, stream=True, store=True, **kwargs
        )
        new_id: str | None = None
        async for event in stream:
            etype = getattr(event, "type", None)
            if etype == "response.created":
                new_id = getattr(getattr(event, "response", None), "id", None)
            elif etype == "response.output_text.delta":
                delta = getattr(event, "delta", "")
                if delta:
                    yield delta
        if memory_key and new_id:
            _memory[memory_key] = new_id
    except Exception as e:
        logger.warning("Responses API streaming failed (%s), fallback to sync", e)
        model = await _resolve_model(config, session_id)
        response = await _client(config).responses.create(
            model=model, store=True, **kwargs
        )
        if memory_key:
            _memory[memory_key] = response.id
        yield response.output_text or ""


# ─── Standard Chat Completions API (Ollama, OpenAI, …) ───────────────────────

async def _chat_completions(messages: list[dict], config: AiConfig) -> str:
    model = _llm_from_config(config) if _is_socle(config) else config.model
    response = await _client(config).chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content or ""


async def _chat_responses_raw(messages: list[dict], config: AiConfig) -> str:
    """Socle one-shot call via Responses API with raw LLM (no agent, no memory)."""
    kwargs = _build_responses_kwargs(messages)
    llm = _llm_from_config(config)
    response = await _client(config).responses.create(
        model=llm, store=False, **kwargs
    )
    return response.output_text or ""


async def _stream_completions(
    messages: list[dict], config: AiConfig
) -> AsyncGenerator[str, None]:
    try:
        stream = await _client(config).chat.completions.create(
            model=config.model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        logger.warning("Chat completions streaming failed (%s), fallback to sync", e)
        response = await _client(config).chat.completions.create(
            model=config.model,
            messages=messages,
        )
        yield response.choices[0].message.content or ""


# ─── Unified entry points ─────────────────────────────────────────────────────

async def chat(
    messages: list[dict], config: AiConfig, memory_key: str | None = None
) -> str:
    if _is_socle(config):
        # Use Responses API with raw LLM (no agent) — Chat Completions on local
        # Socle has a server-side bug where `tools` is not defined.
        return await _chat_responses_raw(messages, config)
    return await _chat_completions(messages, config)


async def stream_chat(
    messages: list[dict], config: AiConfig, memory_key: str | None = None
) -> AsyncGenerator[str, None]:
    if _is_socle(config):
        async for chunk in _stream_responses(messages, config, memory_key):
            yield chunk
    else:
        async for chunk in _stream_completions(messages, config):
            yield chunk


# ─── Public AI functions ──────────────────────────────────────────────────────

async def get_country_response(
    country: dict,
    player_country: dict,
    player_message: str,
    world_context: str,
    diplomatic_history: list[dict],
    config: AiConfig,
    session_id: str = "",
) -> AsyncGenerator[str, None]:
    relations_score = country.get("relations", {}).get(player_country["id"], 0)
    traits = ", ".join(country.get("personality_traits", ["diplomatique"]))

    personality = country.get("personality", "").strip()
    personality_block = f"\n\nPersonnalité & style diplomatique :\n{personality}" if personality else ""

    system = f"""Tu es le représentant officiel de {country['name']} dans une simulation géopolitique se déroulant en {world_context}.

Profil de ton pays :
- Gouvernement : {country.get('government_type', 'inconnu')}
- Idéologie : {country.get('ideology', 'pragmatique')}
- Dirigeant : {country.get('leader', 'inconnu')}
- Traits diplomatiques : {traits}
- Relations avec {player_country['name']} : {relations_score}/100 ({_relation_label(relations_score)})
- PIB : {country.get('economy', {}).get('gdp', 0) if country.get('economy') else 0} milliards USD
- Population : {country.get('population', 0):,}
- Alliances : {', '.join(country.get('alliances', [])) or 'aucune'}{personality_block}

Tu dois répondre en restant fidèle aux intérêts nationaux de ton pays, à son idéologie et à ses relations diplomatiques actuelles.
Sois réaliste, concis (2-3 paragraphes) et diplomatiquement crédible. Réponds en français."""

    messages = [{"role": "system", "content": system}]
    for h in diplomatic_history[-6:]:
        if h.get("player"):
            messages.append({"role": "user", "content": h["player"]})
        if h.get("response"):
            messages.append({"role": "assistant", "content": h["response"]})
    messages.append({"role": "user", "content": f"Message de {player_country['name']} : {player_message}"})

    memory_key = f"diplomacy:{session_id}:{country['id']}" if session_id else None
    async for chunk in stream_chat(messages, config, memory_key):
        yield chunk


async def get_advisor_response(
    player_country: dict,
    world_context: str,
    country_state: dict,
    question: str,
    recent_events: list[dict],
    config: AiConfig,
    session_id: str = "",
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

    memory_key = f"advisor:{session_id}" if session_id else None
    async for chunk in stream_chat(messages, config, memory_key):
        yield chunk


async def process_player_action(
    player_country: dict,
    action: str,
    year: int,
    month: int,
    world_state: dict,
    config: AiConfig,
    recent_diplomacy: list[dict] | None = None,
) -> dict:
    """Returns structured dict including Game Master domestic events and optional map POI."""
    player_id = player_country["id"]
    countries_summary = [
        f"- {cid}: stabilité {cs.get('stability', 50)}/100"
        for cid, cs in list(world_state.items())[:12]
    ]

    diplomacy_context = ""
    if recent_diplomacy:
        lines = []
        for d in recent_diplomacy[-6:]:
            if d.get("player"):
                lines.append(f"  → {player_country['name']} : {d['player'][:120]}")
            if d.get("response"):
                lines.append(f"  ← Réponse : {d['response'][:120]}")
        if lines:
            diplomacy_context = "\n\nDiplomatie récente :\n" + "\n".join(lines)

    system = f"""Tu es le moteur de simulation géopolitique et maître du jeu de Phos.
Nous sommes en {_format_date(year, month)}.
Le joueur contrôle {player_country['name']} (ID: {player_id}).
Gouvernement : {player_country.get('government_type', 'inconnu')}, idéologie : {player_country.get('ideology', 'inconnu')}.

Contexte mondial :
{chr(10).join(countries_summary)}{diplomacy_context}

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
  "map_poi": null,
  "stat_deltas": {{
    "sovereignty": 0,
    "food_autonomy": 0,
    "energy_autonomy": 0,
    "economic_independence": 0
  }},
  "future_events": [
    {{
      "title": "Titre de la conséquence future",
      "description": "Description en 2 phrases",
      "type": "consequence",
      "months_ahead": 2,
      "stability_impact": -5,
      "economy_impact": 0.0
    }}
  ]
}}

Règles générales :
- applicable=false si l'action est irréaliste ou impossible dans le contexte
- relation_changes : ex déclarer la guerre = -60 avec la cible, +10 avec les alliés
- stability_delta : impact sur la stabilité intérieure (-30 à +30)
- economy_delta : facteur multiplicatif sur l'économie (-0.05 à +0.05)
- stat_deltas : variations des indices stratégiques (-10 à +10 par champ)
  - sovereignty : réformes institutionnelles, coups d'état, cessions de souveraineté
  - food_autonomy : investissements agricoles, sécheresse, accords alimentaires
  - energy_autonomy : projets énergétiques, embargo, nouvelles centrales
  - economic_independence : traités commerciaux, sanctions, industrialisation

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
- Si applicable=false : domestic_events=[], map_poi=null

Règles future_events (0-2 conséquences différées) :
- Si l'action a des retombées logiques à moyen terme (1-4 mois plus tard), les lister ici
- months_ahead : dans combien de mois cela surviendra (1 à 4)
- stability_impact : -20 à +15 (conséquence sur la stabilité à terme)
- economy_impact : -0.05 à +0.05
- Exemples : retombées économiques d'un embargo, résultats d'un référendum, fin d'un chantier
- Si pas de conséquences différées logiques : future_events=[]"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Action de {player_country['name']} : {action}"},
    ]
    raw = await chat(messages, config)
    return _parse_action_json(raw, player_id)


def _normalize_action_data(data: dict, raw: str) -> dict:
    """Coerce any malformed fields in a parsed action response to safe types."""
    if not isinstance(data.get("narrative"), str) or not data["narrative"].strip():
        data["narrative"] = raw
    if not isinstance(data.get("applicable"), bool):
        data["applicable"] = True
    if not isinstance(data.get("stability_delta"), (int, float)):
        data["stability_delta"] = 0
    if not isinstance(data.get("economy_delta"), (int, float)):
        data["economy_delta"] = 0.0
    if not isinstance(data.get("relation_changes"), dict):
        data["relation_changes"] = {}
    return data


def _parse_action_json(raw: str, player_id: str) -> dict:
    import json, re
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            if not isinstance(data, dict):
                raise ValueError("not a dict")
            data = _normalize_action_data(data, raw)

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
                        "title": str(de.get("title", "Événement interne")),
                        "description": str(de.get("description", "")),
                        "type": str(de.get("type", "social")),
                        "severity": max(1, min(3, int(de.get("severity", 1)))),
                        "stability_impact": max(-15, min(10, int(de.get("stability_impact", 0)))),
                    })
            raw_sd = data.get("stat_deltas") if isinstance(data.get("stat_deltas"), dict) else {}
            stat_deltas = {
                k: max(-10, min(10, int(raw_sd.get(k, 0))))
                for k in ("sovereignty", "food_autonomy", "energy_autonomy", "economic_independence")
            }
            rc = data.get("relation_changes", {})
            safe_rc: dict = {}
            if isinstance(rc, dict):
                for cid, deltas in rc.items():
                    if isinstance(deltas, dict):
                        safe_rc[str(cid)] = {str(k): int(v) for k, v in deltas.items() if isinstance(v, (int, float))}
            future_events = []
            for fe in (data.get("future_events") or [])[:2]:
                if isinstance(fe, dict) and fe.get("title") and isinstance(fe.get("months_ahead"), int):
                    future_events.append({
                        "title": str(fe["title"]),
                        "description": str(fe.get("description", "")),
                        "type": str(fe.get("type", "consequence")),
                        "months_ahead": max(1, min(4, fe["months_ahead"])),
                        "stability_impact": max(-20, min(15, int(fe.get("stability_impact", 0)))),
                        "economy_impact": max(-0.05, min(0.05, float(fe.get("economy_impact", 0.0)))),
                    })
            return {
                "narrative": data["narrative"],
                "applicable": data["applicable"],
                "relation_changes": safe_rc,
                "stability_delta": max(-30, min(30, int(data["stability_delta"]))),
                "economy_delta": max(-0.1, min(0.1, float(data["economy_delta"]))),
                "domestic_events": domestic,
                "map_poi": poi,
                "stat_deltas": stat_deltas,
                "future_events": future_events,
            }
    except Exception as exc:
        logger.warning("Action JSON parse failed (%s). Raw: %.200s", exc, raw)
    return {
        "narrative": raw, "applicable": True, "relation_changes": {},
        "stability_delta": 0, "economy_delta": 0.0, "domestic_events": [], "map_poi": None,
        "stat_deltas": {"sovereignty": 0, "food_autonomy": 0, "energy_autonomy": 0, "economic_independence": 0},
        "future_events": [],
    }


async def generate_turn_events(
    year: int,
    month: int,
    world_state: dict,
    player_country_id: str,
    config: AiConfig,
    recent_player_actions: list[str] | None = None,
) -> list[dict]:
    reactions_block = ""
    if recent_player_actions:
        actions_text = "\n".join(f"- {a}" for a in recent_player_actions[-3:])
        reactions_block = f"""
Actions récentes du joueur ({player_country_id}) :
{actions_text}

Génère 1-2 événements supplémentaires représentant les RÉACTIONS des pays voisins ou concernés à ces actions (type "reaction").
Garde également 1-2 événements mondiaux indépendants."""

    system = f"""Tu es le moteur d'événements mondiaux de Phos.
Nous sommes en {_format_date(year, month)}.

Génère 2-4 événements mondiaux crédibles qui surviennent ce mois-ci.
Chaque événement doit avoir un type parmi : diplomatic, economic, military, humanitarian, political, natural, reaction, consequence.{reactions_block}

Réponds UNIQUEMENT avec un JSON valide, sans texte autour :
[
  {{
    "title": "Titre de l'événement",
    "description": "Description (2-3 phrases)",
    "affected_countries": ["USA", "RUS"],
    "relation_changes": {{"USA": {{"RUS": -5}}}},
    "type": "diplomatic",
    "stability_impact": 0,
    "economy_impact": 0.0
  }}
]

Règles stability_impact / economy_impact :
- Ne renseigner que si le joueur ({player_country_id}) est dans affected_countries
- stability_impact : entier de -30 à +10 (ex: séisme majeur = -15, crise économique = -8, accord régional = +3)
- economy_impact : float de -0.08 à +0.05 (ex: séisme = -0.04, embargo régional = -0.02, boom commercial = +0.01)
- Sinon laisser à 0 / 0.0"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Génère les événements mondiaux de ce mois."},
    ]
    raw = await chat(messages, config)
    return _parse_events_json(raw)


def _parse_events_json(raw: str) -> list[dict]:
    import json, re
    try:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            events = json.loads(match.group())
            if not isinstance(events, list):
                return []
            valid_types = {"diplomatic", "economic", "military", "humanitarian", "political", "natural", "reaction", "consequence", "general"}
            valid = []
            for e in events:
                if not isinstance(e, dict):
                    continue
                if not isinstance(e.get("title"), str) or not isinstance(e.get("description"), str):
                    continue
                etype = e.get("type", "general")
                if etype not in valid_types:
                    etype = "general"
                valid.append({
                    "title": e["title"],
                    "description": e["description"],
                    "affected_countries": e.get("affected_countries", []) if isinstance(e.get("affected_countries"), list) else [],
                    "relation_changes": e.get("relation_changes", {}) if isinstance(e.get("relation_changes"), dict) else {},
                    "type": etype,
                    "stability_impact": max(-30, min(10, int(e.get("stability_impact", 0)))) if isinstance(e.get("stability_impact"), (int, float)) else 0,
                    "economy_impact": max(-0.08, min(0.05, float(e.get("economy_impact", 0.0)))) if isinstance(e.get("economy_impact"), (int, float)) else 0.0,
                })
            return valid
    except Exception as exc:
        logger.warning("Events JSON parse failed (%s). Raw: %.200s", exc, raw)
    return []


async def generate_turn_summary(
    player_country: dict,
    year: int,
    month: int,
    recent_actions: list[dict],
    recent_world_events: list[dict],
    player_state: dict,
    config: AiConfig,
) -> AsyncGenerator[str, None]:
    actions_text = "\n".join(
        f"- Tour {a.get('month', '?')}/{a.get('year', year)}: {a.get('action', a.get('consequences', ''))}"
        for a in recent_actions[-5:]
    ) or "Aucune action récente."

    events_text = "\n".join(
        f"- {e.get('title', '')} ({e.get('type', 'général')}): {e.get('description', '')}"
        for e in recent_world_events[-6:]
    ) or "Aucun événement mondial."

    stability = player_state.get("stability", 50)
    at_war = player_state.get("at_war_with", [])

    system = f"""Tu es le chroniqueur officiel de Phos, un jeu de simulation géopolitique.
Rédige un résumé narratif immersif et journalistique des derniers tours de jeu pour {player_country['name']}.
Nous sommes en {_format_date(year, month)}.

État actuel :
- Stabilité : {stability}/100
- En guerre avec : {', '.join(at_war) if at_war else 'personne'}
- PIB modifier : {player_state.get('economy_modifier', 1.0):.2f}x

Actions du joueur (récentes) :
{actions_text}

Événements mondiaux récents :
{events_text}

Rédige un résumé narratif en 3-4 paragraphes, dans le style d'un rapport diplomatique ou d'une analyse géopolitique.
Commence par une phrase d'accroche forte. Mentionne les événements marquants, l'évolution du pays, les défis et opportunités.
Réponds en français uniquement."""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Rédige le résumé des derniers tours."},
    ]
    async for chunk in stream_chat(messages, config):
        yield chunk


async def analyze_diplomatic_exchange(
    player_country: dict,
    target_country: dict,
    player_message: str,
    country_response: str,
    config: AiConfig,
) -> dict:
    system = f"""Tu es l'arbitre de Phos. Analyse cet échange diplomatique.

Pays joueur : {player_country['name']} | Pays cible : {target_country['name']}

Message du joueur : {player_message}
Réponse de {target_country['name']} : {country_response}

Un accord concret a-t-il été conclu ? (traité commercial, alliance, accord militaire, aide humanitaire, accord culturel, etc.)
Réponds UNIQUEMENT en JSON valide, sans texte autour :
{{
  "agreement_reached": true/false,
  "agreement_type": "commercial|militaire|diplomatique|culturel|humanitaire|null",
  "summary": "Courte description de l'accord en français, ou null",
  "relation_delta": int_entre_moins10_et_plus20,
  "economy_delta": float_entre_moins0.02_et_plus0.03,
  "domestic_events": []
}}

Règles :
- agreement_reached=true UNIQUEMENT si les deux parties ont explicitement accepté un accord précis
- relation_delta : +5 à +15 pour accord accepté, -5 à -10 pour refus ferme, 0 si discussion neutre
- economy_delta : 0.01 à 0.02 pour accord commercial, 0 sinon
- domestic_events : liste vide sauf pour accord majeur (alliance formelle, grand traité), max 1 événement"""

    messages = [{"role": "system", "content": system}, {"role": "user", "content": "Analyse."}]
    raw = await chat(messages, config)
    return _parse_diplomatic_effect(raw)


def _parse_diplomatic_effect(raw: str) -> dict:
    import json, re
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            if not isinstance(data, dict):
                raise ValueError("not a dict")
            domestic = []
            for de in (data.get("domestic_events") or [])[:1]:
                if isinstance(de, dict) and de.get("title"):
                    domestic.append({
                        "title": str(de.get("title", "")),
                        "description": str(de.get("description", "")),
                        "type": str(de.get("type", "diplomatic")),
                        "severity": max(1, min(3, int(de.get("severity", 1)))),
                        "stability_impact": max(-15, min(10, int(de.get("stability_impact", 0)))),
                    })
            agreement_reached = bool(data.get("agreement_reached", False))
            agreement_type = data.get("agreement_type") if isinstance(data.get("agreement_type"), str) else None
            if agreement_type == "null":
                agreement_type = None
            return {
                "agreement_reached": agreement_reached,
                "agreement_type": agreement_type,
                "summary": str(data["summary"]) if isinstance(data.get("summary"), str) else None,
                "relation_delta": max(-10, min(20, int(data.get("relation_delta", 0)))),
                "economy_delta": max(-0.02, min(0.03, float(data.get("economy_delta", 0.0)))),
                "domestic_events": domestic,
            }
    except Exception as exc:
        logger.warning("Diplomatic effect JSON parse failed (%s). Raw: %.200s", exc, raw)
    return {
        "agreement_reached": False, "agreement_type": None, "summary": None,
        "relation_delta": 0, "economy_delta": 0.0, "domestic_events": [],
    }


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
