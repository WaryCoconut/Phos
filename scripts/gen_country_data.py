"""Injects national_stats, economy.sectors, and military.equipment into default_2016.json."""
import json, os, math

SCENARIO_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'data', 'scenarios', 'default_2016.json')

# ── national_stats explicit values ──────────────────────────────────────────
NATIONAL_STATS = {
    'USA': (97, 94, 87, 95),  'CHN': (92, 88, 72, 82),  'RUS': (93, 85, 96, 78),
    'DEU': (84, 82, 35, 76),  'FRA': (90, 78, 55, 72),  'GBR': (90, 62, 52, 78),
    'JPN': (82, 38, 12, 74),  'IND': (85, 82, 68, 72),  'BRA': (82, 95, 74, 68),
    'CAN': (87,118, 95, 78),  'AUS': (87,145, 92, 76),  'KOR': (76, 45, 18, 68),
    'MEX': (72, 72, 65, 58),  'IDN': (75, 85, 72, 60),  'SAU': (80, 22, 98, 72),
    'TUR': (76, 78, 28, 58),  'ITA': (78, 72, 22, 62),  'ESP': (76, 78, 32, 60),
    'ARG': (72,128, 55, 52),  'ZAF': (72, 78, 65, 55),  'IRN': (68, 72, 88, 58),
    'ISR': (82, 48, 35, 68),  'PRK': (60, 42, 55, 25),  'UKR': (60, 95, 48, 38),
    'POL': (78, 88, 45, 58),  'NLD': (80,145, 48, 65),  'CHE': (86, 52, 58, 72),
    'SWE': (84, 78, 68, 70),  'NOR': (88, 82, 98, 82),  'PAK': (60, 72, 42, 38),
    'NGA': (55, 72, 78, 42),  'EGY': (62, 48, 52, 38),  'VNM': (72, 95, 65, 52),
    'PHL': (62, 72, 35, 42),  'COL': (62, 82, 68, 45),  'VEN': (55, 52, 88, 42),
    'IRQ': (45, 42, 92, 35),  'SYR': (30, 55, 45, 22),  'ARE': (72, 18, 96, 68),
    'QAT': (72, 12, 99, 75),  'CUB': (60, 65, 45, 32),  'KAZ': (65, 72, 88, 52),
    'THA': (68,118, 45, 52),  'MYS': (68, 88, 62, 55),  'ETH': (55, 65, 42, 32),
    'GRC': (65, 68, 28, 38),  'CZE': (78, 82, 38, 55),  'HUN': (72, 78, 35, 48),
    'ROU': (68, 78, 42, 45),
    # 57 added countries
    'AFG': (35, 55, 38, 22),  'AGO': (52, 55, 82, 38),  'ARM': (55, 72, 28, 35),
    'AUT': (82, 85, 52, 68),  'AZE': (62, 72, 88, 45),  'BEL': (78, 92, 38, 62),
    'BGD': (55, 78, 28, 35),  'BGR': (68, 82, 38, 42),  'BLR': (55, 82, 35, 38),
    'BOL': (58, 72, 72, 38),  'CHL': (72, 92, 38, 58),  'CIV': (48, 68, 45, 32),
    'CMR': (48, 72, 52, 32),  'CRI': (68, 75, 38, 48),  'DNK': (82,145, 58, 68),
    'DOM': (55, 62, 28, 38),  'DZA': (62, 68, 88, 45),  'ECU': (58, 82, 72, 42),
    'EST': (75, 82, 38, 52),  'FIN': (82, 88, 48, 68),  'GEO': (55, 68, 28, 35),
    'GHA': (55, 72, 45, 35),  'GTM': (50, 72, 35, 32),  'HRV': (70, 78, 42, 48),
    'IRL': (80, 92, 35, 65),  'JOR': (55, 32, 22, 35),  'KEN': (52, 72, 35, 32),
    'KHM': (52, 78, 32, 28),  'KWT': (72, 12, 98, 72),  'LBN': (38, 32, 22, 32),
    'LBY': (35, 25, 92, 35),  'LKA': (58, 72, 28, 38),  'LTU': (72, 85, 35, 48),
    'LVA': (72, 82, 32, 48),  'MAR': (58, 62, 18, 38),  'MKD': (58, 72, 32, 38),
    'MMR': (55, 78, 45, 32),  'MNG': (55, 72, 65, 32),  'NZL': (84,162, 72, 72),
    'OMN': (65, 18, 92, 55),  'PAN': (62, 65, 28, 48),  'PER': (62, 82, 62, 48),
    'PRT': (72, 75, 28, 48),  'PRY': (55, 95, 72, 38),  'SDN': (42, 52, 55, 25),
    'SOM': (22, 32, 22, 15),  'SRB': (60, 82, 38, 40),  'SVK': (72, 78, 35, 52),
    'SVN': (75, 82, 38, 58),  'TUN': (58, 58, 35, 38),  'TWN': (65, 32, 18, 62),
    'TZA': (50, 68, 32, 28),  'URY': (72,145, 42, 55),  'UZB': (58, 72, 72, 35),
    'YEM': (30, 38, 45, 20),  'ZMB': (50, 62, 35, 28),  'ZWE': (38, 52, 32, 22),
}

