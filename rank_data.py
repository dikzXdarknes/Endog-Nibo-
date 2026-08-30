# rank_data.py
# Sistem RANK berdasarkan TOTAL telur yang pernah ditangkap seumur hidup
# (akumulasi dari semua sesi main, bukan skor 1 game). Jadi kalau telur
# yang didapat kurang buat naik rank, tinggal main lagi nanti nambah terus.

# (nama_rank, ambang_batas_total_telur)
RANK_TIERS = [
    ("Peternak Pemula", 0),
    ("Peternak Perunggu", 50),
    ("Peternak Perak", 150),
    ("Peternak Emas", 300),
    ("Peternak Platinum", 600),
    ("Peternak Elite", 1000),
    ("Peternak Master", 2000),
    ("Peternak Grandmaster", 4000),
    ("Peternak Epic", 7000),
    ("Peternak Legenda", 12000),
    ("Peternak Mitos", 20000),
    ("Peternak Mitos Agung", 35000),
    ("Peternak Mitos Abadi", 60000),
]


def get_rank_info(total_eggs):
    """
    Mengembalikan dict berisi info rank saat ini berdasarkan total telur
    seumur hidup: index, nama, ambang batas rank ini, ambang batas rank
    berikutnya (None kalau sudah rank tertinggi), dan progress 0.0-1.0
    menuju rank berikutnya.
    """
    total_eggs = max(0, int(total_eggs))
    current_index = 0
    for i, (_, threshold) in enumerate(RANK_TIERS):
        if total_eggs >= threshold:
            current_index = i
        else:
            break

    name = RANK_TIERS[current_index][0]
    current_threshold = RANK_TIERS[current_index][1]

    if current_index + 1 < len(RANK_TIERS):
        next_name, next_threshold = RANK_TIERS[current_index + 1]
        span = max(1, next_threshold - current_threshold)
        progress = min(1.0, (total_eggs - current_threshold) / span)
    else:
        next_name, next_threshold = None, None
        progress = 1.0

    return {
        "index": current_index,
        "name": name,
        "threshold": current_threshold,
        "next_name": next_name,
        "next_threshold": next_threshold,
        "progress": progress,
        "total_eggs": total_eggs,
    }


def get_rank_coin_bonus(rank_index):
    """
    Bonus koin permanen dari progres RANK: +2% per tingkat rank yang sudah
    dicapai. Ini bikin push rank berasa gunanya, bukan cuma gengsi doang.
    """
    return max(0, int(rank_index)) * 0.02


PRESTIGE_EGGS_PER_STAR = 20000

def get_prestige_stars(total_eggs):
    """
    Buat pemain yang udah nyampe rank tertinggi: tiap tambahan 20.000 telur
    lagi dapet 1 bintang prestige. Non-destruktif, progress lama tetap aman.
    """
    max_threshold = RANK_TIERS[-1][1]
    total_eggs = max(0, int(total_eggs))
    if total_eggs < max_threshold:
        return 0
    return (total_eggs - max_threshold) // PRESTIGE_EGGS_PER_STAR

