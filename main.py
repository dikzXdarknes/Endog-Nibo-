# main.py
import pygame
import random
import sys
import os
import math
import hmac
import hashlib
from datetime import date, timedelta, datetime

# Import dari file pendukung yang baru kita buat
from settings import *
from game_data import load_data, save_data
from achievement_data import ACHIEVEMENTS, check_achievements, achievement_progress, ensure_achievement_data
from rank_data import RANK_TIERS, get_rank_info, get_rank_coin_bonus, get_prestige_stars

# =========================================================
# ENDOG NIBO - ULTIMATE MISSION EDITION V3 (REVISED)
# =========================================================

pygame.init()

# ---------------------------------------------------------
# BACKSOUND GAME
# ---------------------------------------------------------
pygame.mixer.init()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    bgm_menu_path = os.path.join(BASE_DIR, "bgm.mp3")
    bgm_gameplay_path = os.path.join(BASE_DIR, "bgm_gameplay.mp3")
    # Kalau BGM khusus gameplay belum ada filenya, pakai BGM menu aja buat dua-duanya.
    BGM_GAMEPLAY_AVAILABLE = os.path.exists(bgm_gameplay_path)
    pygame.mixer.music.load(bgm_menu_path)
    pygame.mixer.music.set_volume(0.4)
    # Sengaja belum play() di sini: musik baru mulai pas masuk layar LOADING,
    # biar Splash Intro (logo studio) bener-bener senyap.
    current_bgm_track = None
except Exception as e:
    print("Gagal memuat musik:", e)
    BGM_GAMEPLAY_AVAILABLE = False
    current_bgm_track = None

def set_bgm_track(track):
    """track: 'menu' atau 'gameplay'. Ganti musik cuma kalau memang beda track & filenya ada."""
    global current_bgm_track
    if track == current_bgm_track:
        return
    if track == "gameplay" and not BGM_GAMEPLAY_AVAILABLE:
        return
    try:
        path = bgm_gameplay_path if track == "gameplay" else bgm_menu_path
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
        current_bgm_track = track
    except Exception as e:
        print("Gagal ganti musik:", e)

def load_sfx(filename):
    try:
        return pygame.mixer.Sound(os.path.join(BASE_DIR, "sfx", filename))
    except Exception as e:
        print("Gagal memuat SFX:", filename, e)
        return None

sfx_catch = load_sfx("sfx_catch.wav")
sfx_golden = load_sfx("sfx_golden.wav")
sfx_boss = load_sfx("sfx_boss.wav")
sfx_bomb = load_sfx("sfx_bomb.wav")
sfx_hurt = load_sfx("sfx_hurt.wav")
sfx_levelup = load_sfx("sfx_levelup.wav")
sfx_rankup = load_sfx("sfx_rankup.wav")
sfx_click = load_sfx("sfx_click.wav")
sfx_achievement = load_sfx("sfx_achievement.wav")

def play_sfx(sound, volume=0.6):
    # SFX tidak boleh menghentikan game kalau mixer bermasalah.
    try:
        if sound is not None:
            sound.set_volume(volume)
            sound.play()
    except Exception:
        pass

# ---------------------------------------------------------
# PENGATURAN LAYAR & RENDER UTAMA
# ---------------------------------------------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
pygame.display.set_caption("Endog Nibo")
clock = pygame.time.Clock()

# ---------------------------------------------------------
# FONT
# ---------------------------------------------------------
font_large = pygame.font.Font(None, int(WIDTH * 0.10))
font_medium = pygame.font.Font(None, int(WIDTH * 0.065))
font_small = pygame.font.Font(None, int(WIDTH * 0.045))

# =========================================================
# LOAD GAMBAR
# =========================================================

def load_image(filename, size, use_alpha=True, color_fallback=(100, 100, 100)):
    path = os.path.join(BASE_DIR, filename)
    try:
        if use_alpha:
            image = pygame.image.load(path).convert_alpha()
        else:
            image = pygame.image.load(path).convert()
        return pygame.transform.scale(image, size)
    except Exception:
        temp = pygame.Surface(size, pygame.SRCALPHA if use_alpha else 0)
        temp.fill(color_fallback)
        return temp

bg_menu = load_image("bg_menu.jpg", (WIDTH, HEIGHT), use_alpha=False, color_fallback=(40, 40, 60))

bg_default = load_image("bg.jpg", (WIDTH, HEIGHT), use_alpha=False, color_fallback=(135, 206, 235))
bg_night = load_image("bg_malam.jpg", (WIDTH, HEIGHT), use_alpha=False, color_fallback=(15, 15, 40))
bg_snow = load_image("bg_salju.jpg", (WIDTH, HEIGHT), use_alpha=False, color_fallback=(210, 230, 250))
bg_volcano = load_image("bg_volcano.jpg", (WIDTH, HEIGHT), use_alpha=False, color_fallback=(80, 20, 20))

skin_1 = load_image("keranjang1.jpg", (basket_w, basket_h), use_alpha=True, color_fallback=(139, 69, 19))
skin_2 = load_image("keranjang2.jpg", (basket_w, basket_h), use_alpha=True, color_fallback=(210, 180, 140))
skin_3 = load_image("keranjang3.jpg", (basket_w, basket_h), use_alpha=True, color_fallback=(255, 215, 0))
skin_4 = load_image("keranjang4.jpg", (basket_w, basket_h), use_alpha=True, color_fallback=(0, 238, 255))
# Skin musiman: otomatis kepakai kalau file gambarnya sudah ada, fallback warna tema kalau belum.
skin_natal = load_image("keranjang_natal.jpg", (basket_w, basket_h), use_alpha=True, color_fallback=(200, 30, 40))
skin_halloween = load_image("keranjang_halloween.jpg", (basket_w, basket_h), use_alpha=True, color_fallback=(255, 140, 0))

egg_img = load_image("telur.jpg", (egg_w, egg_h), use_alpha=True, color_fallback=(240, 230, 210))
golden_egg_img = load_image("telur_emas.jpg", (egg_w, egg_h), use_alpha=True, color_fallback=(255, 223, 0))
rotten_egg_img = load_image("telur_busuk.jpg", (egg_w, egg_h), use_alpha=True, color_fallback=(34, 139, 34))

def tint_image(surface, color, strength=90):
    # Kostum telur: pewarnaan overlay ringan di atas foto telur asli,
    # jadi tidak perlu asset baru buat tiap varian warna.
    tinted = surface.copy()
    overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    overlay.fill((color[0], color[1], color[2], strength))
    tinted.blit(overlay, (0, 0))
    return tinted

def load_egg_skin(filename, tint_color, tint_strength=85):
    # Kalau file foto beneran ada (mis. telur_pink.jpg), dipakai langsung.
    # Kalau belum ada, otomatis pakai versi tint sementara (tidak error).
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        return load_image(filename, (egg_w, egg_h), use_alpha=True, color_fallback=tint_color)
    return tint_image(egg_img, tint_color, tint_strength)

egg_skin_default = egg_img
egg_skin_pink = load_egg_skin("telur_pink.jpg", (255, 105, 180))
egg_skin_blue = load_egg_skin("telur_biru.jpg", (70, 130, 255))
egg_skin_mythic = load_egg_skin("telur_mitos.jpg", (170, 60, 255), 100)
egg_skin_frozen = load_egg_skin("telur_beku.jpg", (150, 230, 255), 120)

candy_img = load_image("permen.jpg", (item_w, item_h), use_alpha=True, color_fallback=(255, 105, 180))
magnet_img = load_image("magnet.jpg", (item_w, item_h), use_alpha=True, color_fallback=(220, 20, 60))
magnet_shop_img = load_image("magnet_boost.jpg", (item_w * 2, item_h * 2), use_alpha=False, color_fallback=(220, 20, 60))
bomb_img = load_image("bom.jpg", (item_w, item_h), use_alpha=True, color_fallback=(20, 20, 20))
egg_shield_img = load_image("egg_shield.jpg", (item_w * 2, item_h * 2), use_alpha=False, color_fallback=(45, 150, 235))
coin_boost_img = load_image("coin_boost.jpg", (item_w * 2, item_h * 2), use_alpha=False, color_fallback=(255, 215, 0))
slow_time_img = load_image("slow_time.jpg", (item_w * 2, item_h * 2), use_alpha=False, color_fallback=(80, 180, 255))

