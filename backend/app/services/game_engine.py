import json
import os
import tempfile
import uuid
from typing import Dict, Optional
from datetime import datetime

from app.models.game import GameSession, ActionResult, WorldEvent, DiplomaticMessage, Treaty, PendingConsequence
from app.services.scenario_loader import load_scenario

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sessions")
MAX_SNAPSHOTS = 10

_sessions: Dict[str, GameSession] = {}


# ─── Persistance ────────────────────────────────────────────────────────────────

def _session_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def _snapshots_dir(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, session_id)


def _atomic_write(path: str, data: dict):
    """Write JSON atomically via temp file + os.replace to avoid corruption on crash."""
    dir_ = os.path.dirname(path) or '.'
    os.makedirs(dir_, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=dir_, suffix='.tmp', delete=False, encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        tmp = f.name
    os.replace(tmp, path)


def _save_session(session: GameSession):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    _atomic_write(_session_path(session.id), session.model_dump(mode="json"))


def _save_snapshot(session: GameSession):
    """Snapshot du tour courant, les MAX_SNAPSHOTS derniers sont gardés."""
    snap_dir = _snapshots_dir(session.id)
    os.makedirs(snap_dir, exist_ok=True)
    path = os.path.join(snap_dir, f"turn_{session.turn:05d}.json")
    _atomic_write(path, session.model_dump(mode="json"))

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
            "stability": getattr(country, "initial_stability", 50),
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

    # Merge scenario countries
    countries: dict = {
        cid: _merge_country(scenario.countries.get(cid), state)
        for cid, state in session.country_states.items()
    }
    # Overlay dynamic countries (created from independent regions)
    for cid, data in session.dynamic_countries.items():
        dyn_state = session.country_states.get(cid, {})
        merged = dict(data)
        merged["stability"] = dyn_state.get("stability", merged.get("stability", 45))
        merged["economy_modifier"] = dyn_state.get("economy_modifier", 1.0)
        merged["military_modifier"] = dyn_state.get("military_modifier", 1.0)
        merged["relations"] = dyn_state.get("relations", merged.get("relations", {}))
        merged["at_war_with"] = dyn_state.get("at_war_with", [])
        merged["sanctions_by"] = dyn_state.get("sanctions_by", [])
        merged["active_events"] = dyn_state.get("active_events", [])
        countries[cid] = merged

    return {
        "session_id": session.id,
        "scenario_id": session.scenario_id,
        "year": session.year,
        "month": session.month,
        "turn": session.turn,
        "player_country": _merge_country(player_country, player_state),
        "countries": countries,
        "alliances": {k: v.model_dump() for k, v in scenario.alliances.items()},
        "recent_events": [e.model_dump(mode="json") for e in session.world_events[-10:]],
        "domestic_events": [e.model_dump(mode="json") for e in session.domestic_events[-20:]],
        "map_pois": [p.model_dump(mode="json") for p in session.map_pois],
        "diplomatic_history": [m.model_dump(mode="json") for m in session.diplomatic_history[-20:]],
        "action_history": [a.model_dump(mode="json") for a in session.action_history[-10:]],
        "pending_actions": [a.model_dump(mode="json") for a in session.pending_actions],
        "region_state": session.region_state,
        "treaties": [t.model_dump(mode="json") for t in session.treaties],
        "custom_map_id": scenario.custom_map_id,
        "custom_map_feature_id_property": scenario.custom_map_feature_id_property,
        "initial_territories": scenario.initial_territories,
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


def apply_action_result_to_session(session: GameSession, action_result: dict, save: bool = True, scale: float = 1.0):
    """Apply one action's deltas to session state without advancing the month."""
    from app.models.game import ActionResult, DomesticEvent, MapPOI

    result = ActionResult(
        action=action_result["action"],
        consequences=action_result["narrative"],
        relation_changes=action_result.get("relation_changes", {}),
        year=session.year,
        month=session.month,
    )
    _apply_relation_changes(session, result.relation_changes)

    player_state = session.country_states.get(session.player_country_id, {})
    stab = player_state.get("stability", 50) + action_result.get("stability_delta", 0) * scale
    player_state["stability"] = max(0, min(100, round(stab)))
    eco = player_state.get("economy_modifier", 1.0) * (1 + action_result.get("economy_delta", 0.0) * scale)
    player_state["economy_modifier"] = round(eco, 4)
    session.country_states[session.player_country_id] = player_state

    for de_data in action_result.get("domestic_events", []):
        if not isinstance(de_data, dict) or not de_data.get("title"):
            continue
        de = DomesticEvent(
            title=de_data["title"],
            description=de_data.get("description", ""),
            type=de_data.get("type", "social"),
            severity=max(1, min(3, int(de_data.get("severity", 1)))),
            stability_impact=max(-15, min(10, int(de_data.get("stability_impact", 0)))),
            year=session.year,
            month=session.month,
        )
        session.domestic_events.append(de)
        ps = session.country_states.get(session.player_country_id, {})
        s = ps.get("stability", 50) + de_data.get("stability_impact", 0)
        ps["stability"] = max(0, min(100, round(s)))
        session.country_states[session.player_country_id] = ps

    stat_deltas = action_result.get("stat_deltas", {})
    if stat_deltas:
        scenario = load_scenario(session.scenario_id)
        base_country = scenario.countries.get(session.player_country_id) if scenario else None
        base_ns = (base_country.national_stats.model_dump() if base_country and base_country.national_stats
                   else {"sovereignty": 50, "food_autonomy": 50, "energy_autonomy": 50, "economic_independence": 50})
        ps = session.country_states.get(session.player_country_id, {})
        current_ns = ps.get("national_stats") or dict(base_ns)
        for key in ("sovereignty", "food_autonomy", "energy_autonomy", "economic_independence"):
            delta = stat_deltas.get(key, 0)
            if delta:
                current_ns[key] = round(max(0, min(120, current_ns.get(key, base_ns.get(key, 50)) + delta)), 1)
        ps["national_stats"] = current_ns
        session.country_states[session.player_country_id] = ps

    poi_data = action_result.get("map_poi")
    if poi_data and action_result.get("applicable", True) and isinstance(poi_data, dict) and poi_data.get("name"):
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

    for fe_data in action_result.get("future_events", [])[:2]:
        if not isinstance(fe_data, dict) or not fe_data.get("title"):
            continue
        months_ahead = max(1, int(fe_data.get("months_ahead", 1)))
        trig_month = session.month + months_ahead
        trig_year = session.year + (trig_month - 1) // 12
        trig_month = ((trig_month - 1) % 12) + 1
        session.pending_consequences.append(PendingConsequence(
            trigger_year=trig_year,
            trigger_month=trig_month,
            source_action=action_result.get("action", ""),
            title=str(fe_data["title"]),
            description=str(fe_data.get("description", "")),
            event_type=str(fe_data.get("type", "consequence")),
            stability_impact=max(-20, min(15, int(fe_data.get("stability_impact", 0)))),
            economy_impact=max(-0.05, min(0.05, float(fe_data.get("economy_impact", 0.0)))),
        ))

    session.updated_at = datetime.utcnow()
    if save:
        _save_session(session)


def apply_simulation_unit(
    session: GameSession,
    action_result: dict | None,
    events: list,
    days: int = 30,
    scale: float = 1.0,
):
    """Advance time by `days`, apply world events + optional action, war, treaties, economy, pending consequences. Saves."""
    from app.models.game import WorldEvent

    # Advance day/month/year
    day = getattr(session, 'day', 1) + days
    while day > 30:
        day -= 30
        session.month += 1
        if session.month > 12:
            session.month = 1
            session.year += 1
    session.day = day
    session.turn += 1

    player_id = session.player_country_id
    for e in events:
        event = WorldEvent(
            title=e.get("title", "Événement mondial"),
            description=e.get("description", ""),
            affected_countries=e.get("affected_countries", []),
            relation_changes=e.get("relation_changes", {}),
            stability_impact=max(-30, min(10, int(e.get("stability_impact", 0)))),
            economy_impact=max(-0.08, min(0.05, float(e.get("economy_impact", 0.0)))),
            year=session.year,
            month=session.month,
            day=session.day,
            type=e.get("type", "general"),
        )
        session.world_events.append(event)
        _apply_relation_changes(session, event.relation_changes)
        # Apply direct stability/economy impacts if the player is affected
        if player_id in event.affected_countries:
            if event.stability_impact:
                ps = session.country_states.get(player_id, {})
                ps["stability"] = max(0, min(100, round(ps.get("stability", 50) + event.stability_impact)))
                session.country_states[player_id] = ps
            if event.economy_impact:
                ps = session.country_states.get(player_id, {})
                ps["economy_modifier"] = round(ps.get("economy_modifier", 1.0) * (1 + event.economy_impact), 4)
                session.country_states[player_id] = ps

    if action_result:
        apply_action_result_to_session(session, action_result, save=False, scale=scale)

    _fire_pending_consequences(session)
    _check_stability_crisis(session)
    _progress_war_invasions(session)
    _apply_treaty_effects(session)
    _simulate_economic_tick(session, scale=scale)
    session.updated_at = datetime.utcnow()
    _save_session(session)


def apply_simulation_month(session: GameSession, action_result: dict | None, events: list):
    """Backward-compat wrapper — advance by 30 days (full month)."""
    apply_simulation_unit(session, action_result, events, days=30, scale=1.0)


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


def add_treaty(session_id: str, treaty: Treaty) -> None:
    """Persist a new treaty, skipping duplicates of the same type between the same pair."""
    session = get_session(session_id)
    if not session:
        return
    pair = {treaty.country_a, treaty.country_b}
    for existing in session.treaties:
        if existing.type == treaty.type and {existing.country_a, existing.country_b} == pair:
            return
    session.treaties.append(treaty)
    session.updated_at = datetime.utcnow()
    _save_session(session)


def _apply_treaty_effects(session: GameSession) -> None:
    """Apply monthly economy and relation bonuses from active treaties."""
    player_id = session.player_country_id
    for treaty in session.treaties:
        involves_player = treaty.country_a == player_id or treaty.country_b == player_id
        if treaty.economy_bonus and involves_player:
            ps = session.country_states.get(player_id, {})
            ps["economy_modifier"] = round(ps.get("economy_modifier", 1.0) * (1 + treaty.economy_bonus / 12), 6)
            session.country_states[player_id] = ps

        if treaty.relation_bonus:
            other = treaty.country_b if treaty.country_a == player_id else treaty.country_a
            for cid, oid in [(player_id, other), (other, player_id)]:
                if cid in session.country_states:
                    rel = session.country_states[cid].get("relations", {})
                    rel[oid] = min(100, rel.get(oid, 0) + treaty.relation_bonus)
                    session.country_states[cid]["relations"] = rel


def apply_diplomatic_effects(
    session_id: str,
    player_country_id: str,
    target_country_id: str,
    effect: dict,
) -> None:
    session = get_session(session_id)
    if not session:
        return

    rel_delta = effect.get("relation_delta", 0)
    if rel_delta:
        for cid, oid in [(player_country_id, target_country_id), (target_country_id, player_country_id)]:
            if cid in session.country_states:
                rel = session.country_states[cid].get("relations", {})
                current = rel.get(oid, 0)
                rel[oid] = max(-100, min(100, current + rel_delta))
                session.country_states[cid]["relations"] = rel

    eco_delta = effect.get("economy_delta", 0.0)
    if eco_delta:
        ps = session.country_states.get(player_country_id, {})
        eco = ps.get("economy_modifier", 1.0) * (1 + eco_delta)
        ps["economy_modifier"] = round(eco, 4)
        session.country_states[player_country_id] = ps

    for de_data in effect.get("domestic_events", [])[:1]:
        if isinstance(de_data, dict) and de_data.get("title"):
            from app.models.game import DomesticEvent
            de = DomesticEvent(
                title=de_data["title"],
                description=de_data.get("description", ""),
                type=de_data.get("type", "diplomatic"),
                severity=max(1, min(3, int(de_data.get("severity", 1)))),
                stability_impact=max(-15, min(10, int(de_data.get("stability_impact", 0)))),
                year=session.year,
                month=session.month,
            )
            session.domestic_events.append(de)
            ps = session.country_states.get(player_country_id, {})
            s = ps.get("stability", 50) + de_data.get("stability_impact", 0)
            ps["stability"] = max(0, min(100, s))
            session.country_states[player_country_id] = ps

    # Persist treaty when an agreement is reached
    if effect.get("agreement_reached") and effect.get("agreement_type"):
        agreement_type = effect["agreement_type"]
        economy_bonus = 0.005 if agreement_type == "commercial" else 0.0
        relation_bonus = 1 if agreement_type in ("diplomatique", "militaire") else 0
        treaty = Treaty(
            type=agreement_type,
            country_a=player_country_id,
            country_b=target_country_id,
            summary=effect.get("summary") or f"Accord {agreement_type}",
            year=session.year,
            month=session.month,
            economy_bonus=economy_bonus,
            relation_bonus=relation_bonus,
        )
        add_treaty(session.id, treaty)

    session.updated_at = datetime.utcnow()
    _save_session(session)


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
        # Overlay dynamic national_stats, sectors, equipment if evolved during play
        if state.get("national_stats"):
            d["national_stats"] = state["national_stats"]
        if state.get("sectors") and d.get("economy"):
            d["economy"]["sectors"] = state["sectors"]
        if state.get("equipment") and d.get("military"):
            d["military"]["equipment"] = state["equipment"]
    return d


def _apply_relation_changes(session: GameSession, changes: Dict[str, Dict[str, int]]):
    for country_id, deltas in changes.items():
        if country_id in session.country_states:
            for other_id, delta in deltas.items():
                rel = session.country_states[country_id].get("relations", {})
                current = rel.get(other_id, 0)
                rel[other_id] = max(-100, min(100, current + delta))
                session.country_states[country_id]["relations"] = rel


def _simulate_economic_tick(session: GameSession, scale: float = 1.0):
    scenario = load_scenario(session.scenario_id)
    if not scenario:
        return
    for cid, state in session.country_states.items():
        country = scenario.countries.get(cid)
        if not country or not country.economy:
            continue
        growth = country.economy.gdp_growth / 100 / 12 * scale
        state["economy_modifier"] = round(state.get("economy_modifier", 1.0) * (1 + growth), 4)


def _fire_pending_consequences(session: GameSession) -> None:
    """Fire any PendingConsequences whose trigger date has been reached."""
    if not session.pending_consequences:
        return

    fired_ids: list[str] = []
    for pc in session.pending_consequences:
        if (session.year, session.month) >= (pc.trigger_year, pc.trigger_month):
            from app.models.game import WorldEvent
            session.world_events.append(WorldEvent(
                title=pc.title,
                description=pc.description,
                affected_countries=[session.player_country_id],
                year=session.year,
                month=session.month,
                type=pc.event_type,
                triggered_by_player=True,
            ))
            if pc.stability_impact:
                ps = session.country_states.get(session.player_country_id, {})
                ps["stability"] = max(0, min(100, round(ps.get("stability", 50) + pc.stability_impact)))
                session.country_states[session.player_country_id] = ps
            if pc.economy_impact:
                ps = session.country_states.get(session.player_country_id, {})
                ps["economy_modifier"] = round(ps.get("economy_modifier", 1.0) * (1 + pc.economy_impact), 4)
                session.country_states[session.player_country_id] = ps
            fired_ids.append(pc.id)

    session.pending_consequences = [pc for pc in session.pending_consequences if pc.id not in fired_ids]


def _check_stability_crisis(session: GameSession) -> None:
    """Trigger a coup/crisis event if stability falls below 10."""
    import random
    ps = session.country_states.get(session.player_country_id, {})
    if ps.get("stability", 50) >= 10:
        return
    if random.random() > 0.6:
        return
    from app.models.game import WorldEvent, DomesticEvent
    session.domestic_events.append(DomesticEvent(
        title="Crise de gouvernance — Instabilité critique",
        description=(
            "La chute de la stabilité sous le seuil critique provoque une crise de gouvernance. "
            "Des factions militaires et civiles contestent l'autorité de l'État. "
            "Des mesures d'urgence doivent être prises immédiatement."
        ),
        type="military",
        severity=3,
        stability_impact=-10,
        year=session.year,
        month=session.month,
    ))
    ps["stability"] = max(0, round(ps.get("stability", 0)) - 10)
    session.country_states[session.player_country_id] = ps


# ─── Régions ────────────────────────────────────────────────────────────────────

def _ensure_region_state(session: GameSession) -> dict:
    if not isinstance(session.region_state, dict):
        session.region_state = {"occupied": {}, "independent": {}}
    session.region_state.setdefault("occupied", {})
    session.region_state.setdefault("independent", {})
    return session.region_state


def _get_military_power(session: GameSession, country_id: str) -> float:
    scenario = load_scenario(session.scenario_id)
    dyn = session.dynamic_countries.get(country_id)
    if dyn:
        base = float(dyn.get("military", {}).get("strength", 1))
    elif scenario:
        country = scenario.countries.get(country_id)
        base = float(country.military.strength) if country and country.military else 1.0
    else:
        return 1.0
    modifier = session.country_states.get(country_id, {}).get("military_modifier", 1.0)
    return base * modifier


def _trigger_alliance_defense(session: GameSession, attacker: str, defender: str) -> None:
    """When defender is invaded, allies in the same alliance react automatically."""
    scenario = load_scenario(session.scenario_id)
    if not scenario:
        return

    for alliance_id, alliance in scenario.alliances.items():
        if defender not in alliance.members:
            continue
        for ally_id in alliance.members:
            if ally_id in (defender, attacker):
                continue
            ally_state = session.country_states.get(ally_id)
            if not ally_state:
                continue

            # Degrade attacker relations with every alliance member
            rel = ally_state.get("relations", {})
            rel[attacker] = max(-100, rel.get(attacker, 0) - 15)
            ally_state["relations"] = rel
            session.country_states[ally_id] = ally_state

            # Close allies (relation ≥ 60) automatically enter the war
            if rel.get(defender, 0) >= 60 and attacker not in ally_state.get("at_war_with", []):
                ally_state.setdefault("at_war_with", []).append(attacker)
                session.country_states[ally_id] = ally_state
                atk_state = session.country_states.get(attacker, {})
                if ally_id not in atk_state.get("at_war_with", []):
                    atk_state.setdefault("at_war_with", []).append(ally_id)
                    session.country_states[attacker] = atk_state
                from app.models.game import WorldEvent as WE
                session.world_events.append(WE(
                    title=f"Défense collective ({alliance_id})",
                    description=(
                        f"{ally_id} active la clause de défense collective de l'alliance "
                        f"{alliance_id} et entre en guerre contre {attacker} aux côtés de {defender}."
                    ),
                    affected_countries=[ally_id, defender, attacker],
                    year=session.year,
                    month=session.month,
                ))


def _progress_war_invasions(session: GameSession):
    """Each month: warring sides may capture a region of the opponent (30 % chance)."""
    import random
    from app.data.regions import get_country_regions, SUPPORTED_COUNTRIES

    rs = _ensure_region_state(session)
    war_pairs: set[tuple] = set()
    for cid, state in session.country_states.items():
        for enemy in state.get("at_war_with", []):
            war_pairs.add(tuple(sorted([cid, enemy])))

    for (a_id, b_id) in war_pairs:
        if random.random() > 0.30:
            continue
        a_pow = _get_military_power(session, a_id)
        b_pow = _get_military_power(session, b_id)

        # Stronger side attacks
        if a_pow >= b_pow:
            attacker, defender = a_id, b_id
        else:
            attacker, defender = b_id, a_id

        if defender not in SUPPORTED_COUNTRIES:
            continue

        all_regions = get_country_regions(defender)
        free_regions = [
            r for r in all_regions
            if r["adm1_code"] not in rs["occupied"]
            and r["adm1_code"] not in rs["independent"]
        ]
        if not free_regions:
            continue

        region = random.choice(free_regions)
        rs["occupied"][region["adm1_code"]] = {
            "occupied_by": attacker,
            "country_id": defender,
            "region_name": region.get("name_fr") or region["name"],
        }
        from app.models.game import WorldEvent
        session.world_events.append(WorldEvent(
            title=f"Invasion : {region.get('name_fr') or region['name']}",
            description=(
                f"Les forces de {attacker} ont pris le contrôle de la région "
                f"{region.get('name_fr') or region['name']} ({defender})."
            ),
            affected_countries=[attacker, defender],
            year=session.year,
            month=session.month,
        ))
        _trigger_alliance_defense(session, attacker, defender)


def get_region_state(session_id: str) -> Optional[dict]:
    session = get_session(session_id)
    if not session:
        return None
    return _ensure_region_state(session)


def occupy_region(session_id: str, adm1_code: str, occupying_country_id: str) -> dict:
    """MJ manually occupies a region."""
    from app.data.regions import get_region
    session = get_session(session_id)
    if not session:
        raise ValueError("Session introuvable")
    region = get_region(adm1_code)
    if not region:
        raise ValueError(f"Région inconnue : {adm1_code}")

    rs = _ensure_region_state(session)
    rs["occupied"][adm1_code] = {
        "occupied_by": occupying_country_id,
        "country_id": region["country_id"],
        "region_name": region.get("name_fr") or region["name"],
    }
    session.updated_at = datetime.utcnow()
    _save_session(session)
    return rs


def liberate_region(session_id: str, adm1_code: str) -> dict:
    """Remove occupation from a region."""
    session = get_session(session_id)
    if not session:
        raise ValueError("Session introuvable")
    rs = _ensure_region_state(session)
    rs["occupied"].pop(adm1_code, None)
    session.updated_at = datetime.utcnow()
    _save_session(session)
    return rs


def declare_region_independent(
    session_id: str,
    adm1_code: str,
    new_country_name: str,
    new_country_flag: str = "🏳️",
) -> dict:
    """Create a new independent country from a region."""
    from app.data.regions import get_region, generate_country_id
    import random

    session = get_session(session_id)
    if not session:
        raise ValueError("Session introuvable")
    region = get_region(adm1_code)
    if not region:
        raise ValueError(f"Région inconnue : {adm1_code}")

    parent_id = region["country_id"]
    scenario = load_scenario(session.scenario_id)
    parent_sc = scenario.countries.get(parent_id) if scenario else None
    parent_state = session.country_states.get(parent_id, {})

    existing_ids = set(session.country_states.keys()) | set(session.dynamic_countries.keys())
    new_id = generate_country_id(parent_id, new_country_name, existing_ids)

    # Inherit ~15 % of parent's resources
    ratio = 0.15
    parent_gdp = (parent_sc.economy.gdp if parent_sc and parent_sc.economy else 100.0)
    parent_gdp *= parent_state.get("economy_modifier", 1.0)
    parent_pop = parent_sc.population if parent_sc else 50_000_000
    parent_mil = (parent_sc.military.strength if parent_sc and parent_sc.military else 3)

    # Inherit parent's relations, slightly degraded
    parent_rels = dict(parent_state.get("relations", parent_sc.relations if parent_sc else {}))
    new_relations = {k: max(-30, v - 20) for k, v in parent_rels.items() if k != new_id}
    new_relations[parent_id] = -40  # tense with former country

    REGION_COLORS = [
        "#7c3aed", "#be185d", "#0369a1", "#047857", "#b45309",
        "#9333ea", "#db2777", "#0284c7", "#059669", "#d97706",
    ]
    color = random.choice(REGION_COLORS)

    continent = parent_sc.continent if parent_sc else "Monde"

    new_country: dict = {
        "id": new_id,
        "name": new_country_name,
        "flag": new_country_flag,
        "capital": region.get("name_fr") or region["name"],
        "continent": continent,
        "population": int(parent_pop * ratio),
        "government_type": "transition",
        "ideology": "nationalisme",
        "leader": "Gouvernement provisoire",
        "alliances": [],
        "economy": {
            "gdp": round(parent_gdp * ratio, 2),
            "gdp_per_capita": int((parent_sc.economy.gdp_per_capita if parent_sc and parent_sc.economy else 5000) * 0.8),
            "gdp_growth": -1.5,
            "inflation": 8.0,
            "unemployment": 12.0,
            "debt_pct_gdp": 45.0,
            "currency": "XXX",
            "main_sectors": ["services", "industrie"],
            "sectors": {"agriculture": 15.0, "industrie": 35.0, "services": 50.0},
        },
        "military": {
            "strength": max(1, int(parent_mil * ratio)),
            "active_personnel": int((parent_sc.military.active_personnel if parent_sc and parent_sc.military else 50000) * ratio),
            "nuclear_weapons": False,
            "defense_budget_pct": 2.0,
            "equipment": {},
        },
        "national_stats": {
            "sovereignty": 40.0,
            "food_autonomy": 45.0,
            "energy_autonomy": 40.0,
            "economic_independence": 35.0,
        },
        "relations": new_relations,
        "personality_traits": ["jeune_état", "fragile", "nationaliste"],
        "description": (
            f"{new_country_name} est un État nouvellement indépendant issu de la région "
            f"{region.get('name_fr') or region['name']} ({parent_id}), en {session.year}."
        ),
        "color": color,
        "stability": 40,
        "economy_modifier": 1.0,
        "military_modifier": 1.0,
        "at_war_with": [],
        "sanctions_by": [],
        "active_events": [],
    }

    # Reduce parent's economy proportionally
    ps = session.country_states.setdefault(parent_id, {})
    ps["economy_modifier"] = round(ps.get("economy_modifier", 1.0) * (1 - ratio * 0.8), 4)
    ps["stability"] = max(0, ps.get("stability", 50) - 10)
    session.country_states[parent_id] = ps

    # Register new country
    session.dynamic_countries[new_id] = new_country
    session.country_states[new_id] = {
        "stability": 40,
        "economy_modifier": 1.0,
        "military_modifier": 1.0,
        "relations": new_relations,
        "at_war_with": [],
        "sanctions_by": [],
        "active_events": [],
    }

    # Mark region as independent
    rs = _ensure_region_state(session)
    rs["occupied"].pop(adm1_code, None)
    rs["independent"][adm1_code] = {
        "country_id": new_id,
        "parent_id": parent_id,
        "region_name": region.get("name_fr") or region["name"],
        "since_year": session.year,
    }

    from app.models.game import WorldEvent
    session.world_events.append(WorldEvent(
        title=f"Indépendance : {new_country_name}",
        description=(
            f"{new_country_name} déclare son indépendance depuis la région "
            f"{region.get('name_fr') or region['name']} ({parent_id})."
        ),
        affected_countries=[new_id, parent_id],
        year=session.year,
        month=session.month,
    ))

    session.updated_at = datetime.utcnow()
    _save_session(session)
    return {"new_country_id": new_id, "region_state": rs}


def reunify_region(session_id: str, adm1_code: str) -> dict:
    """Remove independence — region rejoins its parent country."""
    session = get_session(session_id)
    if not session:
        raise ValueError("Session introuvable")
    rs = _ensure_region_state(session)
    ind = rs["independent"].pop(adm1_code, None)
    if ind:
        cid = ind["country_id"]
        session.dynamic_countries.pop(cid, None)
        session.country_states.pop(cid, None)
    session.updated_at = datetime.utcnow()
    _save_session(session)
    return rs