# ── economic sectors explicit [agriculture%, industrie%, services%] ──────────
SECTORS_EXPLICIT = {
    'USA': (1, 19, 80),   'CHN': (9, 40, 51),   'RUS': (4, 33, 63),
    'DEU': (1, 28, 71),   'FRA': (2, 20, 78),   'GBR': (1, 20, 79),
    'JPN': (1, 27, 72),   'IND': (17, 27, 56),  'BRA': (6, 22, 72),
    'CAN': (2, 27, 71),   'AUS': (3, 28, 69),   'KOR': (2, 38, 60),
    'MEX': (4, 32, 64),   'IDN': (14, 41, 45),  'SAU': (2, 56, 42),
    'TUR': (6, 26, 68),   'ITA': (2, 24, 74),   'ESP': (2, 23, 75),
    'ARG': (10, 28, 62),  'ZAF': (2, 30, 68),   'IRN': (9, 35, 56),
    'ISR': (2, 23, 75),   'PRK': (22, 47, 31),  'UKR': (12, 26, 62),
    'POL': (3, 34, 63),   'NLD': (2, 21, 77),   'CHE': (1, 25, 74),
    'SWE': (2, 22, 76),   'NOR': (2, 36, 62),   'PAK': (25, 21, 54),
    'NGA': (21, 24, 55),  'EGY': (11, 35, 54),  'VNM': (17, 34, 49),
    'PHL': (10, 30, 60),  'COL': (7, 33, 60),   'VEN': (4, 48, 48),
    'IRQ': (3, 55, 42),   'SYR': (20, 20, 60),  'ARE': (1, 53, 46),
    'QAT': (1, 61, 38),   'CUB': (4, 26, 70),   'KAZ': (5, 38, 57),
    'THA': (9, 35, 56),   'MYS': (9, 38, 53),   'ETH': (38, 22, 40),
    'GRC': (4, 16, 80),   'CZE': (2, 38, 60),   'HUN': (4, 30, 66),
    'ROU': (5, 31, 64),   'NOR': (2, 36, 62),   'DZA': (12, 45, 43),
    'AZE': (6, 54, 40),   'KWT': (0, 58, 42),   'LBY': (2, 58, 40),
    'AGO': (10, 62, 28),  'NZL': (5, 26, 69),
}

def sectors_from_gdp_per_cap(gdp_per_cap: float) -> tuple:
    if gdp_per_cap > 35000: return (1, 23, 76)
    if gdp_per_cap > 25000: return (2, 26, 72)
    if gdp_per_cap > 15000: return (4, 29, 67)
    if gdp_per_cap > 8000:  return (8, 32, 60)
    if gdp_per_cap > 4000:  return (14, 28, 58)
    if gdp_per_cap > 2000:  return (20, 25, 55)
    return (32, 20, 48)

