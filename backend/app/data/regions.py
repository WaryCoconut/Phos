"""Region registry loaded from Natural Earth 50m admin-1 data (294 regions, 9 countries)."""
import json
import os
from typing import Optional

_META_PATH = os.path.join(os.path.dirname(__file__), "regions_meta.json")

_REGIONS: dict[str, dict] = {}
_BY_COUNTRY: dict[str, list] = {}
_LOADED = False

SUPPORTED_COUNTRIES = {"AUS", "BRA", "CAN", "CHN", "IND", "IDN", "RUS", "ZAF", "USA"}


def _load():
    global _LOADED
    if _LOADED:
        return
    with open(_META_PATH, encoding="utf-8") as f:
        data = json.load(f)
    for code, region in data.items():
        entry = {**region, "adm1_code": code}
        _REGIONS[code] = entry
        _BY_COUNTRY.setdefault(region["country_id"], []).append(entry)
    _LOADED = True


def get_region(adm1_code: str) -> Optional[dict]:
    _load()
    return _REGIONS.get(adm1_code)


def get_country_regions(country_id: str) -> list[dict]:
    _load()
    return _BY_COUNTRY.get(country_id, [])


def all_regions() -> dict[str, dict]:
    _load()
    return _REGIONS


def generate_country_id(parent_id: str, region_name: str, existing_ids: set) -> str:
    """Generate a unique 3-char country ID for an independent region."""
    words = [w for w in region_name.split() if w.isalpha()]
    if len(words) >= 2:
        base = (parent_id[0] + words[0][0] + words[1][0]).upper()
    elif words:
        base = (parent_id[0] + words[0][:2]).upper()
    else:
        base = parent_id[0] + "XX"

    if base not in existing_ids:
        return base
    for suffix in "ABCDEFGHIJ":
        cid = base[:2] + suffix
        if cid not in existing_ids:
            return cid
    return "X" + parent_id[0] + str(abs(hash(region_name)) % 9)