# Ikon Extra Heart dibuat dari bentuk sederhana agar tidak membutuhkan aset tambahan.
def make_heart_icon(size=120):
    # Ikon heart yang lebih rapi: outline gelap, isi merah mengilap, highlight.
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = max(10, size // 7)
    outline = (90, 18, 35)
    red = (235, 55, 75)
    light = (255, 115, 135)
    pygame.draw.circle(surf, outline, (size//2-c, size//3), size//4 + 5)
    pygame.draw.circle(surf, outline, (size//2+c, size//3), size//4 + 5)
    pygame.draw.polygon(surf, outline, [(size//2-size//2//2-5, size//3), (size//2+size//2//2+5, size//3), (size//2, size-size//7+6)])
    pygame.draw.circle(surf, red, (size//2-c, size//3), size//4)
    pygame.draw.circle(surf, red, (size//2+c, size//3), size//4)
    pygame.draw.polygon(surf, red, [(size//2-size//2//2, size//3), (size//2+size//2//2, size//3), (size//2, size-size//7)])
    pygame.draw.ellipse(surf, light, (size*0.28, size*0.20, size*0.20, size*0.12))
    return surf

extra_heart_img = load_image("extra_heart.jpg", (item_w * 2, item_h * 2), use_alpha=False, color_fallback=(45, 20, 50))

# =========================================================
# DATA TOKO & MISI LATAR
# =========================================================

skins = [
    {"id": 1, "name": "Anyaman Kayu", "price": 0, "img": skin_1, "owned": True},
    {"id": 2, "name": "Keranjang Kerajinan", "price": 250, "img": skin_2, "owned": False},
    {"id": 3, "name": "Keranjang Kerajaan", "price": 500, "img": skin_3, "owned": False},
    {"id": 5, "name": "Keranjang Natal", "price": 350, "img": skin_natal, "owned": False},
    {"id": 6, "name": "Keranjang Halloween", "price": 350, "img": skin_halloween, "owned": False},
    {"id": 4, "name": "Keranjang Petir Mythic", "price": 1000, "img": skin_4, "owned": False}
]

# Kostum telur: variasi warna, terpisah dari skin keranjang.
egg_skins = [
    {"id": 1, "name": "Telur Asli", "price": 0, "img": egg_skin_default, "owned": True},
    {"id": 2, "name": "Telur Pink", "price": 200, "img": egg_skin_pink, "owned": False},
    {"id": 3, "name": "Telur Biru", "price": 400, "img": egg_skin_blue, "owned": False},
    {"id": 4, "name": "Telur Mitos Ungu", "price": 900, "img": egg_skin_mythic, "owned": False},
]

bg_items = [
    {"id": 1, "name": "Padang Rumput", "price": 0, "img": bg_default, "owned": True, "animated": False, "unlock_score": 0},
    {"id": 2, "name": "Malam Sunyi", "price": 400, "img": bg_night, "owned": False, "animated": False, "unlock_score": 0},
    {"id": 3, "name": "Musim Salju", "price": 800, "img": bg_snow, "owned": False, "animated": False, "unlock_score": 0},
    {"id": 4, "name": "Gua Volkano (Misi)", "price": 0, "img": bg_volcano, "owned": False, "animated": True, "unlock_score": 5000}
]

items = [
    {"id": 1, "name": "Egg Shield", "price": 150, "img": egg_shield_img, "desc": "Lindungi 1 kesalahan"},
    {"id": 2, "name": "Extra Heart", "price": 200, "img": extra_heart_img, "desc": "+1 nyawa di awal permainan"},
    {"id": 3, "name": "Magnet Booster", "price": 250, "img": magnet_shop_img, "desc": "Aktifkan manual selama 10 detik"},
    {"id": 4, "name": "Coin Boost", "price": 300, "img": coin_boost_img, "desc": "Koin Nibo x2 selama 15 detik"},
    {"id": 5, "name": "Slow Time", "price": 350, "img": slow_time_img, "desc": "Perlambat telur selama 10 detik"},
    {"id": 6, "name": "Mystery Chest", "price": 500, "img": load_image("mystery_chest.jpg", (item_w * 2, item_h * 2), use_alpha=False, color_fallback=(170, 100, 255)), "desc": "Buka untuk hadiah acak!"}
]

# Load data awal player
player_data = load_data()
coins = int(player_data.get("coins", 0))
high_score = int(player_data.get("high_score", 0))
high_score_broken_this_run = False
# Antrean simpan: menghindari nulis file disk di setiap frame tangkapan telur
# (penyebab game terasa 'delay' sesaat pas telur masuk keranjang).
pending_save = False
autosave_timer = 0
AUTOSAVE_INTERVAL = 180  # ~3 detik pada 60 FPS
playtime_frame_counter = 0
screenshot_message = ""
screenshot_message_timer = 0
ensure_achievement_data(player_data)
player_data["achievement_stats"]["best_score"] = max(player_data["achievement_stats"].get("best_score", 0), high_score)
player_data["achievement_stats"]["items_owned"] = max(player_data["achievement_stats"].get("items_owned", 1), len(player_data.get("owned_skins", [1])) + len(player_data.get("owned_bgs", [1])) - 1)
player_data["achievement_stats"]["lifetime_coins"] = max(player_data["achievement_stats"].get("lifetime_coins", 0), coins)
shield_count = max(0, int(player_data.get("shield_count", 0)))
shield_equipped = bool(player_data.get("shield_equipped", False)) and shield_count > 0
extra_heart_count = max(0, int(player_data.get("extra_heart_count", 0)))
magnet_boost_count = max(0, int(player_data.get("magnet_boost_count", 0)))
coin_boost_count = max(0, int(player_data.get("coin_boost_count", 0)))
slow_time_count = max(0, int(player_data.get("slow_time_count", 0)))
player_xp = max(0, int(player_data.get("player_xp", 0)))
player_level = max(1, int(player_data.get("player_level", 1)))

# =========================================================
# SISTEM PET
# =========================================================
PETS = [
    {"id": 1, "name": "Nibo", "unlock_level": 1, "bonus": 0.00, "desc": "Teman setia. Tidak memberi bonus tambahan."},
    {"id": 2, "name": "Flameo", "unlock_level": 5, "bonus": 0.10, "desc": "+10% koin dari telur. Skill: durasi Magnet +30%."},
    {"id": 3, "name": "Sparky", "unlock_level": 10, "bonus": 0.15, "desc": "+15% koin dari telur. Skill: durasi Fever +30%."},
]
active_pet_id = int(player_data.get("active_pet", 1))
if not any(p["id"] == active_pet_id and player_level >= p["unlock_level"] for p in PETS):
    active_pet_id = 1
player_data["active_pet"] = active_pet_id

def get_pet_coin_bonus():
    for p in PETS:
        if p["id"] == active_pet_id:
            return float(p["bonus"]) if player_level >= p["unlock_level"] else 0.0
    return 0.0

def has_active_pet(pet_id):
    if active_pet_id != pet_id:
        return False
    p = next((p for p in PETS if p["id"] == pet_id), None)
    return bool(p) and player_level >= p["unlock_level"]

def get_current_rank_bonus():
    # Bonus koin permanen dari progres RANK (lihat rank_data.py).
    total_eggs = player_data.get("achievement_stats", {}).get("eggs_caught", 0)
    return get_rank_coin_bonus(get_rank_info(total_eggs)["index"])

# =========================================================
# MODE TANTANGAN: tiap main dapet modifier acak, biar tetap seru dimainin berkali-kali.
# =========================================================
CHALLENGE_MODIFIERS = [
    {"id": "kilat", "name": "Telur Kilat", "desc": "Semua telur 30% lebih cepat, koin +50%", "speed_mult": 1.3, "coin_mult": 1.5, "frozen_mult": 1.0, "rain_mult": 1.0},
    {"id": "beku", "name": "Badai Beku", "desc": "Telur Beku 3x lebih sering, koin +30%", "speed_mult": 1.0, "coin_mult": 1.3, "frozen_mult": 3.0, "rain_mult": 1.0},
    {"id": "hujan", "name": "Hujan Telur", "desc": "Hujan Telur lebih sering & lebih lama, koin +20%", "speed_mult": 1.0, "coin_mult": 1.2, "frozen_mult": 1.0, "rain_mult": 2.2},
]
challenge_modifier = CHALLENGE_MODIFIERS[0]

def get_challenge_coin_mult():
    return challenge_modifier["coin_mult"] if game_mode == "CHALLENGE" else 1.0

owned_skins = player_data.get("owned_skins", [1])
active_skin_id = player_data.get("active_skin", 1)
for s in skins:
    s["owned"] = s["id"] in owned_skins or s["id"] == 1

active_skin_index = 0
for i, s in enumerate(skins):
    if s["id"] == active_skin_id:
        active_skin_index = i
        break

owned_bgs = player_data.get("owned_bgs", [1])
active_bg_id = player_data.get("active_bg", 1)
for b in bg_items:
    b["owned"] = b["id"] in owned_bgs or b["id"] == 1 or (b["unlock_score"] > 0 and high_score >= b["unlock_score"])

active_bg_index = 0
for i, b in enumerate(bg_items):
    if b["id"] == active_bg_id:
        active_bg_index = i
        break

owned_egg_skins = player_data.get("owned_egg_skins", [1])
active_egg_skin_id = player_data.get("active_egg_skin", 1)
for e in egg_skins:
    e["owned"] = e["id"] in owned_egg_skins or e["id"] == 1

active_egg_skin_index = 0
for i, e in enumerate(egg_skins):
    if e["id"] == active_egg_skin_id:
        active_egg_skin_index = i
        break

shop_tab = "SKIN"
shop_index = 0
achievement_index = 0
daily_index = 0
pet_view_index = 0
pet_drag_start_x = None
login_message = ""
login_message_active = False

# =========================================================
# DAILY CHALLENGE
# =========================================================

DAILY_CHALLENGE_POOL = [
    {"id": "catch_30", "name": "Penangkap Telur", "desc": "Tangkap 30 telur", "target": 30, "reward": 150, "kind": "eggs"},
    {"id": "combo_15", "name": "Combo Master", "desc": "Capai COMBO x15", "target": 15, "reward": 200, "kind": "combo"},
    {"id": "coins_300", "name": "Pemburu Koin Nibo", "desc": "Dapatkan 300 koin dari permainan", "target": 300, "reward": 250, "kind": "coins"},
    {"id": "catch_60", "name": "Peternak Telur", "desc": "Tangkap 60 telur", "target": 60, "reward": 250, "kind": "eggs"},
    {"id": "combo_25", "name": "Raja Combo", "desc": "Capai COMBO x25", "target": 25, "reward": 350, "kind": "combo"},
    {"id": "coins_600", "name": "Kolektor Koin Nibo", "desc": "Dapatkan 600 koin dari permainan", "target": 600, "reward": 400, "kind": "coins"},
]

def _today_key():
    return date.today().isoformat()

def ensure_daily_challenges():
    daily = player_data.get("daily_challenge")
    today = _today_key()
    if not isinstance(daily, dict) or daily.get("date") != today:
        # Rotasi deterministik berdasarkan tanggal agar semua pemain mendapat
        # paket yang sama pada hari yang sama tanpa menyimpan tanggal lama.
        day_seed = date.today().toordinal()
        start = day_seed % len(DAILY_CHALLENGE_POOL)
        selected = [DAILY_CHALLENGE_POOL[(start + i) % len(DAILY_CHALLENGE_POOL)] for i in range(3)]
        player_data["daily_challenge"] = {
            "date": today,
            "challenges": [
                {**c, "progress": 0, "completed": False, "claimed": False} for c in selected
            ]
        }
        trigger_save()
    return player_data["daily_challenge"]

def daily_add(kind, amount=1, maximum=False):
    global coins, pending_save
    try:
        daily = ensure_daily_challenges()
        changed = False
        for c in daily.get("challenges", []):
            if c.get("kind") != kind or c.get("claimed"):
                continue
            old = int(c.get("progress", 0))
            if maximum:
                new = max(old, int(amount))
            else:
                new = old + int(amount)
            new = min(new, int(c.get("target", 1)))
            if new != old:
                c["progress"] = new
                changed = True
            if c["progress"] >= c["target"] and not c.get("claimed"):
                # Misi hanya ditandai selesai. Reward harus di-CLAIM manual.
                c["completed"] = True
                changed = True
        if changed:
            pending_save = True
    except Exception as e:
        print("DAILY CHALLENGE ERROR (game tetap lanjut):", repr(e))

# =========================================================
# EVENT MINGGUAN
# =========================================================
WEEKLY_EVENT_MILESTONES = [
    {"target": 100, "reward_type": "coins", "amount": 300, "label": "+300 Koin Nibo"},
    {"target": 300, "reward_type": "shield", "amount": 1, "label": "+1 Egg Shield"},
    {"target": 500, "reward_type": "coins", "amount": 750, "label": "+750 Koin Nibo"},
]

def _week_key():
    d = date.today()
    return f"{d.isocalendar().year}-W{d.isocalendar().week:02d}"

def ensure_weekly_event():
    event = player_data.get("weekly_event")
    week = _week_key()
    if not isinstance(event, dict) or event.get("week") != week:
        event = {"week": week, "progress": 0, "claimed": [False, False, False]}
        player_data["weekly_event"] = event
        trigger_save()
    event["progress"] = min(500, max(0, int(event.get("progress", 0))))
    claimed = event.get("claimed", [False, False, False])
    event["claimed"] = list(claimed[:3]) + [False] * max(0, 3-len(claimed))
    return event

def weekly_event_add(amount=1):
    global pending_save
    try:
        event = ensure_weekly_event()
        old = int(event.get("progress", 0))
        event["progress"] = min(500, old + int(amount))
        if event["progress"] != old:
            player_data["weekly_event"] = event
            pending_save = True
    except Exception as e:
        print("WEEKLY EVENT ERROR (game tetap lanjut):", repr(e))

def claim_weekly_reward(index):
    global coins, shield_count, shield_equipped
    event = ensure_weekly_event()
    if index < 0 or index >= len(WEEKLY_EVENT_MILESTONES) or event["claimed"][index]:
        return False, "Hadiah sudah di-claim."
    milestone = WEEKLY_EVENT_MILESTONES[index]
    if int(event.get("progress", 0)) < milestone["target"]:
        return False, "Target belum tercapai."
    if milestone["reward_type"] == "coins":
        coins += milestone["amount"]
    elif milestone["reward_type"] == "shield":
        shield_count += milestone["amount"]
        shield_equipped = shield_count > 0
    event["claimed"][index] = True
    player_data["weekly_event"] = event
    trigger_save()
    return True, f"HADIAH EVENT: {milestone['label']}"

# =========================================================
# LOGIN HARIAN 7 HARI
# =========================================================
LOGIN_REWARDS = [
    {"type": "coins", "amount": 50, "label": "+50 Koin Nibo"},
    {"type": "coins", "amount": 60, "label": "+60 Koin Nibo"},
    {"type": "magnet", "amount": 1, "label": "+1 Magnet"},
    {"type": "coins", "amount": 80, "label": "+80 Koin Nibo"},
    {"type": "coinboost", "amount": 1, "label": "+1 Coin Boost"},
    {"type": "coins", "amount": 100, "label": "+100 Koin Nibo"},
    {"type": "shield", "amount": 1, "label": "MINGGU PERTAMA! +1 Egg Shield"},
    {"type": "coins", "amount": 120, "label": "+120 Koin Nibo"},
    {"type": "slowtime", "amount": 1, "label": "+1 Slow Time"},
    {"type": "coins", "amount": 150, "label": "+150 Koin Nibo"},
    {"type": "magnet", "amount": 1, "label": "+1 Magnet"},
    {"type": "coins", "amount": 180, "label": "+180 Koin Nibo"},
    {"type": "coinboost", "amount": 1, "label": "+1 Coin Boost"},
    {"type": "coins", "amount": 400, "label": "2 MINGGU! +400 Koin Nibo"},
    {"type": "coins", "amount": 220, "label": "+220 Koin Nibo"},
    {"type": "magnet", "amount": 1, "label": "+1 Magnet"},
    {"type": "coins", "amount": 250, "label": "+250 Koin Nibo"},
    {"type": "slowtime", "amount": 1, "label": "+1 Slow Time"},
    {"type": "coins", "amount": 280, "label": "+280 Koin Nibo"},
    {"type": "coinboost", "amount": 1, "label": "+1 Coin Boost"},
    {"type": "shield", "amount": 2, "label": "3 MINGGU! +2 Egg Shield"},
    {"type": "coins", "amount": 300, "label": "+300 Koin Nibo"},
    {"type": "magnet", "amount": 1, "label": "+1 Magnet"},
    {"type": "coins", "amount": 320, "label": "+320 Koin Nibo"},
    {"type": "coinboost", "amount": 1, "label": "+1 Coin Boost"},
    {"type": "coins", "amount": 350, "label": "+350 Koin Nibo"},
    {"type": "slowtime", "amount": 1, "label": "+1 Slow Time"},
    {"type": "coins", "amount": 800, "label": "HAMPIR SEBULAN! +800 Koin Nibo"},
    {"type": "coins", "amount": 400, "label": "+400 Koin Nibo"},
    {"type": "coins", "amount": 1500, "label": "30 HARI PENUH! +1500 Koin Nibo"},
]
LOGIN_CYCLE_DAYS = len(LOGIN_REWARDS)

def _yesterday_key():
    return (date.today() - timedelta(days=1)).isoformat()

def ensure_login_data():
    login = player_data.get("daily_login")
    today = _today_key()
    if not isinstance(login, dict):
        login = {"day": 1, "last_claim": "", "streak": 0}
        player_data["daily_login"] = login
    last = login.get("last_claim", "")
    if last == today:
        return login
    if last and last != _yesterday_key():
        login["day"] = 1
        login["streak"] = 0
    login["day"] = max(1, min(int(login.get("day", 1)), LOGIN_CYCLE_DAYS))
    return login

def claim_daily_login():
    global coins, shield_count, shield_equipped, magnet_boost_count, extra_heart_count, coin_boost_count, slow_time_count
    login = ensure_login_data()
    today = _today_key()
    if login.get("last_claim") == today:
        return False, "LOGIN HARIAN SUDAH DI-CLAIM HARI INI"
    day = max(1, min(int(login.get("day", 1)), LOGIN_CYCLE_DAYS))
    reward = LOGIN_REWARDS[day - 1]
    typ = reward["type"]
    amount = int(reward.get("amount", 1))
    if typ == "coins":
        coins += amount
    elif typ == "shield":
        shield_count += amount
        shield_equipped = True
    elif typ == "magnet":
        magnet_boost_count += amount
    elif typ == "heart":
        extra_heart_count += amount
    elif typ == "coinboost":
        coin_boost_count += amount
    elif typ == "slowtime":
        slow_time_count += amount
    login["last_claim"] = today
    login["streak"] = int(login.get("streak", 0)) + 1
    login["day"] = 1 if day >= LOGIN_CYCLE_DAYS else day + 1
    player_data["daily_login"] = login
    trigger_save()
    return True, f" HARI {day}: {reward['label']} DIDAPAT!"

# =========================================================
# GAME STATE & VARIABLE
# =========================================================

state = "SPLASH"
game_mode = "NORMAL"
mode_time_left = 0
mode_score = 0
loading_timer = 0
splash_timer = 0
SPLASH_FADE = 30
SPLASH_HOLD = 70
SPLASH_DURATION = SPLASH_FADE * 2 + SPLASH_HOLD

# Logo studio opsional: taruh splash_1.png, splash_2.png, dst di folder game
# buat dipakai (gambar akan gantian/crossfade). Kalau belum ada, fallback teks.
splash_images = []
for _i in range(1, 6):
    _p = os.path.join(BASE_DIR, f"splash_{_i}.png")
    if os.path.exists(_p):
        try:
            _img = pygame.image.load(_p).convert_alpha()
            _scale = min(WIDTH * 0.7 / _img.get_width(), HEIGHT * 0.4 / _img.get_height())
            _img = pygame.transform.smoothscale(_img, (int(_img.get_width() * _scale), int(_img.get_height() * _scale)))
            splash_images.append(_img)
        except Exception as e:
            print("Gagal load splash:", _i, e)

prev_state_for_fade = state
fade_in_timer = 0
FADE_IN_DURATION = 15

redeem_input_text = ""
redeem_message = ""
redeem_message_color = WHITE
redeem_message_timer = 0

score = 0
lives = 3
MAX_BASE_SPEED = 18  # Batas atas biar game tidak jadi mustahil di skor tinggi
base_speed = 4
combo_count = 0
shield_count = int(player_data.get("shield_count", 0)) if "player_data" in globals() else 0
shield_equipped = bool(player_data.get("shield_equipped", False)) if "player_data" in globals() else False
extra_heart_count = int(player_data.get("extra_heart_count", 0)) if "player_data" in globals() else 0
magnet_boost_count = int(player_data.get("magnet_boost_count", 0)) if "player_data" in globals() else 0
coin_boost_count = int(player_data.get("coin_boost_count", 0)) if "player_data" in globals() else 0
slow_time_count = int(player_data.get("slow_time_count", 0)) if "player_data" in globals() else 0

basket_x = (WIDTH - basket_w) // 2
basket_y = HEIGHT - int(HEIGHT * 0.15)

egg_x = random.randint(0, WIDTH - egg_w)
egg_y = -100

golden_egg_active = False
golden_egg_x = 0
golden_egg_y = -300

# Telur spesial bertingkat (Pink/Biru/Mitos): hanya muncul kalau skin-nya
# sudah dibeli di toko. Makin tinggi tingkatnya, makin jarang muncul & makin besar koinnya.
pink_egg_active = False
pink_egg_x = 0
pink_egg_y = -350

blue_egg_active = False
blue_egg_x = 0
blue_egg_y = -400

mythic_egg_active = False
mythic_egg_x = 0
mythic_egg_y = -450

rotten_egg_active = False
rotten_egg_x = 0
rotten_egg_y = -400

# Telur Beku: gak bikin game over, tapi keranjang jadi "berat"/lambat
# ngikutin gerakan sesaat setelah kena. Nambah risiko tanpa fatal.
frozen_egg_active = False
frozen_egg_x = 0
frozen_egg_y = -420
freeze_timer = 0


# Hujan Telur: event acak, spawn rate telur biasa naik drastis sesaat.
egg_rain_timer = 0
egg_rain_cooldown = random.randint(1800, 2700)

# Telur Raksasa (Boss Egg): langka, besar, gerak zig-zag, hadiah besar.
boss_egg_active = False
boss_egg_x = 0
boss_egg_y = -500
boss_egg_vx = 3
BOSS_EGG_SCALE = 2.2

bomb_active = False
bomb_x = random.randint(0, WIDTH - item_w)
bomb_y = -600

candy_active = False
candy_x = random.randint(0, WIDTH - item_w)
candy_y = -1000
candy_effect_timer = 0
candy_cooldown = 0

magnet_active = False
magnet_x = random.randint(0, WIDTH - item_w)
magnet_y = -1200
magnet_effect_timer = 0
magnet_cooldown = 0
coin_boost_timer = 0
slow_time_timer = 0
fever_timer = 0
fever_milestone = 0
chest_reward_active = False
chest_reward_message = ""
chest_reward_image = None

floating_texts = []
mythic_particles = []
mythic_egg_particles = []
snow_particles = []
bat_particles = []

# Screen shake + partikel perayaan (combo tinggi, boss egg, rank up).
shake_timer = 0
shake_strength = 0
zoom_timer = 0
ZOOM_DURATION = 24
mythic_catch_flash_timer = 0
celebration_particles = []

def trigger_shake(strength=6, duration=10):
    global shake_timer, shake_strength
    shake_timer = duration
    shake_strength = strength

def spawn_celebration_burst(x, y, color, count=14):
    for _ in range(count):
        angle = random.uniform(0, math.tau if hasattr(math, "tau") else 6.2832)
        speed = random.uniform(1.5, 4.5)
        celebration_particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "size": random.randint(3, 6),
            "alpha": 255,
            "color": color,
        })

def update_and_draw_celebration_particles(surface):
    for p in celebration_particles[:]:
        p_surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (*p["color"], max(0, p["alpha"])), (p["size"], p["size"]), p["size"])
        surface.blit(p_surf, (p["x"], p["y"]))
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.12
        p["alpha"] -= 9
        if p["alpha"] <= 0:
            celebration_particles.remove(p)
ember_sparks = [{"x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT), "speed": random.uniform(1.5, 4), "size": random.randint(2, 5)} for _ in range(35)]

# =========================================================
# TOMBOL & PANEL UI
# =========================================================

# Lobby rapi: tiga tombol utama di tengah dengan jarak lebih lega.
btn_main_w, btn_main_h = 184, 52
btn_play = pygame.Rect(WIDTH // 2 - btn_main_w // 2, int(HEIGHT * 0.46), btn_main_w, btn_main_h)
btn_shop = pygame.Rect(WIDTH // 2 - btn_main_w // 2, int(HEIGHT * 0.56), btn_main_w, btn_main_h)
btn_achievements = pygame.Rect(WIDTH // 2 - btn_main_w // 2, int(HEIGHT * 0.66), btn_main_w, btn_main_h)
btn_rank_menu = pygame.Rect(WIDTH // 2 - btn_main_w // 2, int(HEIGHT * 0.755), btn_main_w, btn_main_h)
btn_stats_menu = pygame.Rect(WIDTH // 2 - btn_main_w // 2, int(HEIGHT * 0.85), btn_main_w, btn_main_h)
# Tombol samping lebih kecil dan memakai ikon gambar/bentuk Pygame, bukan emoji.
side_btn_size = 60
btn_daily = pygame.Rect(10, int(HEIGHT * 0.52), side_btn_size, side_btn_size)
btn_login = pygame.Rect(10, int(HEIGHT * 0.68), side_btn_size, side_btn_size)
btn_pet = pygame.Rect(WIDTH - side_btn_size - 10, int(HEIGHT * 0.52), side_btn_size, side_btn_size)
btn_event = pygame.Rect(WIDTH - side_btn_size - 10, int(HEIGHT * 0.68), side_btn_size, side_btn_size)
btn_mode_normal = pygame.Rect(WIDTH // 2 - 95, int(HEIGHT * 0.16), 190, 46)
btn_mode_fever = pygame.Rect(WIDTH // 2 - 95, int(HEIGHT * 0.32), 190, 46)
btn_mode_survival = pygame.Rect(WIDTH // 2 - 95, int(HEIGHT * 0.48), 190, 46)
btn_mode_challenge = pygame.Rect(WIDTH // 2 - 95, int(HEIGHT * 0.64), 190, 46)
btn_back = pygame.Rect(20, 20, 80, 35)
achievement_panel = pygame.Rect(WIDTH // 2 - 155, int(HEIGHT * 0.17), 310, int(HEIGHT * 0.68))
btn_achievement_prev = pygame.Rect(WIDTH // 2 - 140, int(HEIGHT * 0.78), 50, 38)
btn_achievement_next = pygame.Rect(WIDTH // 2 + 90, int(HEIGHT * 0.78), 50, 38)

shop_panel = pygame.Rect(WIDTH // 2 - 140, int(HEIGHT * 0.22), 280, int(HEIGHT * 0.58))
tab_w, tab_gap = 58, 4
tabs_total_w = 4 * tab_w + 3 * tab_gap
tabs_start_x = shop_panel.centerx - tabs_total_w // 2
tab_y = int(HEIGHT * 0.24)
btn_tab_skin = pygame.Rect(tabs_start_x, tab_y, tab_w, 32)
btn_tab_egg = pygame.Rect(tabs_start_x + (tab_w + tab_gap), tab_y, tab_w, 32)
btn_tab_bg = pygame.Rect(tabs_start_x + 2 * (tab_w + tab_gap), tab_y, tab_w, 32)
btn_tab_item = pygame.Rect(tabs_start_x + 3 * (tab_w + tab_gap), tab_y, tab_w, 32)

btn_buy_item = pygame.Rect(WIDTH // 2 - 110, int(HEIGHT * 0.68), 220, 42)
btn_prev = pygame.Rect(WIDTH // 2 - 125, int(HEIGHT * 0.44), 35, 45)
btn_next = pygame.Rect(WIDTH // 2 + 90, int(HEIGHT * 0.44), 35, 45)

go_panel = pygame.Rect(WIDTH // 2 - 130, int(HEIGHT * 0.13), 260, int(HEIGHT * 0.82))
btn_restart = pygame.Rect(WIDTH // 2 - 90, int(HEIGHT * 0.71), 180, 42)
btn_menu_go = pygame.Rect(WIDTH // 2 - 90, int(HEIGHT * 0.81), 180, 42)
btn_screenshot = pygame.Rect(WIDTH // 2 - 90, int(HEIGHT * 0.60), 180, 36)

btn_pause = pygame.Rect(WIDTH - 50, 10, 40, 35)
# Action bar skill dirapikan: 3 tombol sama besar, jarak rata, dengan label + badge jumlah.
skill_btn_w, skill_btn_h = 95, 58
skill_btn_gap = 10
skill_btn_margin = (WIDTH - 3 * skill_btn_w - 2 * skill_btn_gap) // 2
skill_btn_y = 130
btn_slow_use = pygame.Rect(skill_btn_margin, skill_btn_y, skill_btn_w, skill_btn_h)
btn_coin_use = pygame.Rect(skill_btn_margin + skill_btn_w + skill_btn_gap, skill_btn_y, skill_btn_w, skill_btn_h)
btn_magnet_use = pygame.Rect(skill_btn_margin + 2 * (skill_btn_w + skill_btn_gap), skill_btn_y, skill_btn_w, skill_btn_h)
pause_panel = pygame.Rect(WIDTH // 2 - 130, int(HEIGHT * 0.25), 260, int(HEIGHT * 0.52))
btn_resume = pygame.Rect(WIDTH // 2 - 90, int(HEIGHT * 0.35), 180, 42)
btn_menu_pause = pygame.Rect(WIDTH // 2 - 90, int(HEIGHT * 0.46), 180, 42)
btn_quit = pygame.Rect(WIDTH // 2 - 90, int(HEIGHT * 0.57), 180, 42)

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def draw_heart_shape(surface, center, size, fill=(235,55,75), outline=(80,20,30), highlight=True):
    x, y = center
    r = max(4, size // 4)
    pts = [(x, y + size // 2), (x - size // 2, y), (x - r, y - size // 3),
           (x, y - size // 5), (x + r, y - size // 3), (x + size // 2, y)]
    pygame.draw.polygon(surface, outline, pts)
    pygame.draw.circle(surface, outline, (x - r, y - size // 6), r)
    pygame.draw.circle(surface, outline, (x + r, y - size // 6), r)
    inner = [(x, y + size // 2 - 3), (x - size // 2 + 4, y), (x - r, y - size // 3 + 4),
             (x, y - size // 5 + 4), (x + r, y - size // 3 + 4), (x + size // 2 - 4, y)]
    pygame.draw.polygon(surface, fill, inner)
    pygame.draw.circle(surface, fill, (x - r, y - size // 6), max(2, r-2))
    pygame.draw.circle(surface, fill, (x + r, y - size // 6), max(2, r-2))
    if highlight:
        pygame.draw.ellipse(surface, (255,160,175), (x-size//4, y-size//4, size//7, size//10))

def draw_menu_icon(surface, rect, kind):
    cx, cy = rect.center
    if kind == "daily":
        # Clipboard + checklist
        board = pygame.Rect(cx-24, cy-25, 48, 54)
        pygame.draw.rect(surface, (235,240,235), board, border_radius=5)
        pygame.draw.rect(surface, (45,55,65), board, width=3, border_radius=5)
        pygame.draw.rect(surface, GOLD, (cx-14, cy-31, 28, 10), border_radius=4)
        for yy in (cy-10, cy+3, cy+16):
            pygame.draw.circle(surface, GREEN, (cx-14, yy), 4)
            pygame.draw.line(surface, (70,80,90), (cx-5, yy), (cx+16, yy), 3)
    elif kind == "pet":
        # Ikon tapak kaki (paw print), dikecilkan biar pas di dalam lingkaran tombol.
        pad_color = (235, 170, 115)
        outline = (100, 60, 35)
        pad_rect = pygame.Rect(cx - 13, cy + 2, 26, 18)
        pygame.draw.ellipse(surface, pad_color, pad_rect)
        pygame.draw.ellipse(surface, outline, pad_rect, 2)
        toe_positions = [(cx - 14, cy - 10, 6), (cx - 5, cy - 16, 7), (cx + 5, cy - 16, 7), (cx + 14, cy - 10, 6)]
        for tx, ty, tr in toe_positions:
            pygame.draw.circle(surface, pad_color, (tx, ty), tr)
            pygame.draw.circle(surface, outline, (tx, ty), tr, 2)
    elif kind == "login":
        # Kotak hadiah
        box=pygame.Rect(cx-25,cy-13,50,38)
        pygame.draw.rect(surface, (190,45,170), box, border_radius=5)
        pygame.draw.rect(surface, GOLD, box, width=3, border_radius=5)
        pygame.draw.rect(surface, (235,80,190), (cx-4,cy-13,8,38))
        pygame.draw.polygon(surface, GOLD, [(cx-25,cy-13),(cx,cy-28),(cx+25,cy-13)])
        pygame.draw.line(surface, (130,30,120), (cx,cy-27),(cx,cy-13),3)
    elif kind == "event":
        # Piala event mingguan sederhana.
        pygame.draw.rect(surface, GOLD, (cx-16, cy-18, 32, 28), border_radius=5)
        pygame.draw.rect(surface, (120,80,15), (cx-5, cy+10, 10, 12), border_radius=2)
        pygame.draw.rect(surface, GOLD, (cx-18, cy+21, 36, 6), border_radius=3)
        pygame.draw.arc(surface, GOLD, (cx-28, cy-15, 18, 24), -1.2, 1.2, 4)
        pygame.draw.arc(surface, GOLD, (cx+10, cy-15, 18, 24), 1.9, 4.3, 4)
    elif kind == "coin":
        pygame.draw.circle(surface, GOLD, (cx,cy), 17)
        pygame.draw.circle(surface, (255,240,130), (cx-4,cy-4), 6)
        pygame.draw.circle(surface, (120,90,10), (cx,cy), 17, 2)
    elif kind == "shield":
        pts=[(cx,cy-25),(cx+20,cy-16),(cx+16,cy+12),(cx,cy+28),(cx-16,cy+12),(cx-20,cy-16)]
        pygame.draw.polygon(surface, (220,175,40), pts)
        pygame.draw.polygon(surface, (80,55,20), pts, 3)
        pygame.draw.ellipse(surface, (250,235,150), (cx-7,cy-13,9,16))

def draw_side_button(rect, kind, label, active=False):
    pygame.draw.rect(screen, (20,30,50), rect, border_radius=14)
    pygame.draw.rect(screen, GOLD if active else WHITE, rect, width=3, border_radius=14)
    icon_rect = pygame.Rect(rect.x, rect.y - 7, rect.width, rect.height - 14)
    draw_menu_icon(screen, icon_rect, kind)
    label_y = rect.bottom - 12
    txt = font_small.render(label, True, WHITE)
    screen.blit(txt, (rect.centerx - txt.get_width()//2, label_y - txt.get_height()//2))

def record_leaderboard(final_score):
    # Simpan top 5 skor lokal, terbaru dulu kalau seri.
    board = player_data.get("leaderboard", [])
    if not isinstance(board, list):
        board = []
    board.append(int(final_score))
    board.sort(reverse=True)
    player_data["leaderboard"] = board[:5]

def save_score_screenshot(surface, final_score):
    # Simpan tangkapan layar skor ke folder screenshots/ di samping game.
    try:
        folder = os.path.join(BASE_DIR, "screenshots")
        os.makedirs(folder, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(folder, f"skor_{final_score}_{ts}.png")
        pygame.image.save(surface, path)
        return path
    except Exception as e:
        print("Gagal simpan screenshot:", repr(e))
        return None

# =========================================================
# SISTEM KODE REDEEM (top-up Koin Nibo manual)
# =========================================================
# GANTI kunci ini jadi teks unik/rahasia punya kamu sendiri, JANGAN dikasih tau ke
# siapapun (termasuk pembeli). Kunci inilah yang bikin kode gak bisa ditebak asal-asalan.
REDEEM_SECRET_KEY = "Rf30Fcu2_gUUvPL4TZEeuD3VtuvNgEa3"

def generate_redeem_code(amount, serial):
    """Bikin 1 kode redeem. 'amount' = jumlah Koin Nibo, 'serial' = nomor urut
    pembelian (naikin manual tiap ada yang beli, misal 1, 2, 3, dst).
    Fungsi ini juga ada di script terpisah 'redeem_code_generator.py' biar kamu
    gak perlu buka game buat generate kode."""
    payload = f"{amount}:{serial}"
    sig = hmac.new(REDEEM_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:6].upper()
    return f"NIBO-{amount}-{serial}-{sig}"

def redeem_code(code_str):
    """Cek & pakai kode redeem. Return (sukses: bool, pesan: str)."""
    code_str = code_str.strip().upper()
    parts = code_str.split("-")
    if len(parts) != 4 or parts[0] != "NIBO":
        return False, "Format kode salah."
    try:
        amount = int(parts[1])
        serial = int(parts[2])
    except ValueError:
        return False, "Format kode salah."

    expected = generate_redeem_code(amount, serial)
    if code_str != expected:
        return False, "Kode gak valid."

    redeemed = player_data.setdefault("redeemed_codes", [])
    if code_str in redeemed:
        return False, "Kode ini udah pernah dipakai di HP ini."

    redeemed.append(code_str)
    return True, f"BERHASIL! +{amount} Koin Nibo masuk!"

def trigger_save():
    global shield_count, shield_equipped, extra_heart_count, magnet_boost_count, coin_boost_count, slow_time_count, pending_save
    # Save tidak boleh membuat game keluar jika ada masalah file/data.
    try:
        player_data["owned_egg_skins"] = [e["id"] for e in egg_skins if e.get("owned")]
        if egg_skins:
            idx = max(0, min(active_egg_skin_index, len(egg_skins) - 1))
            player_data["active_egg_skin"] = egg_skins[idx]["id"]
        result = bool(save_data(
            coins, high_score, skins, active_skin_index,
            bg_items, active_bg_index, player_data,
            shield_count, shield_equipped, extra_heart_count, magnet_boost_count, coin_boost_count, slow_time_count
        ))
        pending_save = False
        return result
    except Exception as e:
        print("SAVE ERROR (game tetap lanjut):", repr(e))
        return False

# Siapkan/refresh misi harian dan event mingguan setelah fungsi save tersedia.
ensure_daily_challenges()
ensure_weekly_event()

def process_achievements():
    # Achievement diproses sekali setelah perubahan statistik selesai.
    try:
        newly_unlocked = check_achievements(player_data)
        for achievement in newly_unlocked:
            # Jangan biarkan efek notifikasi menghentikan game.
            try:
                play_sfx(sfx_achievement, 0.6)
                add_floating_text(
                    f"ACHIEVEMENT: {achievement['name']}!",
                    WIDTH // 2 - 70, HEIGHT // 2, GOLD
                )
            except Exception as e:
                print("ACHIEVEMENT TEXT ERROR:", repr(e))
        if newly_unlocked:
            trigger_save()
        return newly_unlocked
    except Exception as e:
        print("ACHIEVEMENT ERROR (game tetap lanjut):", repr(e))
        return []

def check_rank_up():
    # Rank berbasis TOTAL telur seumur hidup, dicek sekali tiap tangkapan.
    global pending_save
    try:
        total_eggs = player_data.get("achievement_stats", {}).get("eggs_caught", 0)
        info = get_rank_info(total_eggs)
        last_index = int(player_data.get("last_rank_index", 0))
        if info["index"] > last_index:
            player_data["last_rank_index"] = info["index"]
            play_sfx(sfx_rankup, 0.7)
            trigger_shake(7, 14)
            spawn_celebration_burst(WIDTH // 2, HEIGHT // 2, GOLD, 24)
            add_floating_text(f"RANK UP! {info['name']}", WIDTH // 2 - 90, HEIGHT // 2 + 40, GOLD)
            pending_save = True
    except Exception as e:
        print("RANK ERROR (game tetap lanjut):", repr(e))

def add_player_xp(amount=1):
    global player_xp, player_level, coins
    old_level = player_level
    player_xp += int(amount)
    player_level = 1 + player_xp // 100
    player_data["player_xp"] = player_xp
    player_data["player_level"] = player_level
    if player_level > old_level:
        bonus = 50 * (player_level - old_level)
        coins += bonus
        play_sfx(sfx_levelup, 0.6)
        add_floating_text(f"LEVEL UP! LV.{player_level} +{bonus} KOIN", WIDTH // 2 - 130, HEIGHT // 2, GOLD)
        trigger_save()

def update_stat(stat, amount=1, maximum=False):
    # Hanya mengubah statistik. Pemeriksaan achievement dilakukan setelah
    # seluruh statistik pada satu event selesai agar tidak memicu save
    # berkali-kali di dalam collision yang sama.
    try:
        stats = player_data["achievement_stats"]
        if maximum:
            stats[stat] = max(stats.get(stat, 0), amount)
        else:
            stats[stat] = stats.get(stat, 0) + amount
    except Exception as e:
        print(f"STAT ERROR {stat} (game tetap lanjut):", repr(e))

def add_floating_text(text, x, y, color):
    floating_texts.append({"text": text, "x": x, "y": y, "color": color, "timer": 40})

def draw_panel(rect, border_color=PANEL_BORDER):
    shape_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    shape_surf.fill(PANEL_BG)
    screen.blit(shape_surf, rect.topleft)
    pygame.draw.rect(screen, border_color, rect, width=3, border_radius=15)

bolt_flash_timer = 0
gem_pulse_index = 0
gem_pulse_timer = 0

def draw_lightning_effect(surface, x, y, w, h):
    global bolt_flash_timer, gem_pulse_index, gem_pulse_timer

    # 1) Aura "napas": glow ungu-biru yang naik-turun pelan kayak detak jantung.
    breathe = (math.sin(pygame.time.get_ticks() / 500) + 1) / 2  # 0..1 pelan
    pulse = 14 + int(breathe * 14)
    glow_surf = pygame.Surface((w + 40 + pulse, h + 40 + pulse), pygame.SRCALPHA)
    gw, gh = w + 40 + pulse, h + 40 + pulse
    pygame.draw.ellipse(glow_surf, (140, 60, 255, 45 + int(breathe * 25)), (0, 0, gw, gh))
    pygame.draw.ellipse(glow_surf, (90, 160, 255, 30 + int(breathe * 20)), (gw * 0.15, gh * 0.15, gw * 0.7, gh * 0.7))
    surface.blit(glow_surf, (x - (gw - w) // 2, y - (gh - h) // 2))

    # 2) Sambaran petir besar TAPI jarang (bukan tiap frame), lebih berdampak.
    if bolt_flash_timer <= 0 and random.random() < 0.012:
        bolt_flash_timer = 10
    if bolt_flash_timer > 0:
        bolt_flash_timer -= 1
        start_x = int(x + w * 0.5) + random.randint(-10, 10)
        start_y = y - 10
        curr_x, curr_y = start_x, start_y
        for _ in range(5):
            next_x = curr_x + random.randint(-22, 22)
            next_y = curr_y + random.randint(10, 22)
            pygame.draw.line(surface, (150, 90, 255), (curr_x, curr_y), (next_x, next_y), 5)
            pygame.draw.line(surface, (210, 230, 255), (curr_x, curr_y), (next_x, next_y), 2)
            if random.random() < 0.4:
                branch_x = next_x + random.randint(-16, 16)
                branch_y = next_y + random.randint(4, 14)
                pygame.draw.line(surface, (150, 90, 255), (next_x, next_y), (branch_x, branch_y), 2)
            curr_x, curr_y = next_x, next_y
        # Flash tipis di seluruh tepi keranjang pas kilat nyambar.
        pygame.draw.rect(surface, (200, 170, 255), (x - 3, y - 3, w + 6, h + 6), width=2, border_radius=10)

    # 3) Partikel "abu listrik" ungu-biru, jarang & pelan naiknya (elegan, gak norak).
    if random.random() < 0.25:
        mythic_particles.append({
            "x": random.uniform(x + w * 0.05, x + w * 0.95),
            "y": y + h * 0.3,
            "speed": random.uniform(0.6, 1.4),
            "size": random.randint(2, 4),
            "alpha": 220,
            "hue": random.choice([(150, 90, 255), (90, 160, 255)])
        })

    for p in mythic_particles[:]:
        p_surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        color = p.get("hue", (150, 90, 255))
        pygame.draw.circle(p_surf, (*color, p["alpha"]), (p["size"], p["size"]), p["size"])
        surface.blit(p_surf, (p["x"], p["y"]))
        p["y"] -= p["speed"]
        p["alpha"] -= 5
        if p["alpha"] <= 0:
            mythic_particles.remove(p)

    # 4) 3 permata di badan keranjang berkedip terang gantian satu-satu.
    gem_pulse_timer += 1
    if gem_pulse_timer > 70:
        gem_pulse_timer = 0
        gem_pulse_index = (gem_pulse_index + 1) % 3
    gem_spots = [(0.5, 0.30), (0.22, 0.62), (0.78, 0.62)]
    for i, (fx, fy) in enumerate(gem_spots):
        gx, gy = int(x + w * fx), int(y + h * fy)
        is_lit = (i == gem_pulse_index) and gem_pulse_timer < 25
        r = 10 if is_lit else 5
        alpha = 230 if is_lit else 90
        gem_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gem_surf, (180, 220, 255, alpha), (r, r), r)
        surface.blit(gem_surf, (gx - r, gy - r))

def draw_mythic_egg_effect(surface, x, y, w, h):
    # Aura ungu di sekeliling Telur Mitos + jejak partikel ungu yang naik ke atas.
    glow_r = w // 2 + 10 + (pygame.time.get_ticks() // 120 % 5)
    glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (170, 60, 255, 60), (glow_r, glow_r), glow_r)
    pygame.draw.circle(glow_surf, (200, 130, 255, 90), (glow_r, glow_r), max(1, glow_r - 10))
    surface.blit(glow_surf, (x + w // 2 - glow_r, y + h // 2 - glow_r))

    if random.random() < 0.6:
        mythic_egg_particles.append({
            "x": random.uniform(x, x + w),
            "y": random.uniform(y, y + h),
            "speed": random.uniform(1.2, 2.8),
            "drift": random.uniform(-0.6, 0.6),
            "size": random.randint(2, 4),
            "alpha": 220
        })

    for p in mythic_egg_particles[:]:
        p_surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (190, 90, 255, p["alpha"]), (p["size"], p["size"]), p["size"])
        surface.blit(p_surf, (p["x"], p["y"]))
        p["y"] -= p["speed"]
        p["x"] += p["drift"]
        p["alpha"] -= 8
        if p["alpha"] <= 0:
            mythic_egg_particles.remove(p)

def draw_snow_effect(surface, x, y, w, h):
    # Salju turun pelan di sekitar Keranjang Natal.
    if random.random() < 0.5:
        snow_particles.append({
            "x": random.uniform(x - 10, x + w + 10),
            "y": y - 10,
            "speed": random.uniform(0.6, 1.6),
            "drift": random.uniform(-0.4, 0.4),
            "size": random.randint(2, 4),
            "alpha": 230
        })

    for p in snow_particles[:]:
        p_surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (255, 255, 255, p["alpha"]), (p["size"], p["size"]), p["size"])
        surface.blit(p_surf, (p["x"], p["y"]))
        p["y"] += p["speed"]
        p["x"] += p["drift"]
        if p["y"] > y + h + 20:
            snow_particles.remove(p)

def draw_bat_effect(surface, x, y, w, h):
    # Kelelawar kecil terbang bolak-balik di sekitar Keranjang Halloween.
    if random.random() < 0.03 and len(bat_particles) < 4:
        bat_particles.append({
            "x": x - 20,
            "y": random.uniform(y - 20, y + h * 0.3),
            "speed": random.uniform(1.5, 2.5),
            "wing": random.uniform(0, 6.28)
        })

    for b in bat_particles[:]:
        b["x"] += b["speed"]
        b["wing"] += 0.4
        flap = abs(math.sin(b["wing"])) * 6
        bx, by = int(b["x"]), int(b["y"])
        pygame.draw.polygon(surface, (20, 20, 25), [(bx - 10, by - flap), (bx - 2, by), (bx, by - 3), (bx + 2, by), (bx + 10, by - flap)])
        if b["x"] > x + w + 30:
            bat_particles.remove(b)

def draw_animated_volcano_bg(bg_img):
    screen.blit(bg_img, (0, 0))
    for spark in ember_sparks:
        pygame.draw.circle(screen, GOLD, (int(spark["x"]), int(spark["y"])), spark["size"])
        pygame.draw.circle(screen, RED, (int(spark["x"]), int(spark["y"])), max(1, spark["size"] - 1))
        spark["y"] -= spark["speed"]
        spark["x"] += random.uniform(-0.5, 0.5)
        if spark["y"] < 0:
            spark["y"] = HEIGHT + 10
            spark["x"] = random.randint(0, WIDTH)

def reset_game(mode=None):
    global game_mode, mode_time_left, mode_score
    if mode is not None:
        game_mode = mode
    mode_time_left = 3600 if game_mode == "FEVER_RUSH" else 0
    mode_score = 0
    global score, lives, base_speed, combo_count, extra_heart_count, magnet_boost_count, coin_boost_count, slow_time_count
    global high_score_broken_this_run
    global mythic_catch_flash_timer
    global egg_x, egg_y, golden_egg_active, golden_egg_y
    global pink_egg_active, pink_egg_y, blue_egg_active, blue_egg_y, mythic_egg_active, mythic_egg_y
    global rotten_egg_active, rotten_egg_y, bomb_active, bomb_y
    global candy_active, candy_effect_timer, candy_cooldown
    global magnet_active, magnet_effect_timer, magnet_cooldown, coin_boost_timer, slow_time_timer, fever_timer, fever_milestone
    global floating_texts, mythic_particles, mythic_egg_particles
    global boss_egg_active, boss_egg_y
    global frozen_egg_active, frozen_egg_y, freeze_timer
    global egg_rain_timer, egg_rain_cooldown, challenge_modifier

    score = 0
    high_score_broken_this_run = False
    mythic_catch_flash_timer = 0
    if game_mode == "CHALLENGE":
        challenge_modifier = random.choice(CHALLENGE_MODIFIERS)
        lives = 3 + (1 if extra_heart_count > 0 else 0)
    elif game_mode == "FEVER_RUSH":
        # Fever Rush = kejar waktu, jadi nyawa dilonggarin dan telur
        # jatuh lebih cepat dari awal biar skor yang dikejar sepadan
        # dengan risikonya.
        lives = 5 + (1 if extra_heart_count > 0 else 0)
    elif game_mode == "SURVIVAL":
        # Survival = hardcore, cuma 1 nyawa tapi koin 2x lipat.
        lives = 1
    else:
        lives = 3 + (1 if extra_heart_count > 0 else 0)
    if extra_heart_count > 0:
        extra_heart_count -= 1
        player_data["extra_heart_count"] = extra_heart_count
    coin_boost_timer = 0
    slow_time_timer = 0
    fever_timer = 0
    fever_milestone = 0
    # Magnet sekarang diaktifkan manual lewat tombol saat bermain.
    # Jangan mengonsumsi magnet otomatis saat ronde dimulai.
    if magnet_boost_count > 0:
        player_data["magnet_boost_count"] = magnet_boost_count
    base_speed = 7 if game_mode == "FEVER_RUSH" else 4
    if game_mode == "CHALLENGE":
        base_speed = base_speed * challenge_modifier["speed_mult"]
    combo_count = 0

    egg_x = random.randint(0, WIDTH - egg_w)
    egg_y = -100

    golden_egg_active = False
    golden_egg_y = -300

    pink_egg_active = False
    pink_egg_y = -350
    blue_egg_active = False
    blue_egg_y = -400
    mythic_egg_active = False
    mythic_egg_y = -450

    rotten_egg_active = False
    rotten_egg_y = -400

    frozen_egg_active = False
    frozen_egg_y = -420
    freeze_timer = 0

    egg_rain_timer = 0
    egg_rain_cooldown = random.randint(1200, 2100) if game_mode == "CHALLENGE" and challenge_modifier["rain_mult"] > 1.0 else random.randint(1800, 2700)

    boss_egg_active = False
    boss_egg_y = -500

    bomb_active = False
    bomb_y = -600

    candy_active = False
    candy_effect_timer = 0
    candy_cooldown = 1200

    magnet_active = False
    magnet_effect_timer = 0
    magnet_cooldown = 1500

    floating_texts.clear()
    mythic_particles.clear()
    mythic_egg_particles.clear()
    snow_particles.clear()
    bat_particles.clear()

def clamp_basket():
    global basket_x
    if basket_x < 0:
        basket_x = 0
    if basket_x > WIDTH - basket_w:
        basket_x = WIDTH - basket_w

# Sinkronisasi achievement dari data lama saat game dibuka.
check_achievements(player_data)

def open_mystery_chest():
    """Beli dan langsung buka chest; reward diumumkan di toko."""
    global coins, shield_count, shield_equipped, extra_heart_count
    global magnet_boost_count, coin_boost_count, slow_time_count
    global chest_reward_active, chest_reward_message, chest_reward_image

    price = 500
    if coins < price:
        chest_reward_active = True
        chest_reward_message = "Koin Nibo belum cukup untuk membuka Mystery Chest!"
        chest_reward_image = None
        return

    coins -= price

    # Hadiah koleksi: Volcano TIDAK PERNAH masuk pool karena khusus misi.
    unowned_skins = [s for s in skins if not s.get("owned")]
    unowned_bgs = [b for b in bg_items if not b.get("owned") and b.get("id") != 4]
    unowned_eggs = [e for e in egg_skins if not e.get("owned")]

    collection_pool = []
    # Item Mythic paling langka: hanya 1% jika masih belum dimiliki.
    mythic = next((s for s in unowned_skins if s.get("id") == 4), None)
    if mythic and random.random() < 0.01:
        reward_kind, reward_obj = "skin", mythic
    else:
        normal_pool = [s for s in unowned_skins if s.get("id") != 4] + unowned_bgs + unowned_eggs
        if normal_pool and random.random() < 0.35:
            # Di antara koleksi biasa, pilih secara acak.
            reward_kind, reward_obj = "collection", random.choice(normal_pool)
        else:
            reward_kind, reward_obj = "item", random.choice([
                "coins", "shield", "magnet", "coinboost", "slowtime", "heart"
            ])

    if reward_kind in ("skin", "collection"):
        reward_obj["owned"] = True
        if reward_obj in skins:
            reward_name = reward_obj["name"]
            chest_reward_image = reward_obj["img"]
        else:
            reward_name = reward_obj["name"]
            chest_reward_image = reward_obj["img"]
        chest_reward_message = f"HADIAH DAPAT: {reward_name}!"
        update_stat("items_owned", 1)
        process_achievements()
    elif reward_kind == "item":
        chest_reward_image = items[5]["img"]
        if reward_obj == "coins":
            amount = random.randint(100, 250)
            coins += amount
            chest_reward_message = f"DAPAT +{amount} KOIN!"
        elif reward_obj == "shield":
            shield_count += 1
            shield_equipped = True
            chest_reward_message = "DAPAT +1 EGG SHIELD!"
        elif reward_obj == "magnet":
            magnet_boost_count += 1
            chest_reward_message = "DAPAT +1 MAGNET!"
        elif reward_obj == "coinboost":
            coin_boost_count += 1
            chest_reward_message = "DAPAT +1 COIN BOOST!"
        elif reward_obj == "slowtime":
            slow_time_count += 1
            chest_reward_message = "DAPAT +1 SLOW TIME!"
        else:
            extra_heart_count += 1
            chest_reward_message = "DAPAT +1 EXTRA HEART!"

    player_data["shield_count"] = shield_count
    player_data["shield_equipped"] = shield_equipped
    player_data["extra_heart_count"] = extra_heart_count
    player_data["magnet_boost_count"] = magnet_boost_count
    player_data["coin_boost_count"] = coin_boost_count
    player_data["slow_time_count"] = slow_time_count
    update_stat("items_bought")
    trigger_save()
    chest_reward_active = True

def consume_shield(reason="" ):
    global shield_count, shield_equipped
    if shield_equipped and shield_count > 0:
        shield_count -= 1
        shield_equipped = False
        player_data["shield_count"] = shield_count
        player_data["shield_equipped"] = shield_equipped
        add_floating_text("SHIELD MELINDUNGI!", WIDTH // 2 - 90, HEIGHT // 2, CYAN)
        trigger_save()
        return True
    return False

# =========================================================
# GAME LOOP
# =========================================================

running = True

while running:
    clock.tick(60)

    if state != prev_state_for_fade:
        fade_in_timer = FADE_IN_DURATION
        prev_state_for_fade = state

    if state == "SPLASH":
        screen.fill(BLACK)
        splash_timer += 1

        if splash_timer <= SPLASH_FADE:
            alpha = int(255 * (splash_timer / SPLASH_FADE))
        elif splash_timer <= SPLASH_FADE + SPLASH_HOLD:
            alpha = 255
        else:
            fade_progress = (splash_timer - SPLASH_FADE - SPLASH_HOLD) / SPLASH_FADE
            alpha = max(0, int(255 * (1 - fade_progress)))

        if splash_images:
            seg = max(1, SPLASH_DURATION // len(splash_images))
            idx = min(len(splash_images) - 1, splash_timer // seg)
            img = splash_images[idx]
            img_copy = img.copy()
            img_copy.set_alpha(alpha)
            screen.blit(img_copy, (WIDTH // 2 - img.get_width() // 2, HEIGHT // 2 - img.get_height() // 2))
        else:
            glow_pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2
            studio_txt = font_large.render("DIKZ STUDIO GAME", True, (210, 190, 255))
            glow_surf = pygame.Surface((studio_txt.get_width() + 60, studio_txt.get_height() + 60), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (150, 90, 255, int(70 * glow_pulse * (alpha / 255))), glow_surf.get_rect())
            glow_surf.set_alpha(alpha)
            screen.blit(glow_surf, (WIDTH // 2 - glow_surf.get_width() // 2, HEIGHT // 2 - glow_surf.get_height() // 2))
            studio_txt.set_alpha(alpha)
            screen.blit(studio_txt, (WIDTH // 2 - studio_txt.get_width() // 2, HEIGHT // 2 - studio_txt.get_height() // 2))
            tagline = font_small.render("presents", True, (170, 150, 210))
            tagline.set_alpha(alpha)
            screen.blit(tagline, (WIDTH // 2 - tagline.get_width() // 2, HEIGHT // 2 + studio_txt.get_height() // 2 + 6))

        if splash_timer >= SPLASH_DURATION:
            state = "LOADING"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                state = "LOADING"

    elif state == "LOADING":
        screen.fill(BLACK)
        loading_timer += 1
        LOADING_DURATION = 90
        progress = min(1.0, loading_timer / LOADING_DURATION)

        loading_text = font_large.render("LOADING...", True, WHITE)
        screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, HEIGHT // 2 - 60))

        bar_w, bar_h = 240, 18
        bar_x, bar_y = WIDTH // 2 - bar_w // 2, HEIGHT // 2
        pygame.draw.rect(screen, (60, 60, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=9)
        pygame.draw.rect(screen, GOLD, (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=9)
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=9)
        pct_txt = font_small.render(f"{int(progress * 100)}%", True, WHITE)
        screen.blit(pct_txt, (WIDTH // 2 - pct_txt.get_width() // 2, bar_y + bar_h + 8))

        if loading_timer > LOADING_DURATION:
            state = "MENU"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    elif state == "REDEEM":
        screen.fill((20, 24, 40))
        title_txt = font_large.render("TUKAR KODE", True, GOLD)
        screen.blit(title_txt, (WIDTH // 2 - title_txt.get_width() // 2, 60))

        desc_txt = font_small.render("Masukin kode dari penjual Koin Nibo:", True, WHITE)
        screen.blit(desc_txt, (WIDTH // 2 - desc_txt.get_width() // 2, 140))

        input_box = pygame.Rect(30, 180, WIDTH - 60, 54)
        pygame.draw.rect(screen, WHITE, input_box, border_radius=10)
        pygame.draw.rect(screen, GOLD, input_box, width=3, border_radius=10)
        cursor = "|" if (pygame.time.get_ticks() // 400) % 2 == 0 else ""
        input_txt = font_medium.render(redeem_input_text + cursor, True, BLACK)
        screen.blit(input_txt, (input_box.x + 12, input_box.centery - input_txt.get_height() // 2))

        btn_redeem_confirm = pygame.Rect(WIDTH // 2 - 100, 260, 200, 50)
        pygame.draw.rect(screen, GREEN, btn_redeem_confirm, border_radius=12)
        confirm_lbl = font_medium.render("TUKAR", True, WHITE)
        screen.blit(confirm_lbl, (btn_redeem_confirm.centerx - confirm_lbl.get_width() // 2, btn_redeem_confirm.centery - confirm_lbl.get_height() // 2))

        if redeem_message:
            msg_txt = font_small.render(redeem_message, True, redeem_message_color)
            screen.blit(msg_txt, (WIDTH // 2 - msg_txt.get_width() // 2, 330))

        btn_redeem_back = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 90, 120, 44)
        pygame.draw.rect(screen, DARK_GRAY, btn_redeem_back, border_radius=10)
        back_lbl = font_small.render("Kembali", True, WHITE)
        screen.blit(back_lbl, (btn_redeem_back.centerx - back_lbl.get_width() // 2, btn_redeem_back.centery - back_lbl.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save(); running = False
            elif event.type == pygame.TEXTINPUT:
                if len(redeem_input_text) < 24:
                    redeem_input_text += event.text
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    redeem_input_text = redeem_input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    ok, msg = redeem_code(redeem_input_text)
                    redeem_message = msg
                    redeem_message_color = GREEN if ok else RED
                    if ok:
                        coins += int(redeem_input_text.strip().upper().split("-")[1])
                        trigger_save()
                        redeem_input_text = ""
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_redeem_confirm.collidepoint(event.pos):
                    ok, msg = redeem_code(redeem_input_text)
                    redeem_message = msg
                    redeem_message_color = GREEN if ok else RED
                    if ok:
                        coins += int(redeem_input_text.strip().upper().split("-")[1])
                        trigger_save()
                        redeem_input_text = ""
                elif btn_redeem_back.collidepoint(event.pos):
                    pygame.key.stop_text_input()
                    state = "MENU"

    elif state == "MENU":
        screen.blit(bg_menu, (0, 0))

        title_text = font_large.render("ENDOG NIBO", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, int(HEIGHT * 0.15)))

        hs_text = font_medium.render(f"High Score: {high_score}", True, GOLD)
        screen.blit(hs_text, (WIDTH // 2 - hs_text.get_width() // 2, int(HEIGHT * 0.27)))

        # Bar koin berdiri sendiri di atas menu utama.
        coin_bar = pygame.Rect(WIDTH // 2 - 125, int(HEIGHT * 0.30), 250, 46)
        pygame.draw.rect(screen, (25, 25, 45), coin_bar, border_radius=18)
        pygame.draw.rect(screen, GOLD, coin_bar, width=2, border_radius=18)
        draw_menu_icon(screen, pygame.Rect(coin_bar.x + 6, coin_bar.y + 2, 42, 42), "coin")
        coin_text = font_medium.render(f"{coins}", True, GOLD)
        screen.blit(coin_text, (coin_bar.x + 55, coin_bar.centery - coin_text.get_height() // 2))

        btn_redeem = pygame.Rect(coin_bar.right + 8, coin_bar.y, 38, 46)
        pygame.draw.rect(screen, GREEN, btn_redeem, border_radius=12)
        plus_txt = font_medium.render("+", True, WHITE)
        screen.blit(plus_txt, (btn_redeem.centerx - plus_txt.get_width() // 2, btn_redeem.centery - plus_txt.get_height() // 2))

        # Tidak ada emoji: level/XP ditulis dengan font biasa.
        level_txt = font_small.render(f"LEVEL {player_level}  |  XP {player_xp % 100}/100", True, WHITE)
        screen.blit(level_txt, (WIDTH // 2 - level_txt.get_width() // 2, coin_bar.bottom + 4))

        # Rank berdasarkan total telur seumur hidup (bukan cuma 1 game).
        rank_info = get_rank_info(player_data.get("achievement_stats", {}).get("eggs_caught", 0))
        rank_bonus_pct = int(get_rank_coin_bonus(rank_info["index"]) * 100)
        rank_short_name = rank_info["name"].replace("Peternak ", "")
        prestige_stars = get_prestige_stars(rank_info["total_eggs"])
        star_suffix = f" {'*' * min(prestige_stars, 5)}" if prestige_stars > 0 else ""
        if rank_info["next_threshold"] is not None:
            rank_txt = font_small.render(
                f"RANK: {rank_short_name} ({rank_info['total_eggs']}/{rank_info['next_threshold']}) +{rank_bonus_pct}%",
                True, CYAN
            )
        else:
            rank_txt = font_small.render(f"RANK: {rank_short_name}{star_suffix} (MAX) +{rank_bonus_pct}%", True, GOLD)
        screen.blit(rank_txt, (WIDTH // 2 - rank_txt.get_width() // 2, level_txt.get_height() + coin_bar.bottom + 6))

        # Tiga tombol utama saja di tengah.
        pygame.draw.rect(screen, GREEN, btn_play, border_radius=12)
        play_txt = font_medium.render("PLAY", True, WHITE)
        screen.blit(play_txt, (btn_play.centerx - play_txt.get_width() // 2, btn_play.centery - play_txt.get_height() // 2))

        pygame.draw.rect(screen, GOLD, btn_shop, border_radius=12)
        shop_txt = font_medium.render("TOKO", True, BLACK)
        screen.blit(shop_txt, (btn_shop.centerx - shop_txt.get_width() // 2, btn_shop.centery - shop_txt.get_height() // 2))

        pygame.draw.rect(screen, PURPLE, btn_achievements, border_radius=12)
        ach_txt = font_medium.render("PRESTASI", True, WHITE)
        screen.blit(ach_txt, (btn_achievements.centerx - ach_txt.get_width() // 2, btn_achievements.centery - ach_txt.get_height() // 2))

        pygame.draw.rect(screen, CYAN, btn_rank_menu, border_radius=12)
        rank_btn_txt = font_medium.render("RANK", True, BLACK)
        screen.blit(rank_btn_txt, (btn_rank_menu.centerx - rank_btn_txt.get_width() // 2, btn_rank_menu.centery - rank_btn_txt.get_height() // 2))

        pygame.draw.rect(screen, (90, 200, 140), btn_stats_menu, border_radius=12)
        stats_btn_txt = font_medium.render("STATISTIK", True, BLACK)
        screen.blit(stats_btn_txt, (btn_stats_menu.centerx - stats_btn_txt.get_width() // 2, btn_stats_menu.centery - stats_btn_txt.get_height() // 2))

        # Fitur pendukung dibuat kecil di sisi kiri/kanan agar lobby tetap lapang.
        draw_side_button(btn_daily, "daily", "MISI")
        draw_side_button(btn_login, "login", "LOGIN")
        draw_side_button(btn_pet, "pet", "PET")
        draw_side_button(btn_event, "event", "EVENT")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                trigger_save()
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_play.collidepoint(event.pos):
                    state = "MODE_SELECT"
                elif btn_redeem.collidepoint(event.pos):
                    redeem_input_text = ""
                    redeem_message = ""
                    pygame.key.start_text_input()
                    state = "REDEEM"
                elif btn_shop.collidepoint(event.pos):
                    shop_index = 0
                    chest_reward_active = False
                    chest_reward_message = ""
                    chest_reward_image = None
                    state = "SHOP"
                elif btn_achievements.collidepoint(event.pos):
                    achievement_index = 0
                    state = "ACHIEVEMENTS"
                elif btn_rank_menu.collidepoint(event.pos):
                    state = "RANK_LIST"
                elif btn_stats_menu.collidepoint(event.pos):
                    state = "STATS"
                elif btn_daily.collidepoint(event.pos):
                    ensure_daily_challenges()
                    state = "DAILY"
                elif btn_pet.collidepoint(event.pos):
                    pet_view_index = max(0, min(pet_view_index, len(PETS) - 1))
                    chest_reward_active = False
                    chest_reward_message = ""
                    chest_reward_image = None
                    state = "PET"
                elif btn_login.collidepoint(event.pos):
                    login_message_active = False
                    state = "LOGIN"
                elif btn_event.collidepoint(event.pos):
                    state = "EVENT"

    elif state == "EVENT":
        screen.blit(bg_menu, (0, 0))
        title = font_large.render("EVENT MINGGUAN", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.07)))
        info = font_small.render("Kumpulkan telur selama minggu ini", True, CYAN)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, int(HEIGHT * 0.15)))
        event = ensure_weekly_event()
        progress = int(event.get("progress", 0))
        bar = pygame.Rect(WIDTH // 2 - 130, int(HEIGHT * 0.20), 260, 22)
        pygame.draw.rect(screen, DARK_GRAY, bar, border_radius=10)
        fill = int(bar.width * (progress / 500))
        if fill > 0:
            pygame.draw.rect(screen, PURPLE, (bar.x, bar.y, fill, bar.height), border_radius=10)
        ptxt = font_small.render(f"{progress} / 500 TELUR", True, WHITE)
        screen.blit(ptxt, (WIDTH // 2 - ptxt.get_width() // 2, bar.y + 28))
        y = int(HEIGHT * 0.32)
        for i, m in enumerate(WEEKLY_EVENT_MILESTONES):
            panel = pygame.Rect(WIDTH // 2 - 145, y, 290, 72)
            ready = progress >= m["target"]
            claimed = bool(event["claimed"][i])
            draw_panel(panel, border_color=GREEN if ready and not claimed else GOLD if claimed else CYAN)
            title_txt = font_small.render(f"TARGET {m['target']} TELUR", True, GOLD)
            screen.blit(title_txt, (panel.x + 12, panel.y + 8))
            reward_txt = font_small.render(m["label"], True, WHITE)
            screen.blit(reward_txt, (panel.x + 12, panel.y + 36))
            claim_rect = pygame.Rect(panel.right - 88, panel.y + 20, 74, 32)
            pygame.draw.rect(screen, GREEN if ready and not claimed else DARK_GRAY, claim_rect, border_radius=7)
            claim_txt = font_small.render("CLAIM" if not claimed else "SELESAI", True, WHITE if ready and not claimed else GRAY)
            screen.blit(claim_txt, (claim_rect.centerx - claim_txt.get_width() // 2, claim_rect.centery - claim_txt.get_height() // 2))
            y += 82
        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx - back_txt.get_width() // 2, btn_back.centery - back_txt.get_height() // 2))
        for event_ui in pygame.event.get():
            if event_ui.type == pygame.QUIT:
                trigger_save(); running = False
            elif event_ui.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event_ui.pos):
                    state = "MENU"
                else:
                    y_claim = int(HEIGHT * 0.32)
                    for i, m in enumerate(WEEKLY_EVENT_MILESTONES):
                        claim_rect = pygame.Rect(WIDTH // 2 - 145 + 290 - 88, y_claim + 20, 74, 32)
                        if claim_rect.collidepoint(event_ui.pos):
                            ok, msg = claim_weekly_reward(i)
                            if ok:
                                chest_reward_message = msg
                                chest_reward_image = None
                                chest_reward_active = True
                            break
                        y_claim += 82

    elif state == "PET":
        screen.blit(bg_menu, (0, 0))
        title = font_large.render("PET", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.07)))
        info = font_small.render("Geser atau pakai panah untuk memilih pet", True, CYAN)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, int(HEIGHT * 0.15)))

        pet_view_index = max(0, min(pet_view_index, len(PETS) - 1))
        p = PETS[pet_view_index]
        unlocked = player_level >= p["unlock_level"]
        active = active_pet_id == p["id"]
        card = pygame.Rect(WIDTH // 2 - 120, int(HEIGHT * 0.23), 240, 300)
        draw_panel(card, GOLD if active else (GREEN if unlocked else DARK_GRAY))
        cx, cy = card.centerx, card.y + 85
        pet_color = (245, 225, 190) if p["id"] == 1 else (255, 150, 50) if p["id"] == 2 else (255, 210, 50)
        pygame.draw.circle(screen, pet_color, (cx, cy), 58)
        pygame.draw.circle(screen, BLACK, (cx-19, cy-7), 6)
        pygame.draw.circle(screen, BLACK, (cx+19, cy-7), 6)
        name = font_medium.render(p["name"], True, WHITE)
        screen.blit(name, (cx-name.get_width()//2, card.y+160))
        bonus = font_small.render(f"+{int(p['bonus']*100)}% Koin Nibo" if p["bonus"] else "Tanpa Bonus", True, GOLD)
        screen.blit(bonus, (cx-bonus.get_width()//2, card.y+202))
        if unlocked:
            label = "DIPAKAI" if active else "GUNAKAN"
            pygame.draw.rect(screen, DARK_GRAY if active else GREEN, pygame.Rect(card.x+35, card.bottom-58, card.width-70, 40), border_radius=8)
            t = font_small.render(label, True, WHITE)
            screen.blit(t, (cx-t.get_width()//2, card.bottom-58 + 20-t.get_height()//2))
        else:
            t = font_small.render(f"LOCK Lv.{p['unlock_level']}", True, GOLD)
            screen.blit(t, (cx-t.get_width()//2, card.bottom-42))

        btn_pet_prev = pygame.Rect(12, int(HEIGHT * 0.48), 45, 48)
        btn_pet_next = pygame.Rect(WIDTH - 57, int(HEIGHT * 0.48), 45, 48)
        pygame.draw.rect(screen, GRAY if pet_view_index > 0 else DARK_GRAY, btn_pet_prev, border_radius=10)
        pygame.draw.rect(screen, GRAY if pet_view_index < len(PETS)-1 else DARK_GRAY, btn_pet_next, border_radius=10)
        screen.blit(font_large.render("<", True, BLACK), (btn_pet_prev.centerx-10, btn_pet_prev.centery-22))
        screen.blit(font_large.render(">", True, BLACK), (btn_pet_next.centerx-10, btn_pet_next.centery-22))
        dots = "  ".join("O" if i == pet_view_index else "-" for i in range(len(PETS)))
        dot_txt = font_small.render(dots, True, GOLD)
        screen.blit(dot_txt, (WIDTH//2-dot_txt.get_width()//2, int(HEIGHT*0.73)))
        desc = font_small.render(p["desc"], True, WHITE)
        screen.blit(desc, (WIDTH//2-desc.get_width()//2, int(HEIGHT*0.78)))
        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx-back_txt.get_width()//2, btn_back.centery-back_txt.get_height()//2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save(); running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pet_drag_start_x = event.pos[0]
                if btn_back.collidepoint(event.pos):
                    trigger_save(); state = "MENU"
                elif btn_pet_prev.collidepoint(event.pos) and pet_view_index > 0:
                    pet_view_index -= 1
                elif btn_pet_next.collidepoint(event.pos) and pet_view_index < len(PETS)-1:
                    pet_view_index += 1
                elif card.collidepoint(event.pos) and unlocked:
                    active_pet_id = p["id"]
                    player_data["active_pet"] = active_pet_id
                    trigger_save()
            elif event.type == pygame.MOUSEBUTTONUP:
                if pet_drag_start_x is not None:
                    dx = event.pos[0] - pet_drag_start_x
                    if abs(dx) > 45:
                        if dx < 0 and pet_view_index < len(PETS)-1:
                            pet_view_index += 1
                        elif dx > 0 and pet_view_index > 0:
                            pet_view_index -= 1
                    pet_drag_start_x = None

    elif state == "LOGIN":
        screen.blit(bg_menu, (0, 0))
        title = font_large.render("LOGIN HARIAN", True, WHITE)
        screen.blit(title, (WIDTH//2-title.get_width()//2, int(HEIGHT*0.05)))
        login = ensure_login_data()
        day = int(login.get("day", 1))
        claimed_today = login.get("last_claim") == _today_key()
        streak_txt = font_small.render(f"Streak: {login.get('streak', 0)} hari  |  Kalender 30 Hari", True, CYAN)
        screen.blit(streak_txt, (WIDTH//2-streak_txt.get_width()//2, int(HEIGHT*0.11)))

        # Grid 5 kolom x 6 baris supaya 30 hari muat di 1 layar tanpa scroll.
        cols, rows = 5, 6
        cell_w, cell_h, gap = 65, 50, 4
        grid_left = (WIDTH - (cols * cell_w + (cols - 1) * gap)) // 2
        grid_top = int(HEIGHT * 0.16)

        REWARD_SHORT = {"coins": None, "shield": "SHIELD", "magnet": "MAGNET", "heart": "HEART", "coinboost": "COIN x2", "slowtime": "SLOW"}
        last_claimed_day = LOGIN_CYCLE_DAYS if day == 1 else day - 1

        for i, reward in enumerate(LOGIN_REWARDS):
            col = i % cols
            row = i // cols
            x = grid_left + col * (cell_w + gap)
            y = grid_top + row * (cell_h + gap)
            r = pygame.Rect(x, y, cell_w, cell_h)
            active_day = (i + 1) == day and not claimed_today
            is_past = (i + 1) < day or (claimed_today and (i + 1) == last_claimed_day)
            color = GOLD if active_day else (GREEN if is_past else DARK_GRAY)
            draw_panel(r, color)

            d_txt = font_small.render(str(i + 1), True, WHITE)
            screen.blit(d_txt, (r.centerx - d_txt.get_width() // 2, r.y + 2))

            short = REWARD_SHORT.get(reward["type"])
            reward_line = short if short else f"{reward['amount']}"
            rw_txt = font_small.render(reward_line, True, GOLD if active_day else WHITE)
            screen.blit(rw_txt, (r.centerx - rw_txt.get_width() // 2, r.y + cell_h - 20))

            if claimed_today and (i + 1) == last_claimed_day:
                check = font_small.render("OK", True, GREEN)
                screen.blit(check, (r.right - check.get_width() - 2, r.y + 2))

        claim_btn = pygame.Rect(WIDTH//2-105, int(HEIGHT*0.72), 210, 48)
        can_claim = not claimed_today
        pygame.draw.rect(screen, GREEN if can_claim else DARK_GRAY, claim_btn, border_radius=10)
        ct = font_medium.render("CLAIM HARI INI" if can_claim else "SUDAH DI-CLAIM", True, WHITE)
        screen.blit(ct, (claim_btn.centerx-ct.get_width()//2, claim_btn.centery-ct.get_height()//2))
        if login_message_active:
            msg = font_small.render(login_message, True, GOLD)
            screen.blit(msg, (WIDTH//2-msg.get_width()//2, int(HEIGHT*0.82)))
        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx-back_txt.get_width()//2, btn_back.centery-back_txt.get_height()//2))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save(); running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    state = "MENU"
                elif claim_btn.collidepoint(event.pos) and can_claim:
                    ok, msg = claim_daily_login()
                    login_message = msg
                    login_message_active = True

    elif state == "MODE_SELECT":
        screen.blit(bg_menu, (0, 0))
        title = font_large.render("MODE GAME", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.05)))

        mode_rows = [
            (btn_mode_normal, "NORMAL", GREEN, WHITE, "Klasik: tangkap telur, kejar skor tertinggi."),
            (btn_mode_fever, "FEVER RUSH", GOLD, BLACK, "60 detik, telur cepat sejak awal, 5 nyawa!"),
            (btn_mode_survival, "SURVIVAL", RED, WHITE, "Hardcore: cuma 1 nyawa, tapi koin 2x lipat!"),
            (btn_mode_challenge, "TANTANGAN", CYAN, BLACK, "Modifier acak tiap main, selalu beda!"),
        ]
        for rect, label, color, txt_color, desc in mode_rows:
            pygame.draw.rect(screen, color, rect, border_radius=10)
            t = font_medium.render(label, True, txt_color)
            screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
            d = font_small.render(desc, True, WHITE)
            screen.blit(d, (WIDTH // 2 - d.get_width() // 2, rect.bottom + 4))

        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx - back_txt.get_width() // 2, btn_back.centery - back_txt.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save(); running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_mode_normal.collidepoint(event.pos):
                    reset_game("NORMAL"); state = "GAME"
                elif btn_mode_fever.collidepoint(event.pos):
                    reset_game("FEVER_RUSH"); state = "GAME"
                elif btn_mode_survival.collidepoint(event.pos):
                    reset_game("SURVIVAL"); state = "GAME"
                elif btn_mode_challenge.collidepoint(event.pos):
                    reset_game("CHALLENGE"); state = "GAME"
                elif btn_back.collidepoint(event.pos):
                    state = "MENU"

    elif state == "RANK_LIST":
        screen.blit(bg_menu, (0, 0))
        title = font_large.render("DAFTAR RANK", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.04)))

        total_eggs_now = player_data.get("achievement_stats", {}).get("eggs_caught", 0)
        my_rank = get_rank_info(total_eggs_now)

        sub_txt = font_small.render(f"Total telur ditangkap: {total_eggs_now}", True, GOLD)
        screen.blit(sub_txt, (WIDTH // 2 - sub_txt.get_width() // 2, int(HEIGHT * 0.10)))

        bonus_txt = font_small.render(
            f"Bonus koin dari RANK: +{int(get_rank_coin_bonus(my_rank['index']) * 100)}%", True, CYAN
        )
        screen.blit(bonus_txt, (WIDTH // 2 - bonus_txt.get_width() // 2, int(HEIGHT * 0.13)))

        prestige_stars = get_prestige_stars(total_eggs_now)
        if prestige_stars > 0:
            prestige_txt = font_small.render(f"PRESTIGE: {'*' * prestige_stars} ({prestige_stars})", True, GOLD)
            screen.blit(prestige_txt, (WIDTH // 2 - prestige_txt.get_width() // 2, int(HEIGHT * 0.165)))

        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx - back_txt.get_width() // 2, btn_back.centery - back_txt.get_height() // 2))

        list_top = int(HEIGHT * 0.21)
        list_bottom = int(HEIGHT * 0.94)
        row_h = (list_bottom - list_top) / len(RANK_TIERS)
        row_w = WIDTH - 40

        for i, (r_name, r_threshold) in enumerate(RANK_TIERS):
            row_y = int(list_top + i * row_h)
            row_rect = pygame.Rect(20, row_y, row_w, int(row_h) - 4)
            is_current = (i == my_rank["index"])
            is_unlocked = total_eggs_now >= r_threshold

            if is_current:
                pygame.draw.rect(screen, (60, 50, 10), row_rect, border_radius=8)
                pygame.draw.rect(screen, GOLD, row_rect, width=2, border_radius=8)
                text_color = GOLD
            elif is_unlocked:
                pygame.draw.rect(screen, (20, 40, 30), row_rect, border_radius=8)
                text_color = GREEN
            else:
                pygame.draw.rect(screen, (25, 25, 30), row_rect, border_radius=8)
                text_color = GRAY

            marker = "-> " if is_current else ("OK " if is_unlocked else "")
            row_label = font_small.render(f"{marker}{r_name}", True, text_color)
            screen.blit(row_label, (row_rect.x + 10, row_rect.centery - row_label.get_height() // 2))

            req_label = font_small.render(f"{r_threshold}", True, text_color)
            screen.blit(req_label, (row_rect.right - req_label.get_width() - 10, row_rect.centery - req_label.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state = "MENU"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    state = "MENU"

    elif state == "STATS":
        screen.blit(bg_menu, (0, 0))
        title = font_large.render("STATISTIK PEMAIN", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.05)))

        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx - back_txt.get_width() // 2, btn_back.centery - back_txt.get_height() // 2))

        stats = player_data.get("achievement_stats", {})
        total_playtime_sec = int(player_data.get("total_playtime_sec", 0))
        hours = total_playtime_sec // 3600
        minutes = (total_playtime_sec % 3600) // 60

        rows = [
            ("Total Telur Ditangkap", stats.get("eggs_caught", 0)),
            ("Telur Emas Ditangkap", stats.get("golden_eggs", 0)),
            ("Telur Raksasa Ditangkap", stats.get("boss_eggs", 0)),
            ("Combo Terbaik", stats.get("best_combo", 0)),
            ("Skor Tertinggi", stats.get("best_score", 0)),
            ("Total Koin Nibo Terkumpul", stats.get("lifetime_coins", 0)),
            ("Item Dibeli", stats.get("items_bought", 0)),
            ("Skin/BG Dimiliki", stats.get("items_owned", 1)),
            ("Waktu Bermain", f"{hours} jam {minutes} menit"),
        ]

        row_top = int(HEIGHT * 0.15)
        row_h = 46
        for i, (label, value) in enumerate(rows):
            y = row_top + i * row_h
            row_rect = pygame.Rect(15, y, WIDTH - 30, row_h - 6)
            draw_panel(row_rect)
            lbl = font_small.render(label, True, WHITE)
            screen.blit(lbl, (row_rect.x + 10, row_rect.centery - lbl.get_height() // 2))
            val = font_small.render(str(value), True, GOLD)
            screen.blit(val, (row_rect.right - val.get_width() - 10, row_rect.centery - val.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state = "MENU"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    state = "MENU"

    elif state == "ACHIEVEMENTS":
        screen.blit(bg_menu, (0, 0))
        title = font_large.render("PRESTASI", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.06)))

        unlocked_count = len(player_data.get("achievements", []))
        count_txt = font_small.render(f"{unlocked_count} / {len(ACHIEVEMENTS)} TERBUKA", True, GOLD)
        screen.blit(count_txt, (WIDTH // 2 - count_txt.get_width() // 2, int(HEIGHT * 0.13)))

        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx - back_txt.get_width() // 2, btn_back.centery - back_txt.get_height() // 2))

        draw_panel(achievement_panel, border_color=PURPLE)
        achievement_index = max(0, min(achievement_index, len(ACHIEVEMENTS) - 1))
        ach = ACHIEVEMENTS[achievement_index]
        unlocked = ach["id"] in player_data.get("achievements", [])
        progress = min(achievement_progress(player_data, ach), ach["target"])

        icon = ach["icon"] if unlocked else "LOCK"
        icon_txt = font_large.render(icon, True, WHITE)
        screen.blit(icon_txt, (WIDTH // 2 - icon_txt.get_width() // 2, int(HEIGHT * 0.22)))

        name_txt = font_medium.render(ach["name"], True, GOLD if unlocked else WHITE)
        screen.blit(name_txt, (WIDTH // 2 - name_txt.get_width() // 2, int(HEIGHT * 0.38)))

        desc_txt = font_small.render(ach["desc"], True, WHITE)
        screen.blit(desc_txt, (WIDTH // 2 - desc_txt.get_width() // 2, int(HEIGHT * 0.45)))

        if unlocked:
            status_txt = font_small.render("UNLOCKED", True, GREEN)
        else:
            status_txt = font_small.render(f"Progress: {progress:,} / {ach['target']:,}", True, CYAN)
        screen.blit(status_txt, (WIDTH // 2 - status_txt.get_width() // 2, int(HEIGHT * 0.53)))

        bar = pygame.Rect(WIDTH // 2 - 110, int(HEIGHT * 0.59), 220, 18)
        pygame.draw.rect(screen, DARK_GRAY, bar, border_radius=8)
        fill_w = int(bar.width * (progress / max(1, ach["target"])))
        if fill_w > 0:
            pygame.draw.rect(screen, GREEN if unlocked else CYAN, (bar.x, bar.y, fill_w, bar.height), border_radius=8)

        nav_txt = font_small.render(f"{achievement_index + 1} / {len(ACHIEVEMENTS)}", True, WHITE)
        screen.blit(nav_txt, (WIDTH // 2 - nav_txt.get_width() // 2, int(HEIGHT * 0.69)))

        pygame.draw.rect(screen, GRAY, btn_achievement_prev, border_radius=8)
        pygame.draw.rect(screen, GRAY, btn_achievement_next, border_radius=8)
        prev_txt = font_medium.render("<", True, BLACK)
        next_txt = font_medium.render(">", True, BLACK)
        screen.blit(prev_txt, (btn_achievement_prev.centerx - prev_txt.get_width() // 2, btn_achievement_prev.centery - prev_txt.get_height() // 2))
        screen.blit(next_txt, (btn_achievement_next.centerx - next_txt.get_width() // 2, btn_achievement_next.centery - next_txt.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save()
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    state = "MENU"
                elif btn_achievement_prev.collidepoint(event.pos):
                    achievement_index = (achievement_index - 1) % len(ACHIEVEMENTS)
                elif btn_achievement_next.collidepoint(event.pos):
                    achievement_index = (achievement_index + 1) % len(ACHIEVEMENTS)

    elif state == "DAILY":
        screen.blit(bg_menu, (0, 0))
        title = font_large.render("MISI HARIAN", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.07)))
        daily = ensure_daily_challenges()
        date_txt = font_small.render(f"Hari ini - {daily.get('date', _today_key())}", True, CYAN)
        screen.blit(date_txt, (WIDTH // 2 - date_txt.get_width() // 2, int(HEIGHT * 0.15)))

        y = int(HEIGHT * 0.23)
        for c in daily.get("challenges", []):
            panel = pygame.Rect(WIDTH // 2 - 145, y, 290, 90)
            draw_panel(panel, border_color=GOLD if c.get("claimed") else CYAN)
            name = font_medium.render(c.get("name", "Misi"), True, GOLD if c.get("claimed") else WHITE)
            screen.blit(name, (panel.x + 14, panel.y + 10))
            desc = font_small.render(c.get("desc", ""), True, WHITE)
            screen.blit(desc, (panel.x + 14, panel.y + 42))
            progress = min(int(c.get("progress", 0)), int(c.get("target", 1)))
            status = "SELESAI" if c.get("claimed") else f"{progress}/{c.get('target', 1)} - +{c.get('reward', 0)} koin"
            st = font_small.render(status, True, GREEN if c.get("claimed") else GOLD)
            screen.blit(st, (panel.x + 14, panel.y + 66))
            y += 102

        coin_txt = font_medium.render(f"Koin Nibo: {coins}", True, GOLD)
        screen.blit(coin_txt, (WIDTH // 2 - coin_txt.get_width() // 2, int(HEIGHT * 0.72)))
        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx - back_txt.get_width() // 2, btn_back.centery - back_txt.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save(); running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    state = "MENU"
                else:
                    # Claim misi yang sudah selesai secara manual.
                    daily_now = ensure_daily_challenges()
                    y_claim = int(HEIGHT * 0.23)
                    for c in daily_now.get("challenges", []):
                        progress = min(int(c.get("progress", 0)), int(c.get("target", 1)))
                        claim_rect = pygame.Rect(WIDTH // 2 - 145 + 290 - 92, y_claim + 53, 78, 28)
                        if claim_rect.collidepoint(event.pos) and (c.get("completed") or progress >= int(c.get("target", 1))) and not c.get("claimed"):
                            coins += int(c.get("reward", 0))
                            c["claimed"] = True
                            c["completed"] = True
                            player_data["daily_challenge"] = daily_now
                            trigger_save()
                            chest_reward_message = f"Misi selesai! +{c.get('reward', 0)} Koin Nibo"
                            chest_reward_image = None
                            chest_reward_active = True
                            break
                        y_claim += 102

    elif state == "SHOP":
        screen.blit(bg_menu, (0, 0))

        title = font_large.render("TOKO", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.06)))

        coin_text = font_medium.render(f"Koin Nibo Kamu: {coins}", True, GOLD)
        screen.blit(coin_text, (WIDTH // 2 - coin_text.get_width() // 2, int(HEIGHT * 0.14)))

        pygame.draw.rect(screen, GRAY, btn_back, border_radius=8)
        back_txt = font_small.render("Kembali", True, BLACK)
        screen.blit(back_txt, (btn_back.centerx - back_txt.get_width() // 2, btn_back.centery - back_txt.get_height() // 2))

        draw_panel(shop_panel)

        color_s_tab = GREEN if shop_tab == "SKIN" else DARK_GRAY
        color_e_tab = GREEN if shop_tab == "EGG" else DARK_GRAY
        color_b_tab = GREEN if shop_tab == "BG" else DARK_GRAY
        color_i_tab = GREEN if shop_tab == "ITEM" else DARK_GRAY
        for rect, color, label in [(btn_tab_skin, color_s_tab, "Skin"), (btn_tab_egg, color_e_tab, "Telur"), (btn_tab_bg, color_b_tab, "BG"), (btn_tab_item, color_i_tab, "Item")]:
            pygame.draw.rect(screen, color, rect, border_radius=6)
            lbl = font_small.render(label, True, WHITE)
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

        active_list = skins if shop_tab == "SKIN" else egg_skins if shop_tab == "EGG" else bg_items if shop_tab == "BG" else items
        shop_index = max(0, min(shop_index, len(active_list) - 1))
        current_item = active_list[shop_index]

        if shop_tab == "ITEM":
            item_name = font_medium.render(current_item["name"], True, WHITE)
            screen.blit(item_name, (WIDTH // 2 - item_name.get_width() // 2, int(HEIGHT * 0.32)))
            preview = pygame.transform.scale(current_item["img"], (120, 120))
            screen.blit(preview, (WIDTH // 2 - 60, int(HEIGHT * 0.38)))
            desc = font_small.render(current_item.get("desc", "Power-up"), True, CYAN)
            screen.blit(desc, (WIDTH // 2 - desc.get_width() // 2, int(HEIGHT * 0.58)))
            pygame.draw.rect(screen, GRAY, btn_prev, border_radius=8)
            pygame.draw.rect(screen, GRAY, btn_next, border_radius=8)
            prev_txt = font_large.render("<", True, BLACK); next_txt = font_large.render(">", True, BLACK)
            screen.blit(prev_txt, (btn_prev.centerx - prev_txt.get_width() // 2, btn_prev.centery - prev_txt.get_height() // 2))
            screen.blit(next_txt, (btn_next.centerx - next_txt.get_width() // 2, btn_next.centery - next_txt.get_height() // 2))

            item_id = current_item["id"]
            if item_id == 1:
                count = shield_count
                label = "Shield"
                equipped = shield_equipped
            elif item_id == 2:
                count = extra_heart_count
                label = "Extra Heart"
                equipped = False
            elif item_id == 3:
                count = magnet_boost_count
                label = "Magnet"
                equipped = False
            elif item_id == 4:
                count = coin_boost_count
                label = "Coin Boost"
                equipped = False
            elif item_id == 5:
                count = slow_time_count
                label = "Slow Time"
                equipped = False
            else:
                count = 0
                label = "Chest"
                equipped = False

            pygame.draw.rect(screen, GREEN if coins >= current_item["price"] else RED, btn_buy_item, border_radius=10)
            if item_id == 6:
                lbl_text = f"BELI & BUKA ({current_item['price']} Koin Nibo)"
                count_text = "DAPATKAN HADIAH RANDOM"
            else:
                lbl_text = f"Beli ({current_item['price']} Koin Nibo)"
                count_text = f"Persediaan {label}: {count}"
            lbl = font_small.render(lbl_text, True, WHITE)
            screen.blit(lbl, (btn_buy_item.centerx - lbl.get_width() // 2, btn_buy_item.centery - lbl.get_height() // 2))
            count_lbl = font_small.render(count_text, True, GOLD)
            screen.blit(count_lbl, (WIDTH // 2 - count_lbl.get_width() // 2, int(HEIGHT * 0.64)))
        else:
            item_name = font_medium.render(current_item["name"], True, WHITE)
            screen.blit(item_name, (WIDTH // 2 - item_name.get_width() // 2, int(HEIGHT * 0.32)))
            if shop_tab == "SKIN":
                preview_x = WIDTH // 2 - basket_w // 2; preview_y = int(HEIGHT * 0.44)
                screen.blit(current_item["img"], (preview_x, preview_y))
                if current_item["id"] == 4: draw_lightning_effect(screen, preview_x, preview_y, basket_w, basket_h)
                elif current_item["id"] == 5: draw_snow_effect(screen, preview_x, preview_y, basket_w, basket_h)
                elif current_item["id"] == 6: draw_bat_effect(screen, preview_x, preview_y, basket_w, basket_h)
            elif shop_tab == "EGG":
                egg_preview = pygame.transform.smoothscale(current_item["img"], (egg_w * 2, egg_h * 2))
                screen.blit(egg_preview, (WIDTH // 2 - egg_w, int(HEIGHT * 0.42)))
            else:
                prev_bg = pygame.transform.scale(current_item["img"], (140, 140))
                screen.blit(prev_bg, (WIDTH // 2 - 70, int(HEIGHT * 0.41)))
            pygame.draw.rect(screen, GRAY, btn_prev, border_radius=8); pygame.draw.rect(screen, GRAY, btn_next, border_radius=8)
            prev_txt = font_large.render("<", True, BLACK); next_txt = font_large.render(">", True, BLACK)
            screen.blit(prev_txt, (btn_prev.centerx - prev_txt.get_width() // 2, btn_prev.centery - prev_txt.get_height() // 2))
            screen.blit(next_txt, (btn_next.centerx - next_txt.get_width() // 2, btn_next.centery - next_txt.get_height() // 2))
            is_active = (active_skin_index == shop_index) if shop_tab == "SKIN" else (current_item["id"] == 1) if shop_tab == "EGG" else (active_bg_index == shop_index)
            if not current_item["owned"]:
                if shop_tab == "BG" and current_item.get("unlock_score", 0) > 0:
                    claim_ready = bool(player_data.get("volcano_claim_ready", False)) and high_score >= current_item.get("unlock_score", 0)
                    pygame.draw.rect(screen, GREEN if claim_ready else DARK_GRAY, btn_buy_item, border_radius=10)
                    lbl = font_small.render("CLAIM HADIAH" if claim_ready else f"Misi: Skor {current_item['unlock_score']}", True, WHITE if claim_ready else GOLD)
                else:
                    can_buy = coins >= current_item["price"]
                    pygame.draw.rect(screen, GREEN if can_buy else RED, btn_buy_item, border_radius=10)
                    lbl = font_small.render(f"Beli ({current_item['price']} Koin Nibo)", True, WHITE)
            elif shop_tab == "EGG" and current_item["id"] != 1:
                pygame.draw.rect(screen, GOLD, btn_buy_item, border_radius=10)
                lbl = font_small.render("Muncul Otomatis", True, BLACK)
            else:
                pygame.draw.rect(screen, DARK_GRAY if is_active else GOLD, btn_buy_item, border_radius=10)
                lbl = font_small.render("Sedang Dipakai" if is_active else "Gunakan", True, WHITE if is_active else BLACK)
            screen.blit(lbl, (btn_buy_item.centerx - lbl.get_width() // 2, btn_buy_item.centery - lbl.get_height() // 2))

        if chest_reward_active:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 185))
            screen.blit(overlay, (0, 0))
            panel = pygame.Rect(WIDTH // 2 - 145, HEIGHT // 2 - 145, 290, 290)
            draw_panel(panel, border_color=GOLD)
            title_txt = font_medium.render("MYSTERY CHEST", True, GOLD)
            screen.blit(title_txt, (panel.centerx - title_txt.get_width() // 2, panel.y + 18))
            if chest_reward_image is not None:
                preview_reward = pygame.transform.scale(chest_reward_image, (95, 95))
                screen.blit(preview_reward, (panel.centerx - 48, panel.y + 65))
            reward_txt = font_small.render(chest_reward_message, True, WHITE)
            screen.blit(reward_txt, (panel.centerx - reward_txt.get_width() // 2, panel.y + 175))
            close_txt = font_small.render("Tap untuk menutup", True, CYAN)
            screen.blit(close_txt, (panel.centerx - close_txt.get_width() // 2, panel.y + 230))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save(); running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if chest_reward_active:
                    chest_reward_active = False
                    chest_reward_message = ""
                    chest_reward_image = None
                    continue
                if btn_back.collidepoint(event.pos):
                    trigger_save(); state = "MENU"
                elif btn_tab_skin.collidepoint(event.pos): shop_tab = "SKIN"; shop_index = 0
                elif btn_tab_egg.collidepoint(event.pos): shop_tab = "EGG"; shop_index = 0
                elif btn_tab_bg.collidepoint(event.pos): shop_tab = "BG"; shop_index = 0
                elif btn_tab_item.collidepoint(event.pos): shop_tab = "ITEM"; shop_index = 0
                elif btn_prev.collidepoint(event.pos): shop_index = (shop_index - 1) % len(active_list)
                elif btn_next.collidepoint(event.pos): shop_index = (shop_index + 1) % len(active_list)
                elif btn_buy_item.collidepoint(event.pos):
                    if shop_tab == "ITEM":
                        item_id = current_item["id"]
                        price = current_item["price"]
                        if coins >= price:
                            if item_id == 6:
                                # Mystery Chest membayar sendiri di open_mystery_chest().
                                open_mystery_chest()
                                continue
                            coins -= price
                            if item_id == 1:
                                shield_count += 1
                                shield_equipped = True
                                player_data["shield_count"] = shield_count
                                player_data["shield_equipped"] = shield_equipped
                                msg = "SHIELD DIDAPAT!"
                            elif item_id == 2:
                                extra_heart_count += 1
                                player_data["extra_heart_count"] = extra_heart_count
                                msg = "EXTRA HEART DIDAPAT!"
                            elif item_id == 3:
                                magnet_boost_count += 1
                                player_data["magnet_boost_count"] = magnet_boost_count
                                msg = "MAGNET BOOST DIDAPAT!"
                            elif item_id == 4:
                                coin_boost_count += 1
                                player_data["coin_boost_count"] = coin_boost_count
                                msg = "COIN BOOST DIDAPAT!"
                            elif item_id == 5:
                                slow_time_count += 1
                                player_data["slow_time_count"] = slow_time_count
                                msg = "SLOW TIME DIDAPAT!"
                            update_stat("items_bought")
                            process_achievements()
                            trigger_save()
                            chest_reward_message = f"{msg}"
                            chest_reward_image = current_item.get("img")
                            chest_reward_active = True
                    elif not current_item["owned"]:
                        if shop_tab == "BG" and current_item.get("unlock_score", 0) > 0:
                            if high_score >= current_item["unlock_score"] and player_data.get("volcano_claim_ready", False):
                                current_item["owned"] = True
                                player_data["volcano_claim_ready"] = False
                                active_bg_index = shop_index
                                trigger_save()
                                chest_reward_message = "BACKGROUND VOLCANO DIDAPAT!"
                                chest_reward_image = current_item["img"]
                                chest_reward_active = True
                        elif coins >= current_item["price"]:
                            coins -= current_item["price"]; current_item["owned"] = True
                            update_stat("items_bought"); update_stat("items_owned", 1); process_achievements()
                            if shop_tab == "SKIN": active_skin_index = shop_index
                            elif shop_tab == "EGG": active_egg_skin_index = shop_index
                            else: active_bg_index = shop_index
                            trigger_save()
                            chest_reward_message = f"{current_item['name']} berhasil didapat!"
                            chest_reward_image = current_item.get("img")
                            chest_reward_active = True
                    else:
                        if shop_tab == "SKIN": active_skin_index = shop_index
                        elif shop_tab == "EGG":
                            if current_item["id"] == 1: active_egg_skin_index = shop_index
                        else: active_bg_index = shop_index
                        trigger_save()

    elif state == "GAME":
        mouse_x, _ = pygame.mouse.get_pos()
        target_basket_x = mouse_x - basket_w // 2
        if freeze_timer > 0:
            # Kena Telur Beku: keranjang cuma boleh ngikut pelan-pelan (lag), bukan lompat instan.
            basket_x += (target_basket_x - basket_x) * 0.12
            freeze_timer -= 1
        else:
            basket_x = target_basket_x
        clamp_basket()

        # Catat waktu main total (buat halaman Statistik), 1 detik sekali.
        playtime_frame_counter += 1
        if playtime_frame_counter >= 60:
            playtime_frame_counter = 0
            player_data["total_playtime_sec"] = int(player_data.get("total_playtime_sec", 0)) + 1
            pending_save = True

        # Simpan progres misi/event secara berkala saja (bukan tiap tangkapan),
        # supaya tidak ada jeda nulis file setiap kali telur masuk keranjang.
        if pending_save:
            autosave_timer -= 1
            if autosave_timer <= 0:
                trigger_save()
                autosave_timer = AUTOSAVE_INTERVAL
        else:
            autosave_timer = AUTOSAVE_INTERVAL

        if game_mode == "FEVER_RUSH":
            mode_time_left = max(0, mode_time_left - 1)
            mode_score = score
            if mode_time_left == 0:
                high_score = max(high_score, score)
                record_leaderboard(score)
                trigger_save()
                state = "GAMEOVER"

        current_speed = base_speed
        if slow_time_timer > 0:
            current_speed = max(1, int(current_speed * 0.45))
        if candy_effect_timer > 0:
            candy_effect_timer -= 1
            current_speed = max(2, base_speed // 2)

        if candy_cooldown > 0:
            candy_cooldown -= 1

        if magnet_effect_timer > 0:
            magnet_effect_timer -= 1

        if magnet_cooldown > 0:
            magnet_cooldown -= 1
        if coin_boost_timer > 0:
            coin_boost_timer -= 1
        if slow_time_timer > 0:
            slow_time_timer = max(0, slow_time_timer - 1)
            if slow_time_timer == 0:
                add_floating_text("SLOW TIME SELESAI!", WIDTH // 2 - 90, HEIGHT // 2, WHITE)
        if fever_timer > 0:
            fever_timer = max(0, fever_timer - 1)
            if fever_timer == 0:
                add_floating_text("FEVER SELESAI!", WIDTH // 2 - 75, HEIGHT // 2, WHITE)

        if magnet_effect_timer > 0:
            target_x = basket_x + basket_w // 2 - egg_w // 2
            if egg_x < target_x:
                egg_x += min(6, target_x - egg_x)
            elif egg_x > target_x:
                egg_x -= min(6, egg_x - target_x)

            if golden_egg_active:
                if golden_egg_x < target_x:
                    golden_egg_x += min(6, target_x - golden_egg_x)
                elif golden_egg_x > target_x:
                    golden_egg_x -= min(6, golden_egg_x - target_x)

        egg_y += current_speed
        if egg_y > HEIGHT:
            if not consume_shield("MISS"):
                lives -= 1
                combo_count = 0
                fever_milestone = 0
                add_floating_text("MISSED!", egg_x, HEIGHT - 100, RED)
            egg_x = random.randint(0, WIDTH - egg_w)
            egg_y = -100

        # Hujan Telur: event acak sesaat, peluang munculnya telur spesial jadi jauh
        # lebih tinggi + telur utama jatuh lebih cepat. Bikin panik/seru sesekali.
        if egg_rain_timer > 0:
            egg_rain_timer -= 1
        else:
            egg_rain_cooldown -= 1
            if egg_rain_cooldown <= 0:
                rain_mult = challenge_modifier["rain_mult"] if game_mode == "CHALLENGE" else 1.0
                egg_rain_timer = int(240 * rain_mult)
                egg_rain_cooldown = random.randint(1800, 2700)
                add_floating_text("HUJAN TELUR!", WIDTH // 2 - 90, HEIGHT // 3, CYAN)
        rain_active = egg_rain_timer > 0
        spawn_mult = 3.0 if rain_active else 1.0

        # Telur Emas: sekarang lebih langka, tapi koinnya lebih besar.
        if not golden_egg_active and random.random() < 0.0015 * spawn_mult:
            golden_egg_active = True
            golden_egg_x = random.randint(0, WIDTH - egg_w)
            golden_egg_y = -100

        if golden_egg_active:
            golden_egg_y += current_speed + 1
            if golden_egg_y > HEIGHT:
                golden_egg_active = False

        # Telur Pink/Biru/Mitos: hanya bisa muncul kalau skin-nya sudah dibeli
        # di toko (id 2 = Pink, id 3 = Biru, id 4 = Mitos). Makin tinggi
        # tingkatnya, makin jarang munculnya & makin besar koinnya.
        pink_owned = any(e["id"] == 2 and e.get("owned") for e in egg_skins)
        blue_owned = any(e["id"] == 3 and e.get("owned") for e in egg_skins)
        mythic_owned = any(e["id"] == 4 and e.get("owned") for e in egg_skins)

        if pink_owned and not pink_egg_active and random.random() < 0.0030 * spawn_mult:
            pink_egg_active = True
            pink_egg_x = random.randint(0, WIDTH - egg_w)
            pink_egg_y = -100

        if pink_egg_active:
            pink_egg_y += current_speed + 1
            if pink_egg_y > HEIGHT:
                pink_egg_active = False

        if blue_owned and not blue_egg_active and random.random() < 0.0020 * spawn_mult:
            blue_egg_active = True
            blue_egg_x = random.randint(0, WIDTH - egg_w)
            blue_egg_y = -100

        if blue_egg_active:
            blue_egg_y += current_speed + 1
            if blue_egg_y > HEIGHT:
                blue_egg_active = False

        if mythic_owned and not mythic_egg_active and random.random() < 0.0012 * spawn_mult:
            mythic_egg_active = True
            mythic_egg_x = random.randint(0, WIDTH - egg_w)
            mythic_egg_y = -100

        if mythic_egg_active:
            mythic_egg_y += current_speed + 1
            if mythic_egg_y > HEIGHT:
                mythic_egg_active = False

        if not rotten_egg_active and random.random() < 0.0035:
            rotten_egg_active = True
            rotten_egg_x = random.randint(0, WIDTH - egg_w)
            rotten_egg_y = -100

        if rotten_egg_active:
            rotten_egg_y += current_speed + 1
            if rotten_egg_y > HEIGHT:
                rotten_egg_active = False

        # Telur Beku: bikin keranjang jadi lambat/berat sesaat kalau kena, gak fatal.
        frozen_spawn_mult = challenge_modifier["frozen_mult"] if game_mode == "CHALLENGE" else 1.0
        if not frozen_egg_active and random.random() < 0.0022 * frozen_spawn_mult:
            frozen_egg_active = True
            frozen_egg_x = random.randint(0, WIDTH - egg_w)
            frozen_egg_y = -100

        if frozen_egg_active:
            frozen_egg_y += current_speed + 1
            if frozen_egg_y > HEIGHT:
                frozen_egg_active = False



        # Telur Raksasa: langka, gerak zig-zag, hadiah besar.
        if not boss_egg_active and random.random() < 0.0007:
            boss_egg_active = True
            boss_egg_x = random.randint(0, WIDTH - int(egg_w * BOSS_EGG_SCALE))
            boss_egg_y = -150
            boss_egg_vx = random.choice([-4, -3, 3, 4])
            add_floating_text("TELUR RAKSASA MUNCUL!", WIDTH // 2 - 110, 60, PURPLE)

        if boss_egg_active:
            boss_egg_y += max(2, int(current_speed * 0.7))
            boss_egg_x += boss_egg_vx
            boss_w_now = int(egg_w * BOSS_EGG_SCALE)
            if boss_egg_x <= 0 or boss_egg_x >= WIDTH - boss_w_now:
                boss_egg_vx = -boss_egg_vx
                boss_egg_x = max(0, min(boss_egg_x, WIDTH - boss_w_now))
            if boss_egg_y > HEIGHT:
                boss_egg_active = False

        if not bomb_active and random.random() < 0.0025:
            bomb_active = True
            bomb_x = random.randint(0, WIDTH - item_w)
            bomb_y = -100

        if bomb_active:
            bomb_y += current_speed + 1
            if bomb_y > HEIGHT:
                bomb_active = False

        if not candy_active and candy_cooldown <= 0 and random.random() < 0.004:
            candy_active = True
            candy_x = random.randint(0, WIDTH - item_w)
            candy_y = -100

        if candy_active:
            candy_y += current_speed
            if candy_y > HEIGHT:
                candy_active = False
                candy_cooldown = 1200

        basket_rect = pygame.Rect(basket_x, basket_y, basket_w, basket_h)
        egg_rect = pygame.Rect(egg_x, egg_y, egg_w, egg_h)
        
        if basket_rect.colliderect(egg_rect):
            # Satu sumber untuk semua pengali, biar balancing gampang diubah dari sini saja.
            fever_multiplier = 2 if fever_timer > 0 else 1
            coin_boost_multiplier = 2 if coin_boost_timer > 0 else 1
            pet_bonus = 1.0 + get_pet_coin_bonus() + get_current_rank_bonus() + (1.0 if game_mode == "SURVIVAL" else 0.0)
            per_egg_coin_rate = coin_boost_multiplier * fever_multiplier * get_challenge_coin_mult()

            score += fever_multiplier
            base_coin_gain = int(per_egg_coin_rate * pet_bonus)
            coins += base_coin_gain
            combo_count += 1
            play_sfx(sfx_catch, 0.4)
            update_stat("eggs_caught")
            update_stat("lifetime_coins")
            update_stat("best_combo", combo_count, maximum=True)

            # 5) Bonus khusus Keranjang Petir Mythic: percikan listrik + flash tipis tiap nangkep telur.
            if skins[active_skin_index]["id"] == 4:
                mythic_catch_flash_timer = 6
                for _ in range(6):
                    mythic_particles.append({
                        "x": basket_x + basket_w * random.uniform(0.2, 0.8),
                        "y": basket_y + random.uniform(-4, 6),
                        "speed": random.uniform(1.5, 3.0),
                        "size": random.randint(2, 3),
                        "alpha": 255,
                        "hue": random.choice([(150, 90, 255), (90, 160, 255)])
                    })

            # Proses achievement sekali setelah semua stat telur diperbarui.
            process_achievements()
            check_rank_up()

            bonus_coin = 0
            if combo_count >= 15:
                add_floating_text("PERFECT! +3", basket_x, basket_y - 20, PURPLE)
                trigger_shake(5, 8)
                spawn_celebration_burst(basket_x + basket_w // 2, basket_y, PURPLE, 10)
                bonus_coin = 3
            elif combo_count >= 10:
                add_floating_text("SUPER! +2", basket_x, basket_y - 20, GOLD)
                bonus_coin = 2
            elif combo_count >= 5:
                add_floating_text("GREAT! +1", basket_x, basket_y - 20, CYAN)
                bonus_coin = 1
            else:
                add_floating_text("+1", basket_x, basket_y - 20, WHITE)

            bonus_coin_gain = int(bonus_coin * per_egg_coin_rate * pet_bonus)
            coins += bonus_coin_gain
            coins_gained = base_coin_gain + bonus_coin_gain
            daily_add("eggs", 1)
            weekly_event_add(1)
            daily_add("combo", combo_count, maximum=True)
            daily_add("coins", coins_gained)

            # Combo + Fever: setiap 10 combo memicu Fever selama 10 detik.
            if combo_count >= (5 if game_mode == "FEVER_RUSH" else 10) and combo_count // (5 if game_mode == "FEVER_RUSH" else 10) > fever_milestone:
                fever_milestone = combo_count // (5 if game_mode == "FEVER_RUSH" else 10)
                fever_timer = int(600 * (1.3 if has_active_pet(3) else 1.0))
                add_floating_text("FEVER MODE! x2", WIDTH // 2 - 90, HEIGHT // 2, GOLD)

            egg_x = random.randint(0, WIDTH - egg_w)
            egg_y = -100
            if score % 10 == 0:
                speed_cap = MAX_BASE_SPEED + 6 if game_mode == "FEVER_RUSH" else MAX_BASE_SPEED
                base_speed = min(base_speed + 1, speed_cap)

        if golden_egg_active:
            g_egg_rect = pygame.Rect(golden_egg_x, golden_egg_y, egg_w, egg_h)
            if basket_rect.colliderect(g_egg_rect):
                fever_multiplier = 2 if fever_timer > 0 else 1
                score += 10 * fever_multiplier
                golden_coins_gained = int((20 if coin_boost_timer > 0 else 10) * fever_multiplier * (1.0 + get_pet_coin_bonus() + get_current_rank_bonus() + (1.0 if game_mode == "SURVIVAL" else 0.0)) * get_challenge_coin_mult())
                coins += golden_coins_gained
                daily_add("coins", golden_coins_gained)
                weekly_event_add(1)
                update_stat("golden_eggs")
                update_stat("lifetime_coins", golden_coins_gained)
                process_achievements()
                play_sfx(sfx_golden, 0.6)
                add_floating_text("GOLDEN! +10", basket_x, basket_y - 30, GOLD)
                golden_egg_active = False

        if pink_egg_active:
            p_egg_rect = pygame.Rect(pink_egg_x, pink_egg_y, egg_w, egg_h)
            if basket_rect.colliderect(p_egg_rect):
                fever_multiplier = 2 if fever_timer > 0 else 1
                score += 2 * fever_multiplier
                pink_coins_gained = int((6 if coin_boost_timer > 0 else 3) * fever_multiplier * (1.0 + get_pet_coin_bonus() + get_current_rank_bonus() + (1.0 if game_mode == "SURVIVAL" else 0.0)) * get_challenge_coin_mult())
                coins += pink_coins_gained
                daily_add("coins", pink_coins_gained)
                weekly_event_add(1)
                update_stat("pink_eggs")
                update_stat("lifetime_coins", pink_coins_gained)
                process_achievements()
                play_sfx(sfx_catch, 0.5)
                add_floating_text("PINK! +3", basket_x, basket_y - 30, (255, 105, 180))
                pink_egg_active = False

        if blue_egg_active:
            b2_egg_rect = pygame.Rect(blue_egg_x, blue_egg_y, egg_w, egg_h)
            if basket_rect.colliderect(b2_egg_rect):
                fever_multiplier = 2 if fever_timer > 0 else 1
                score += 3 * fever_multiplier
                blue_coins_gained = int((8 if coin_boost_timer > 0 else 4) * fever_multiplier * (1.0 + get_pet_coin_bonus() + get_current_rank_bonus() + (1.0 if game_mode == "SURVIVAL" else 0.0)) * get_challenge_coin_mult())
                coins += blue_coins_gained
                daily_add("coins", blue_coins_gained)
                weekly_event_add(1)
                update_stat("blue_eggs")
                update_stat("lifetime_coins", blue_coins_gained)
                process_achievements()
                play_sfx(sfx_catch, 0.5)
                add_floating_text("BIRU! +4", basket_x, basket_y - 30, (70, 130, 255))
                blue_egg_active = False

        if mythic_egg_active:
            m_egg_rect = pygame.Rect(mythic_egg_x, mythic_egg_y, egg_w, egg_h)
            if basket_rect.colliderect(m_egg_rect):
                fever_multiplier = 2 if fever_timer > 0 else 1
                score += 4 * fever_multiplier
                mythic_coins_gained = int((10 if coin_boost_timer > 0 else 5) * fever_multiplier * (1.0 + get_pet_coin_bonus() + get_current_rank_bonus() + (1.0 if game_mode == "SURVIVAL" else 0.0)) * get_challenge_coin_mult())
                coins += mythic_coins_gained
                daily_add("coins", mythic_coins_gained)
                weekly_event_add(1)
                update_stat("mythic_eggs")
                update_stat("lifetime_coins", mythic_coins_gained)
                process_achievements()
                play_sfx(sfx_golden, 0.5)
                add_floating_text("MITOS! +5", basket_x, basket_y - 30, (170, 60, 255))
                mythic_egg_active = False

        if rotten_egg_active:
            r_egg_rect = pygame.Rect(rotten_egg_x, rotten_egg_y, egg_w, egg_h)
            if basket_rect.colliderect(r_egg_rect):
                if not consume_shield("ROTTEN"):
                    lives -= 1
                    combo_count = 0
                    fever_milestone = 0
                    play_sfx(sfx_hurt, 0.6)
                    add_floating_text("BUSUK! -1 NYAWA", basket_x, basket_y - 30, RED)
                else:
                    add_floating_text("SHIELD! TELUR BUSUK DITAHAN", basket_x, basket_y - 30, CYAN)
                rotten_egg_active = False

        if frozen_egg_active:
            fz_egg_rect = pygame.Rect(frozen_egg_x, frozen_egg_y, egg_w, egg_h)
            if basket_rect.colliderect(fz_egg_rect):
                if not consume_shield("FROZEN"):
                    freeze_timer = 150
                    play_sfx(sfx_hurt, 0.4)
                    add_floating_text("BEKU! KERANJANG MELAMBAT", basket_x, basket_y - 30, CYAN)
                else:
                    add_floating_text("SHIELD! TELUR BEKU DITAHAN", basket_x, basket_y - 30, CYAN)
                frozen_egg_active = False

        if boss_egg_active:
            boss_w_now = int(egg_w * BOSS_EGG_SCALE)
            boss_h_now = int(egg_h * BOSS_EGG_SCALE)
            boss_rect = pygame.Rect(boss_egg_x, boss_egg_y, boss_w_now, boss_h_now)
            if basket_rect.colliderect(boss_rect):
                fever_multiplier = 2 if fever_timer > 0 else 1
                score += 15 * fever_multiplier
                boss_bonus_mult = 1.0 + get_pet_coin_bonus() + get_current_rank_bonus() + (1.0 if game_mode == "SURVIVAL" else 0.0)
                boss_coins_gained = int(40 * fever_multiplier * boss_bonus_mult * get_challenge_coin_mult())
                coins += boss_coins_gained
                daily_add("coins", boss_coins_gained)
                weekly_event_add(3)
                update_stat("boss_eggs")
                update_stat("eggs_caught", 5)
                update_stat("lifetime_coins", boss_coins_gained)
                process_achievements()
                check_rank_up()
                play_sfx(sfx_boss, 0.7)
                trigger_shake(8, 14)
                spawn_celebration_burst(basket_x + basket_w // 2, basket_y, PURPLE, 22)
                add_floating_text("TELUR RAKSASA! +15 & KOIN BESAR", basket_x - 40, basket_y - 30, PURPLE)
                boss_egg_active = False

        if bomb_active:
            b_rect = pygame.Rect(bomb_x, bomb_y, item_w, item_h)
            if basket_rect.colliderect(b_rect):
                if not consume_shield("BOMB"):
                    lives = 0
                    play_sfx(sfx_bomb, 0.7)
                    add_floating_text("BOOM! GAME OVER", basket_x, basket_y - 30, RED)
                else:
                    add_floating_text("SHIELD! BOM DITAHAN", basket_x, basket_y - 30, CYAN)
                bomb_active = False

        if candy_active:
            c_rect = pygame.Rect(candy_x, candy_y, item_w, item_h)
            if basket_rect.colliderect(c_rect):
                candy_effect_timer = 250
                candy_active = False
                candy_cooldown = 1200
                add_floating_text("SLOW MOTION!", basket_x, basket_y - 20, GREEN)

        if magnet_active:
            m_rect = pygame.Rect(magnet_x, magnet_y, item_w, item_h)
            if basket_rect.colliderect(m_rect):
                magnet_effect_timer = 300
                magnet_active = False
                magnet_cooldown = 1500
                add_floating_text("MAGNET AKTIF!", basket_x, basket_y - 20, RED)

        if score > high_score:
            high_score = score
            player_data["achievement_stats"]["best_score"] = high_score
            process_achievements()
            if not high_score_broken_this_run:
                high_score_broken_this_run = True
                trigger_shake(4, 14)
                zoom_timer = ZOOM_DURATION
                add_floating_text("HIGH SCORE BARU!", WIDTH // 2 - 110, HEIGHT // 3, GOLD)
            for b in bg_items:
                if b["unlock_score"] > 0 and high_score >= b["unlock_score"]:
                    if not b["owned"]:
                        player_data["volcano_claim_ready"] = True
                        add_floating_text("MISI SELESAI! KLAIM BG VOLKANO DI TOKO", WIDTH // 2 - 150, HEIGHT // 2, GOLD)

        if lives <= 0:
            record_leaderboard(score)
            trigger_save()
            state = "GAMEOVER"
        current_bg_data = bg_items[active_bg_index]
        shake_dx = random.randint(-shake_strength, shake_strength) if shake_timer > 0 else 0
        shake_dy = random.randint(-shake_strength, shake_strength) if shake_timer > 0 else 0
        if shake_timer > 0:
            shake_timer -= 1
        if current_bg_data.get("animated", False):
            draw_animated_volcano_bg(current_bg_data["img"])
        else:
            screen.blit(current_bg_data["img"], (shake_dx, shake_dy))

        # Telur utama SELALU pakai tampilan default. Pink/Biru/Mitos sekarang murni
        # "kunci pembuka" buat telur spesial (biar gak dobel sama yang di-drop random).
        active_egg_img = egg_skins[0]["img"]
        screen.blit(active_egg_img, (egg_x + shake_dx, egg_y + shake_dy))

        if golden_egg_active:
            screen.blit(golden_egg_img, (golden_egg_x, golden_egg_y))

        if pink_egg_active:
            screen.blit(egg_skin_pink, (pink_egg_x, pink_egg_y))

        if blue_egg_active:
            screen.blit(egg_skin_blue, (blue_egg_x, blue_egg_y))

        if mythic_egg_active:
            draw_mythic_egg_effect(screen, mythic_egg_x, mythic_egg_y, egg_w, egg_h)
            screen.blit(egg_skin_mythic, (mythic_egg_x, mythic_egg_y))

        if rotten_egg_active:
            screen.blit(rotten_egg_img, (rotten_egg_x, rotten_egg_y))

        if frozen_egg_active:
            ice_glow = pygame.Surface((egg_w + 16, egg_h + 16), pygame.SRCALPHA)
            pygame.draw.ellipse(ice_glow, (150, 230, 255, 70), (0, 0, egg_w + 16, egg_h + 16))
            screen.blit(ice_glow, (frozen_egg_x - 8, frozen_egg_y - 8))
            screen.blit(egg_skin_frozen, (frozen_egg_x, frozen_egg_y))

        if boss_egg_active:
            boss_w_now = int(egg_w * BOSS_EGG_SCALE)
            boss_h_now = int(egg_h * BOSS_EGG_SCALE)
            glow_r = boss_w_now // 2 + 6 + (pygame.time.get_ticks() // 100 % 4)
            pygame.draw.circle(screen, PURPLE, (boss_egg_x + boss_w_now // 2, boss_egg_y + boss_h_now // 2), glow_r, 3)
            boss_img_draw = pygame.transform.smoothscale(golden_egg_img, (boss_w_now, boss_h_now))
            screen.blit(boss_img_draw, (boss_egg_x, boss_egg_y))

        if bomb_active:
            screen.blit(bomb_img, (bomb_x, bomb_y))

        if candy_active:
            screen.blit(candy_img, (candy_x, candy_y))

        if magnet_active:
            screen.blit(magnet_img, (magnet_x, magnet_y))

        active_skin_img = skins[active_skin_index]["img"]
        screen.blit(active_skin_img, (basket_x + shake_dx, basket_y + shake_dy))

        active_skin_id = skins[active_skin_index]["id"]
        if active_skin_id == 4:
            draw_lightning_effect(screen, basket_x, basket_y, basket_w, basket_h)
        elif active_skin_id == 5:
            draw_snow_effect(screen, basket_x, basket_y, basket_w, basket_h)
        elif active_skin_id == 6:
            draw_bat_effect(screen, basket_x, basket_y, basket_w, basket_h)

        for ft in floating_texts[:]:
            txt = font_small.render(ft["text"], True, ft["color"])
            screen.blit(txt, (ft["x"], ft["y"]))
            ft["y"] -= 1
            ft["timer"] -= 1
            if ft["timer"] <= 0:
                floating_texts.remove(ft)

        hud_score = font_small.render(f"Skor: {score}", True, WHITE)
        hud_hs = font_small.render(f"Best: {high_score}", True, GOLD)
        hud_coins = font_small.render(f"Koin Nibo: {coins}", True, GOLD)

        screen.blit(hud_score, (10, 10))
        screen.blit(hud_hs, (10, 32))
        # Koin Nibo diberi area sendiri; tombol power-up tidak menutupinya.
        screen.blit(hud_coins, (WIDTH - hud_coins.get_width() - 10, 10))
        if game_mode == "FEVER_RUSH":
            rush_txt = font_small.render(f"RUSH {mode_time_left / 60:.1f}s", True, GOLD)
            screen.blit(rush_txt, (WIDTH // 2 - rush_txt.get_width() // 2, 10))
        if game_mode == "CHALLENGE":
            mod_txt = font_small.render(f"{challenge_modifier['name']}: {challenge_modifier['desc']}", True, CYAN)
            screen.blit(mod_txt, (WIDTH // 2 - mod_txt.get_width() // 2, 10))
        combo_tier_color = PURPLE if combo_count >= 15 else GOLD if combo_count >= 10 else CYAN if combo_count >= 5 else WHITE
        combo_font = font_medium if combo_count >= 10 else font_small
        combo_txt = combo_font.render(f"COMBO x{combo_count}", True, combo_tier_color)
        if combo_count >= 5:
            pulse = 1.0 + 0.12 * abs(math.sin(pygame.time.get_ticks() / 150))
            combo_txt = pygame.transform.rotozoom(combo_txt, 0, pulse)
        screen.blit(combo_txt, (10, 78))
        if fever_timer > 0:
            fever_txt = font_small.render(f"FEVER {fever_timer / 60:.1f}s  x2", True, GOLD)
            screen.blit(fever_txt, (10, 104))
        if egg_rain_timer > 0:
            rain_pulse = 1.0 + 0.1 * abs(math.sin(pygame.time.get_ticks() / 100))
            rain_txt = font_medium.render("HUJAN TELUR!", True, CYAN)
            rain_txt = pygame.transform.rotozoom(rain_txt, 0, rain_pulse)
            screen.blit(rain_txt, (WIDTH // 2 - rain_txt.get_width() // 2, 40))

        # Nyawa digambar sebagai logo heart, bukan emoji.
        for life_i in range(lives):
            draw_heart_shape(screen, (24 + life_i * 28, 68), 22)

        # Tombol skill dirapikan: ukuran seragam, ada label & badge jumlah,
        # dan progress cooldown biar jelas kapan siap dipakai lagi.
        skill_buttons = [
            (btn_slow_use, slow_time_img, "SLOW", slow_time_count, slow_time_timer, 600),
            (btn_coin_use, coin_boost_img, "COIN x2", coin_boost_count, coin_boost_timer, 900),
            (btn_magnet_use, magnet_img, "MAGNET", magnet_boost_count, magnet_effect_timer, 600),
        ]
        for rect, icon, label, count, cooldown_left, cooldown_max in skill_buttons:
            ready = count > 0 and cooldown_left <= 0
            bg_color = GOLD if ready else ((40, 40, 55) if count > 0 else DARK_GRAY)
            pygame.draw.rect(screen, bg_color, rect, border_radius=10)
            pygame.draw.rect(screen, WHITE if ready else GRAY, rect, width=2, border_radius=10)

            icon_size = rect.height - 26
            icon_draw = pygame.transform.smoothscale(icon, (icon_size, icon_size))
            screen.blit(icon_draw, (rect.centerx - icon_size // 2, rect.y + 4))

            label_txt = font_small.render(label, True, BLACK if ready else WHITE)
            screen.blit(label_txt, (rect.centerx - label_txt.get_width() // 2, rect.bottom - label_txt.get_height() - 3))

            # Badge jumlah charge yang dimiliki, pojok kanan atas tombol.
            if count > 0:
                badge_center = (rect.right - 12, rect.y + 12)
                pygame.draw.circle(screen, RED, badge_center, 11)
                pygame.draw.circle(screen, WHITE, badge_center, 11, 1)
                badge_txt = font_small.render(str(count), True, WHITE)
                screen.blit(badge_txt, (badge_center[0] - badge_txt.get_width() // 2, badge_center[1] - badge_txt.get_height() // 2))

            # Sedang cooldown/aktif: tampilkan sisa detik menimpa ikon.
            if cooldown_left > 0:
                cd_txt = font_small.render(f"{cooldown_left / 60:.0f}s", True, WHITE)
                cd_bg = pygame.Surface((cd_txt.get_width() + 6, cd_txt.get_height() + 2), pygame.SRCALPHA)
                cd_bg.fill((0, 0, 0, 160))
                screen.blit(cd_bg, (rect.centerx - cd_txt.get_width() // 2 - 3, rect.y + 4))
                screen.blit(cd_txt, (rect.centerx - cd_txt.get_width() // 2, rect.y + 5))

        pygame.draw.rect(screen, GRAY, btn_pause, border_radius=6)
        p_symbol = font_small.render("||", True, BLACK)
        screen.blit(p_symbol, (btn_pause.centerx - p_symbol.get_width() // 2, btn_pause.centery - p_symbol.get_height() // 2))

        if candy_effect_timer > 0:
            st_txt = font_small.render("SLOW-MO", True, GREEN)
            screen.blit(st_txt, (10, 80))

        # Status pasif (bukan tombol) tetap ditampilkan ringkas di kanan atas.
        if shield_count > 0:
            sh_txt = font_small.render(f"SHIELD x{shield_count}" + (" AKTIF" if shield_equipped else ""), True, CYAN)
            screen.blit(sh_txt, (WIDTH - sh_txt.get_width() - 10, 34))
        if extra_heart_count > 0:
            eh_txt = font_small.render(f"HEART +{extra_heart_count}", True, RED)
            screen.blit(eh_txt, (WIDTH - eh_txt.get_width() - 10, 56))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save()
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state = "PAUSE"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_pause.collidepoint(event.pos):
                    state = "PAUSE"
                elif btn_slow_use.collidepoint(event.pos) and slow_time_count > 0 and slow_time_timer <= 0:
                    slow_time_timer = 600
                    slow_time_count -= 1
                    player_data["slow_time_count"] = slow_time_count
                    add_floating_text("SLOW TIME 10 DETIK!", WIDTH // 2 - 100, HEIGHT // 2, CYAN)
                    trigger_save()
                elif btn_coin_use.collidepoint(event.pos) and coin_boost_count > 0 and coin_boost_timer <= 0:
                    coin_boost_timer = 900
                    coin_boost_count -= 1
                    player_data["coin_boost_count"] = coin_boost_count
                    add_floating_text("COIN BOOST x2 AKTIF!", WIDTH // 2 - 100, HEIGHT // 2, GOLD)
                    trigger_save()
                elif btn_magnet_use.collidepoint(event.pos) and magnet_boost_count > 0 and magnet_effect_timer <= 0:
                    magnet_effect_timer = int(600 * (1.3 if has_active_pet(2) else 1.0))
                    magnet_boost_count -= 1
                    player_data["magnet_boost_count"] = magnet_boost_count
                    add_floating_text("MAGNET AKTIF 10 DETIK!", WIDTH // 2 - 100, HEIGHT // 2, CYAN)
                    trigger_save()

    elif state == "PAUSE":
        screen.blit(bg_menu, (0, 0))
        draw_panel(pause_panel)

        p_title = font_large.render("PAUSE", True, WHITE)
        screen.blit(p_title, (WIDTH // 2 - p_title.get_width() // 2, int(HEIGHT * 0.28)))

        pygame.draw.rect(screen, GREEN, btn_resume, border_radius=10)
        res_lbl = font_medium.render("LANJUTKAN", True, WHITE)
        screen.blit(res_lbl, (btn_resume.centerx - res_lbl.get_width() // 2, btn_resume.centery - res_lbl.get_height() // 2))

        pygame.draw.rect(screen, RED, btn_menu_pause, border_radius=10)
        menu_lbl = font_medium.render("MENU UTAMA", True, WHITE)
        screen.blit(menu_lbl, (btn_menu_pause.centerx - menu_lbl.get_width() // 2, btn_menu_pause.centery - menu_lbl.get_height() // 2))

        pygame.draw.rect(screen, DARK_GRAY, btn_quit, border_radius=10)
        quit_lbl = font_medium.render("KELUAR", True, WHITE)
        screen.blit(quit_lbl, (btn_quit.centerx - quit_lbl.get_width() // 2, btn_quit.centery - quit_lbl.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                trigger_save()
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state = "GAME"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_resume.collidepoint(event.pos):
                    state = "GAME"
                elif btn_menu_pause.collidepoint(event.pos):
                    trigger_save()
                    state = "MENU"
                elif btn_quit.collidepoint(event.pos):
                    trigger_save()
                    running = False

    elif state == "GAMEOVER":
        screen.blit(bg_menu, (0, 0))
        draw_panel(go_panel, border_color=RED)

        go_txt = font_large.render("GAME OVER", True, RED)
        screen.blit(go_txt, (WIDTH // 2 - go_txt.get_width() // 2, int(HEIGHT * 0.18)))

        res_txt = font_medium.render(f"Skor Akhir: {score}", True, WHITE)
        screen.blit(res_txt, (WIDTH // 2 - res_txt.get_width() // 2, int(HEIGHT * 0.27)))

        hs_go_txt = font_medium.render(f"High Score: {high_score}", True, GOLD)
        screen.blit(hs_go_txt, (WIDTH // 2 - hs_go_txt.get_width() // 2, int(HEIGHT * 0.34)))

        # Leaderboard lokal: 5 skor terbaik di perangkat ini.
        board = player_data.get("leaderboard", [])
        board_title = font_small.render("TOP 5 SKOR LOKAL", True, CYAN)
        screen.blit(board_title, (WIDTH // 2 - board_title.get_width() // 2, int(HEIGHT * 0.40)))
        for i, s in enumerate(board[:5]):
            row = font_small.render(f"{i + 1}. {s}", True, WHITE if s != score else GOLD)
            screen.blit(row, (WIDTH // 2 - row.get_width() // 2, int(HEIGHT * 0.40) + 20 + i * 18))

        pygame.draw.rect(screen, (60, 140, 220), btn_screenshot, border_radius=8)
        ss_lbl = font_small.render("SIMPAN SCREENSHOT SKOR", True, WHITE)
        screen.blit(ss_lbl, (btn_screenshot.centerx - ss_lbl.get_width() // 2, btn_screenshot.centery - ss_lbl.get_height() // 2))
        if screenshot_message_timer > 0:
            ss_msg = font_small.render(screenshot_message, True, GREEN)
            screen.blit(ss_msg, (WIDTH // 2 - ss_msg.get_width() // 2, btn_screenshot.bottom + 2))

        pygame.draw.rect(screen, GREEN, btn_restart, border_radius=10)
        rest_lbl = font_medium.render("MAIN LAGI", True, WHITE)
        screen.blit(rest_lbl, (btn_restart.centerx - rest_lbl.get_width() // 2, btn_restart.centery - rest_lbl.get_height() // 2))

        pygame.draw.rect(screen, GOLD, btn_menu_go, border_radius=10)
        menu_lbl = font_medium.render("MENU UTAMA", True, BLACK)
        screen.blit(menu_lbl, (btn_menu_go.centerx - menu_lbl.get_width() // 2, btn_menu_go.centery - menu_lbl.get_height() // 2))

        if screenshot_message_timer > 0:
            screenshot_message_timer -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_restart.collidepoint(event.pos):
                    reset_game()
                    state = "GAME"
                elif btn_menu_go.collidepoint(event.pos):
                    state = "MENU"
                elif btn_screenshot.collidepoint(event.pos):
                    saved_path = save_score_screenshot(screen, score)
                    screenshot_message = "TERSIMPAN!" if saved_path else "GAGAL SIMPAN"
                    screenshot_message_timer = 90

    if mythic_catch_flash_timer > 0:
        mythic_catch_flash_timer -= 1
        flash_alpha = int(60 * (mythic_catch_flash_timer / 6))
        flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash_surf.fill((170, 120, 255, flash_alpha))
        screen.blit(flash_surf, (0, 0))

    if zoom_timer > 0:
        zoom_timer -= 1
        zoom_progress = zoom_timer / ZOOM_DURATION
        zoom_scale = 1.0 + 0.05 * math.sin(zoom_progress * math.pi)
        zoomed = pygame.transform.smoothscale(screen, (int(WIDTH * zoom_scale), int(HEIGHT * zoom_scale)))
        offset_x = (zoomed.get_width() - WIDTH) // 2
        offset_y = (zoomed.get_height() - HEIGHT) // 2
        screen.blit(zoomed, (-offset_x, -offset_y))

    if fade_in_timer > 0:
        fade_in_timer -= 1
        fade_alpha = int(255 * (fade_in_timer / FADE_IN_DURATION))
        fade_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fade_surf.fill((0, 0, 0, fade_alpha))
        screen.blit(fade_surf, (0, 0))

    if state != "SPLASH":
        set_bgm_track("gameplay" if state == "GAME" else "menu")

    pygame.display.flip()

pygame.quit()
sys.exit()
