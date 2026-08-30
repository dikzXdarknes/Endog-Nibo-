# achievement_data.py

ACHIEVEMENTS = [
    {"id": "first_egg", "name": "Telur Pertama", "desc": "Tangkap 1 telur", "target": 1, "stat": "eggs_caught", "icon": "EG"},
    {"id": "egg_100", "name": "Pengumpul Telur", "desc": "Tangkap 100 telur", "target": 100, "stat": "eggs_caught", "icon": "BK"},
    {"id": "egg_1000", "name": "Peternak", "desc": "Tangkap 1.000 telur", "target": 1000, "stat": "eggs_caught", "icon": "PT"},
    {"id": "golden_10", "name": "Golden Hunter", "desc": "Tangkap 10 telur emas", "target": 10, "stat": "golden_eggs", "icon": "GM"},
    {"id": "combo_10", "name": "Combo Master", "desc": "Capai combo x10", "target": 10, "stat": "best_combo", "icon": "CO"},
    {"id": "combo_50", "name": "Combo God", "desc": "Capai combo x50", "target": 50, "stat": "best_combo", "icon": "EL"},
    {"id": "combo_100", "name": "Impossible?!", "desc": "Capai combo x100", "target": 100, "stat": "best_combo", "icon": "KR"},
    {"id": "score_500", "name": "Pemula", "desc": "Capai skor 500", "target": 500, "stat": "best_score", "icon": "TG"},
    {"id": "score_5000", "name": "Pro Player", "desc": "Capai skor 5.000", "target": 5000, "stat": "best_score", "icon": "PR"},
    {"id": "score_10000", "name": "Master Endog", "desc": "Capai skor 10.000", "target": 10000, "stat": "best_score", "icon": "MS"},
    {"id": "score_50000", "name": "Touch Grass", "desc": "Capai skor 50.000", "target": 50000, "stat": "best_score", "icon": "DE"},
    {"id": "coins_1000", "name": "Kaya Raya", "desc": "Kumpulkan 1.000 koin", "target": 1000, "stat": "lifetime_coins", "icon": "KY"},
    {"id": "coins_10000", "name": "Sultan Endog", "desc": "Kumpulkan 10.000 koin", "target": 10000, "stat": "lifetime_coins", "icon": "BL"},
    {"id": "first_shop", "name": "Belanja Dulu", "desc": "Beli item pertama di toko", "target": 1, "stat": "items_bought", "icon": "KO"},
    {"id": "collector", "name": "Kolektor", "desc": "Miliki 5 skin/background", "target": 5, "stat": "items_owned", "icon": "DM"},
    {"id": "completionist", "name": "Completionist", "desc": "Buka semua achievement", "target": 15, "stat": "unlocked_count", "icon": "FX"},
]

DEFAULT_STATS = {
    "eggs_caught": 0,
    "golden_eggs": 0,
    "best_combo": 0,
    "best_score": 0,
    "lifetime_coins": 0,
    "items_bought": 0,
    "items_owned": 1,
}


def ensure_achievement_data(data):
    data.setdefault("achievement_stats", DEFAULT_STATS.copy())
    for key, value in DEFAULT_STATS.items():
        data["achievement_stats"].setdefault(key, value)
    data.setdefault("achievements", [])
    return data


def get_unlocked(data):
    return set(data.get("achievements", []))


def check_achievements(data):
    ensure_achievement_data(data)
    unlocked = get_unlocked(data)
    newly_unlocked = []

    for achievement in ACHIEVEMENTS:
        if achievement["id"] == "completionist":
            continue
        value = data["achievement_stats"].get(achievement["stat"], 0)
        if value >= achievement["target"] and achievement["id"] not in unlocked:
            unlocked.add(achievement["id"])
            newly_unlocked.append(achievement)

    normal_count = len([a for a in ACHIEVEMENTS if a["id"] != "completionist"])
    if len(unlocked) >= normal_count and "completionist" not in unlocked:
        unlocked.add("completionist")
        newly_unlocked.append(next(a for a in ACHIEVEMENTS if a["id"] == "completionist"))

    data["achievements"] = list(unlocked)
    return newly_unlocked


def achievement_progress(data, achievement):
    ensure_achievement_data(data)
    if achievement["stat"] == "unlocked_count":
        return len(data.get("achievements", []))
    return data["achievement_stats"].get(achievement["stat"], 0)