# ── military equipment ───────────────────────────────────────────────────────
EQUIPMENT_EXPLICIT = {
    'USA': {'chars_combat': 2381, 'avions_chasse': 2831, 'navires_guerre': 273, 'sous_marins': 72,  'helicopteres': 5760, 'artillerie': 1934},
    'CHN': {'chars_combat': 7716, 'avions_chasse': 1271, 'navires_guerre': 75,  'sous_marins': 68,  'helicopteres': 912,  'artillerie': 5971},
    'RUS': {'chars_combat':20215, 'avions_chasse': 1167, 'navires_guerre': 48,  'sous_marins': 63,  'helicopteres': 1543, 'artillerie': 6083},
    'DEU': {'chars_combat':  406, 'avions_chasse':  215, 'navires_guerre': 20,  'sous_marins':  6,  'helicopteres':  226, 'artillerie':  185},
    'FRA': {'chars_combat':  222, 'avions_chasse':  254, 'navires_guerre': 22,  'sous_marins': 10,  'helicopteres':  408, 'artillerie':  262},
    'GBR': {'chars_combat':  249, 'avions_chasse':  208, 'navires_guerre': 19,  'sous_marins': 10,  'helicopteres':  354, 'artillerie':  184},
    'JPN': {'chars_combat':  678, 'avions_chasse':  363, 'navires_guerre': 48,  'sous_marins': 17,  'helicopteres':  658, 'artillerie':  616},
    'IND': {'chars_combat': 4426, 'avions_chasse':  672, 'navires_guerre': 25,  'sous_marins': 13,  'helicopteres':  722, 'artillerie': 9719},
    'BRA': {'chars_combat':  437, 'avions_chasse':  162, 'navires_guerre': 15,  'sous_marins':  5,  'helicopteres':  456, 'artillerie':  436},
    'CAN': {'chars_combat':   80, 'avions_chasse':  184, 'navires_guerre': 13,  'sous_marins':  4,  'helicopteres':  363, 'artillerie':   24},
    'AUS': {'chars_combat':   59, 'avions_chasse':   98, 'navires_guerre': 13,  'sous_marins':  6,  'helicopteres':  196, 'artillerie':   72},
    'KOR': {'chars_combat': 2381, 'avions_chasse':  582, 'navires_guerre': 23,  'sous_marins': 22,  'helicopteres':  695, 'artillerie':11038},
    'ISR': {'chars_combat': 2760, 'avions_chasse':  339, 'navires_guerre':  8,  'sous_marins':  5,  'helicopteres':  146, 'artillerie':  586},
    'TUR': {'chars_combat': 2414, 'avions_chasse':  281, 'navires_guerre': 16,  'sous_marins': 12,  'helicopteres':  469, 'artillerie': 1748},
    'PAK': {'chars_combat': 2924, 'avions_chasse':  425, 'navires_guerre': 10,  'sous_marins':  8,  'helicopteres':  323, 'artillerie': 3278},
    'IRN': {'chars_combat': 1634, 'avions_chasse':  337, 'navires_guerre':  8,  'sous_marins': 21,  'helicopteres':  129, 'artillerie': 1900},
    'PRK': {'chars_combat': 5025, 'avions_chasse':  563, 'navires_guerre':  8,  'sous_marins': 70,  'helicopteres':  202, 'artillerie':21000},
    'EGY': {'chars_combat': 4624, 'avions_chasse':  583, 'navires_guerre': 10,  'sous_marins':  4,  'helicopteres':  381, 'artillerie': 3855},
    'SAU': {'chars_combat':  892, 'avions_chasse':  363, 'navires_guerre':  8,  'sous_marins':  0,  'helicopteres':  285, 'artillerie':  516},
    'ITA': {'chars_combat':  200, 'avions_chasse':  218, 'navires_guerre': 20,  'sous_marins':  6,  'helicopteres':  244, 'artillerie':  176},
    'ESP': {'chars_combat':  328, 'avions_chasse':  170, 'navires_guerre': 23,  'sous_marins':  3,  'helicopteres':  157, 'artillerie':  306},
    'POL': {'chars_combat':  944, 'avions_chasse':  100, 'navires_guerre':  5,  'sous_marins':  5,  'helicopteres':  248, 'artillerie':  862},
    'UKR': {'chars_combat': 2809, 'avions_chasse':  225, 'navires_guerre': 10,  'sous_marins':  1,  'helicopteres':  149, 'artillerie': 2260},
    'GRC': {'chars_combat': 1563, 'avions_chasse':  309, 'navires_guerre': 13,  'sous_marins': 11,  'helicopteres':  205, 'artillerie': 1920},
}

