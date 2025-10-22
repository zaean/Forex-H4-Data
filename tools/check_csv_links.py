import requests
import os

# Repositorio y carpeta base
USER = "zaean"
REPO = "Forex-H4-Data"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/"
LOCAL_PATH = r"C:\Users\Usert\Documents\Forex\Forex-H4-Data"

def check_links():
    csv_files = [f for f in os.listdir(LOCAL_PATH) if f.lower().endswith(".csv")]
    print(f"\n🔍 Verificando {len(csv_files)} archivos CSV en GitHub:\n")

    for f in csv_files:
        url = BASE_URL + f
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                print(f"✅ {f} → OK ({url})")
            else:
                print(f"❌ {f} → ERROR {r.status_code} ({url})")
        except Exception as e:
            print(f"⚠️ {f} → fallo de conexión: {e}")

if __name__ == "__main__":
    check_links()
