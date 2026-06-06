import json
import os
import uuid
from typing import Dict, Optional
from datetime import datetime

from app.models.game import GameSession, ActionResult, WorldEvent, DiplomaticMessage
from app.services.scenario_loader import load_scenario

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sessions")
MAX_SNAPSHOTS = 10

_sessions: Dict[str, GameSession] = {}


# ─── Persistance ────────────────────────────────────────────────────────────────

def _session_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def _snapshots_dir(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, session_id)


def _save_session(session: GameSession):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    data = session.model_dump(mode="json")
    with open(_session_path(session.id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _save_snapshot(session: GameSession):
    """Snapshot du tour courant, les MAX_SNAPSHOTS derniers sont gardés."""
    snap_dir = _snapshots_dir(session.id)
    os.makedirs(snap_dir, exist_ok=True)
    path = os.path.join(snap_dir, f"turn_{session.turn:05d}.json")
    data = session.model_dump(mode="json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # Nettoyer les vieux snapshots
    snaps = sorted(f for f in os.listdir(snap_dir) if f.endswith(".json"))
    for old in snaps[:-MAX_SNAPSHOTS]:
        os.remove(os.path.join(snap_dir, old))


def _load_session_from_disk(session_id: str) -> Optional[GameSession]:
    path = _session_path(session_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return GameSession(**data)


# ─── API publique ───────────────────────────────────────────────────────────────

def create_session(scenario_id: str, player_country_id: str) -> GameSession:
    scenario = load_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Scénario introuvable : {scenario_id}")
    if player_country_id not in scenario.countries:
        raise ValueError(f"Pays introuvable dans le scénario : {player_country_id}")

    country_states: Dict[str, dict] = {}
    for cid, country in scenario.countries.items():
        country_states[cid] = {
            "stability": 50,
            "economy_modifier": 1.0,
            "military_modifier": 1.0,
            "relations": dict(country.relations),
            "at_war_with": [],
            "sanctions_by": [],
            "active_events": [],
        }

    initial_events = [
        WorldEvent(
            title=e.title,
            description=e.description,
            affected_countries=e.affected_countries,
            year=e.year,
            month=e.month,
        )
        for e in scenario.initial_events
    ]

    session = GameSession(
        scenario_id=scenario_id,
        player_country_id=player_country_id,
        year=scenario.start_year,
        month=scenario.start_month,
        country_states=country_states,
        world_events=initial_events,
    )
    _sessions[session.id] = session
    _save_session(session)
    _save_snapshot(session)
    return session


def get_session(session_id: str) -> Optional[GameSession]:
    if session_id not in _sessions:
        # Tenter de charger depuis le disque
        session = _load_session_from_disk(session_id)
        if session:
            _sessions[session_id] = session
    return _sessions.get(session_id)


def get_game_state(session_id: str) -> Optional[dict]:
    session = get_session(session_id)
    if not session:
        return None
    scenario = load_scenario(session.scenario_id)
    if not scenario:
        return None

    player_country = scenario.countries.get(session.player_country_id)
    player_state = session.country_states.get(session.player_country_id, {})

    return {
        "session_id": session.id,
        "scenario_id": session.scenario_id,
        "year": session.year,
        "month": session.month,
        "turn": session.turn,
        "player_country": _merge_country(player_country, player_state),
        "countries": {
            cid: _merge_country(scenario.countries.get(cid), state)
            for cid, state in session.country_states.items()
        },
        "alliances": {k: v.model_dump() for k, v in scenario.alliances.items()},
        "recent_events": [e.model_dump(mode="json") for e in session.world_events[-10:]],
        "domestic_events": [e.model_dump(mode="json") for e in session.domestic_events[-20:]],
        "map_pois": [p.model_dump(mode="json") for p in session.map_pois],
        "diplomatic_history": [m.model_dump(mode="json") for m in session.diplomatic_history[-20:]],
        "action_history": [a.model_dump(mode="json") for a in session.action_history[-10:]],
        "pending_actions": [a.model_dump(mode="json") for a in session.pending_actions],
    }


def apply_action_result(session_id: str, result: ActionResult):
    session = get_session(session_id)
    if not session:
        return
    session.action_history.append(result)
    _apply_relation_changes(session, result.relation_changes)
    for event in result.world_events:
        session.world_events.append(event)
    session.updated_at = datetime.utcnow()
    _save_session(session)


def queue_action(session_id: str, content: str) -> list:
    from app.models.game import PendingAction
    session = get_session(session_id)
    if not session:
        raise ValueError("Session introuvable")
    session.pending_actions.append(PendingAction(content=content))
    session.updated_at = datetime.utcnow()
    _save_session(session)
    return [a.model_dump(mode="json") for a in session.pending_actions]


def remove_queued_action(session_id: str, index: int) -> list:
    session = get_session(session_id)
    if not session:
        raise ValueError("Session introuvable")
    if 0 <= index < len(session.pending_actions):
        session.pending_actions.pop(index)
        session.updated_at = datetime.utcnow()
        _save_session(session)
    return [a.model_dump(mode="json") for a in session.pending_actions]


def apply_simulation_month(session: GameSession, action_result: dict | None, events: list):
    """Apply one month's changes to session state. Save after each month."""
    from app.models.game import ActionResult, WorldEvent

    session.month += 1
    if session.month > 12:
        session.month = 1
        session.year += 1
    session.turn += 1

    # Apply world events
    for e in events:
        event = WorldEvent(
            title=e.get("title", "Événement mondial"),
            description=e.get("description", ""),
            affected_countries=e.get("affected_countries", []),
            relation_changes=e.get("relation_changes", {}),
            year=session.year,
            month=session.month,
        )
        session.world_events.append(event)
        _apply_relation_changes(session, event.relation_changes)

    # Apply action result (not stored in history — consumed by game master)
    if action_result:
        result = ActionResult(
            action=action_result["action"],
            consequences=action_result["narrative"],
            relation_changes=action_result.get("relation_changes", {}),
            year=session.year,
            month=session.month,
        )
        _apply_relation_changes(session, result.relation_changes)

        # Apply stability and economy deltas
        player_state = session.country_states.get(session.player_country_id, {})
        stab = player_state.get("stability", 50) + action_result.get("stability_delta", 0)
        player_state["stability"] = max(0, min(100, stab))
        eco = player_state.get("economy_modifier", 1.0) * (1 + action_result.get("economy_delta", 0.0))
        player_state["economy_modifier"] = round(eco, 4)
        session.country_states[session.player_country_id] = player_state

        # Apply domestic events from Game Master
        for de_data in action_result.get("domestic_events", []):
            from app.models.game import DomesticEvent
            de = DomesticEvent(
                title=de_data["title"],
                description=de_data["description"],
                type=de_data.get("type", "social"),
                severity=de_data.get("severity", 1),
                stability_impact=de_data.get("stability_impact", 0),
                year=session.year,
                month=session.month,
            )
            session.domestic_events.append(de)
            # Apply domestic stability impact
            ps = session.country_states.get(session.player_country_id, {})
            s = ps.get("stability", 50) + de_data.get("stability_impact", 0)
            ps["stability"] = max(0, min(100, s))
            session.country_states[session.player_country_id] = ps

        # Apply map POI from Game Master
        poi_data = action_result.get("map_poi")
        if poi_data and action_result.get("applicable", True):
            from app.models.game import MapPOI
            poi = MapPOI(
                name=poi_data["name"],
                type=poi_data["type"],
                country_id=session.player_country_id,
                coordinates=poi_data["coordinates"],
                icon=poi_data.get("icon", "📍"),
                year=session.year,
                month=session.month,
            )
            session.map_pois.append(poi)

    _simulate_economic_tick(session)
    session.updated_at = datetime.utcnow()
    _save_session(session)


def add_diplomatic_message(session_id: str, msg: DiplomaticMessage):
    session = get_session(session_id)
    if not session:
        return
    session.diplomatic_history.append(msg)
    session.updated_at = datetime.utcnow()
    _save_session(session)


def advance_turn(session_id: str, events_json: str | None = None) -> dict:
    session = get_session(session_id)
    if not session:
        raise ValueError("Session introuvable")

    session.month += 1
    if session.month > 12:
        session.month = 1
        session.year += 1
    session.turn += 1

    if events_json:
        try:
            events_data = json.loads(events_json)
            for e in events_data:
                event = WorldEvent(
                    title=e.get("title", "Événement mondial"),
                    description=e.get("description", ""),
                    affected_countries=e.get("affected_countries", []),
                    year=session.year,
                    month=session.month,
                    triggered_by_player=False,
                )
                session.world_events.append(event)
        except (json.JSONDecodeError, KeyError):
            pass

    _simulate_economic_tick(session)
    session.updated_at = datetime.utcnow()
    _save_session(session)
    _save_snapshot(session)

    return {
        "year": session.year,
        "month": session.month,
        "turn": session.turn,
        "new_events": [e.model_dump(mode="json") for e in session.world_events[-5:]],
    }


def restore_snapshot(session_id: str, turn: int) -> GameSession:
    snap_dir = _snapshots_dir(session_id)
    path = os.path.join(snap_dir, f"turn_{turn:05d}.json")
    if not os.path.exists(path):
        raise ValueError(f"Snapshot du tour {turn} introuvable")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    session = GameSession(**data)
    _sessions[session_id] = session
    _save_session(session)
    return session


def list_snapshots(session_id: str) -> list[dict]:
    snap_dir = _snapshots_dir(session_id)
    if not os.path.exists(snap_dir):
        return []
    result = []
    for filename in sorted(os.listdir(snap_dir), reverse=True):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(snap_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        result.append({
            "turn": data["turn"],
            "year": data["year"],
            "month": data["month"],
            "saved_at": data["updated_at"],
        })
    return result


def delete_session(session_id: str) -> bool:
    _sessions.pop(session_id, None)
    path = _session_path(session_id)
    deleted = False
    if os.path.exists(path):
        os.remove(path)
        deleted = True
    snap_dir = _snapshots_dir(session_id)
    if os.path.exists(snap_dir):
        import shutil
        shutil.rmtree(snap_dir)
    return deleted


def get_diplomatic_history_with(session_id: str, target_country_id: str) -> list[dict]:
    session = get_session(session_id)
    if not session:
        return []
    return [
        {
            "player": msg.content if msg.from_country == session.player_country_id else "",
            "response": msg.response or "",
        }
        for msg in session.diplomatic_history
        if (msg.from_country == session.player_country_id and msg.to_country == target_country_id)
        or (msg.from_country == target_country_id and msg.to_country == session.player_country_id)
    ]


def list_sessions() -> list[dict]:
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    result = []
    for filename in os.listdir(SESSIONS_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(SESSIONS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            scenario = load_scenario(data["scenario_id"])
            country = scenario.countries.get(data["player_country_id"]) if scenario else None
            result.append({
                "id": data["id"],
                "scenario_id": data["scenario_id"],
                "scenario_name": scenario.name if scenario else data["scenario_id"],
                "player_country_id": data["player_country_id"],
                "player_country_name": country.name if country else data["player_country_id"],
                "player_country_flag": country.flag if country else "",
                "year": data["year"],
                "month": data["month"],
                "turn": data["turn"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
            })
        except Exception:
            continue
    result.sort(key=lambda x: x["updated_at"], reverse=True)
    return result


# ─── Internals ──────────────────────────────────────────────────────────────────

def _merge_country(country, state: dict) -> dict:
    if not country:
        return {}
    d = country.model_dump()
    if state:
        d["stability"] = state.get("stability", 50)
        d["economy_modifier"] = state.get("economy_modifier", 1.0)
        d["military_modifier"] = state.get("military_modifier", 1.0)
        d["relations"] = state.get("relations", d.get("relations", {}))
        d["at_war_with"] = state.get("at_war_with", [])
        d["sanctions_by"] = state.get("sanctions_by", [])
        d["active_events"] = state.get("active_events", [])
    return d


def _apply_relation_changes(session: GameSession, changes: Dict[str, Dict[str, int]]):
    for country_id, deltas in changes.items():
        if country_id in session.country_states:
            for other_id, delta in deltas.items():
                rel = session.country_states[country_id].get("relations", {})
                current = rel.get(other_id, 0)
                rel[other_id] = max(-100, min(100, current + delta))
                session.country_states[country_id]["relations"] = rel


def _simulate_economic_tick(session: GameSession):
    scenario = load_scenario(session.scenario_id)
    if not scenario:
        return
    for cid, state in session.country_states.items():
        country = scenario.countries.get(cid)
        if not country or not country.economy:
            continue
        growth = country.economy.gdp_growth / 100 / 12
        state["economy_modifier"] = round(state.get("economy_modifier", 1.0) * (1 + growth), 4)
