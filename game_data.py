# game_data.py
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

DEFAULT_DATA = {
    "coins": 0,
    "high_score": 0,
    "owned_skins": [1],
    "active_skin": 1,
    "owned_bgs": [1],
    "active_bg": 1,
    "achievement_stats": {
        "eggs_caught": 0,
        "golden_eggs": 0,
        "best_combo": 0,
        "best_score": 0,
        "lifetime_coins": 0,
        "items_bought": 0,
        "items_owned": 1
    },
    "achievements": [],
    "shield_count": 0,
    "shield_equipped": False,
    "extra_heart_count": 0,
    "magnet_boost_count": 0,
    "coin_boost_count": 0,
    "slow_time_count": 0,
    "player_xp": 0,
    "player_level": 1,
    "volcano_claim_ready": False,
    "active_pet": 1,
    "daily_login": {"day": 1, "last_claim": "", "streak": 0},
    "leaderboard": []
}

def _default_data():
    # Buat salinan baru supaya nested dict/list tidak ikut terbagi.
    return json.loads(json.dumps(DEFAULT_DATA))

def load_data():
    if not os.path.exists(DATA_FILE):
        data = _default_data()
        _write_data(data)
        return data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("data.json bukan object JSON")

        defaults = _default_data()
        for key, value in defaults.items():
            if key not in data:
                data[key] = value

        if not isinstance(data.get("achievement_stats"), dict):
            data["achievement_stats"] = defaults["achievement_stats"]
        for key, value in defaults["achievement_stats"].items():
            data["achievement_stats"].setdefault(key, value)

        if not isinstance(data.get("achievements"), list):
            data["achievements"] = []
        if not isinstance(data.get("owned_skins"), list):
            data["owned_skins"] = [1]
        if not isinstance(data.get("owned_bgs"), list):
            data["owned_bgs"] = [1]

        return data
    except Exception as e:
        print("Gagal membaca data.json, memakai data default:", e)
        return _default_data()

def _write_data(data):
    # Tulis secara aman: file sementara diganti menjadi data.json setelah sukses.
    temp_file = DATA_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp_file, DATA_FILE)
        return True
    except Exception as e:
        print("Gagal menyimpan data:", e)
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except OSError:
            pass
        return False

def save_data(coins, high_score, skins, active_skin_index, bg_items, active_bg_index, player_data=None, shield_count=0, shield_equipped=False, extra_heart_count=0, magnet_boost_count=0, coin_boost_count=0, slow_time_count=0):
    # player_data dibuat opsional agar kompatibel dengan kode lama.
    data = dict(player_data) if isinstance(player_data, dict) else {}
    data["coins"] = int(coins)
    data["high_score"] = int(high_score)
    data["owned_skins"] = [s["id"] for s in skins if s.get("owned")]
    data["owned_bgs"] = [b["id"] for b in bg_items if b.get("owned")]

    if skins:
        active_skin_index = max(0, min(int(active_skin_index), len(skins) - 1))
        data["active_skin"] = skins[active_skin_index]["id"]
    if bg_items:
        active_bg_index = max(0, min(int(active_bg_index), len(bg_items) - 1))
        data["active_bg"] = bg_items[active_bg_index]["id"]

    data["shield_count"] = max(0, int(shield_count))
    data["shield_equipped"] = bool(shield_equipped) and data["shield_count"] > 0
    data["extra_heart_count"] = max(0, int(extra_heart_count))
    data["magnet_boost_count"] = max(0, int(magnet_boost_count))
    data["coin_boost_count"] = max(0, int(coin_boost_count))
    data["slow_time_count"] = max(0, int(slow_time_count))

    # Pastikan achievement ikut tersimpan.
    if isinstance(player_data, dict):
        data["achievement_stats"] = player_data.get("achievement_stats", {})
        data["achievements"] = player_data.get("achievements", [])

    return _write_data(data)
