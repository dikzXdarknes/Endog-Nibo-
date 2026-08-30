# redeem_code_generator.py
# Jalanin script ini di HP/laptop kamu (bukan di game) tiap ada yang beli Koin Nibo.
# CARA PAKAI:
#   python3 redeem_code_generator.py
# lalu tinggal ikutin instruksinya (masukin jumlah koin & nomor urut pembelian).
#
# PENTING: REDEEM_SECRET_KEY di bawah ini HARUS PERSIS SAMA dengan yang ada di
# main.py (variabel REDEEM_SECRET_KEY). Kalau kamu ganti salah satu, ganti juga
# yang satunya, atau kode yang dihasilkan gak bakal valid di game.

import hmac
import hashlib

REDEEM_SECRET_KEY = "Rf30Fcu2_gUUvPL4TZEeuD3VtuvNgEa3"


def generate_redeem_code(amount, serial):
    payload = f"{amount}:{serial}"
    sig = hmac.new(REDEEM_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:6].upper()
    return f"NIBO-{amount}-{serial}-{sig}"


if __name__ == "__main__":
    print("=== Generator Kode Redeem Koin Nibo ===")
    print("(Ctrl+C buat keluar)\n")
    while True:
        try:
            amount = int(input("Jumlah Koin Nibo yang dibeli: ").strip())
            serial = int(input("Nomor urut pembelian (naikin tiap transaksi, misal 1, 2, 3, ...): ").strip())
        except ValueError:
            print("Input harus angka ya. Coba lagi.\n")
            continue
        except KeyboardInterrupt:
            print("\nSelesai.")
            break

        code = generate_redeem_code(amount, serial)
        print(f"\n>>> KODE: {code}")
        print("Kirim kode ini ke pembeli. Simpan juga nomor urutnya biar gak kepakai dua kali.\n")