STRENGTH_BASES = [
    # str=0      1      2      3      4      5       6      7       8       9      10
    [   0,    50,   150,   350,   600,   900,  1400,  2200,  3500,  5000,  7000],  # chars
    [   0,    20,    60,   120,   200,   280,   350,   430,   550,   750,  1000],  # jets
    [   0,     1,     3,     5,     7,    10,    14,    18,    24,    35,    50 ],  # ships
    [   0,     0,     1,     2,     3,     5,     8,    12,    18,    30,    45 ],  # subs
    [   0,    20,    50,   100,   160,   250,   350,   480,   650,   850,  1100],  # heli
    [   0,    50,   200,   500,   800,  1200,  1800,  2500,  3500,  5000,  8000],  # arty
]

def equipment_from_strength(strength: int, gdp: float, budget_pct: float) -> dict:
    s = max(0, min(10, strength))
    # Scale slightly by defense spending (budget relative to $50B median)
    budget = gdp * budget_pct / 100
    scale = math.sqrt(max(0.1, budget / 50))
    def sc(base):
        return max(0, round(base * scale))
    return {
        'chars_combat':    sc(STRENGTH_BASES[0][s]),
        'avions_chasse':   sc(STRENGTH_BASES[1][s]),
        'navires_guerre':  sc(STRENGTH_BASES[2][s]),
        'sous_marins':     sc(STRENGTH_BASES[3][s]),
        'helicopteres':    sc(STRENGTH_BASES[4][s]),
        'artillerie':      sc(STRENGTH_BASES[5][s]),
    }

# ── main ─────────────────────────────────────────────────────────────────────
with open(SCENARIO_PATH, encoding='utf-8') as f:
    data = json.load(f)

for cid, country in data['countries'].items():
    # national_stats
    if cid in NATIONAL_STATS:
        sv, fa, en, ei = NATIONAL_STATS[cid]
    else:
        # Derive from existing data
        gdp_pc = (country.get('economy') or {}).get('gdp_per_capita', 5000)
        mil_s  = (country.get('military') or {}).get('strength', 2)
        nuclear = (country.get('military') or {}).get('nuclear_weapons', False)
        sv = min(95, 45 + mil_s * 4 + (20 if nuclear else 0))
        fa = 55 + (gdp_pc / 1000 * 0.5 if gdp_pc < 15000 else 5)
        en = 40
        ei = min(88, 35 + gdp_pc / 1000)
        sv, fa, en, ei = round(sv, 0), round(fa, 0), round(en, 0), round(ei, 0)

    country['national_stats'] = {
        'sovereignty': float(sv),
        'food_autonomy': float(fa),
        'energy_autonomy': float(en),
        'economic_independence': float(ei),
    }

    # sectors
    if country.get('economy') is not None:
        if cid in SECTORS_EXPLICIT:
            ag, ind, svc = SECTORS_EXPLICIT[cid]
        else:
            gdp_pc = country['economy'].get('gdp_per_capita', 5000)
            ag, ind, svc = sectors_from_gdp_per_cap(gdp_pc)
        country['economy']['sectors'] = {
            'agriculture': float(ag),
            'industrie': float(ind),
            'services': float(svc),
        }

    # equipment
    if country.get('military') is not None:
        if cid in EQUIPMENT_EXPLICIT:
            country['military']['equipment'] = EQUIPMENT_EXPLICIT[cid]
        else:
            s  = country['military'].get('strength', 2)
            bp = country['military'].get('defense_budget_pct', 2.0)
            g  = (country.get('economy') or {}).get('gdp', 50)
            country['military']['equipment'] = equipment_from_strength(s, g, bp)

with open(SCENARIO_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Done — {len(data['countries'])} countries updated.")
