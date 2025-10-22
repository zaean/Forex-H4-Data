# tools/fix_mt5_csv_overwrite.py
# Limpia CSVs de MT5 y sobrescribe si el archivo está sano; si no, crea *_FIXED.csv.
# Autodetecta la carpeta del repo a partir de la ubicación del script.

import csv
import shutil
from pathlib import Path

# Carpeta raíz del repo (padre de /tools)
CARPETA = Path(__file__).resolve().parents[1]

HEADERS = ["datetime", "open", "high", "low", "close", "volume"]
MAX_COLS = 6
BAD_TOLERANCE = 0.10   # >10% filas inválidas => no sobrescribe (genera *_FIXED.csv)
BACKUP_EXT = ".bak"

def read_text_any(path: Path) -> str:
    for enc in ("utf-16le", "utf-8-sig", "utf-8"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return path.read_bytes().decode("utf-8", errors="ignore")

def detect_sep(line: str) -> str:
    if "\t" in line: return "\t"
    if ";" in line:  return ";"
    return ","  # por defecto

def looks_like_header(line: str) -> bool:
    l = line.strip().lower()
    return all(k in l for k in ("datetime","open","high","low","close"))

def clean_rows(lines: list[str]):
    if not lines: return [], 0, 0
    sep = detect_sep(lines[0])
    start_idx = 1 if looks_like_header(lines[0]) else 0

    total = bad = 0
    rows = []
    for i in range(start_idx, len(lines)):
        raw = lines[i].strip()
        if not raw:
            continue
        parts = raw.split(sep)

        total += 1
        parts = parts[:MAX_COLS] if len(parts) else [""]*MAX_COLS
        if len(parts) < MAX_COLS:
            parts += [""]*(MAX_COLS-len(parts))

        dt = parts[0].strip()
        ok_dt = len(dt)>=10 and dt[4] in ".-/" and dt[7] in ".-/"
        def is_num(s:str):
            s = s.replace(",", "").replace(" ", "")
            try: float(s); return True
            except: return False
        ok_ohlc = all(is_num(x) for x in parts[1:5])

        if not (ok_dt and ok_ohlc): bad += 1
        rows.append(parts)
    return rows, total, bad

def write_csv(path: Path, rows, overwrite: bool):
    if overwrite:
        bak = path.with_suffix(path.suffix + BACKUP_EXT)
        try:
            shutil.copy2(path, bak)
            print(f"   • Backup: {bak.name}")
        except Exception as e:
            print(f"   • Aviso backup: {e}")
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8", newline="") as fw:
            w = csv.writer(fw); w.writerow(HEADERS); w.writerows(rows)
        tmp.replace(path)
        print(f"✅ Sobrescrito: {path.relative_to(CARPETA)}")
        return path
    else:
        out = path.with_name(path.stem + "_FIXED.csv")
        with out.open("w", encoding="utf-8", newline="") as fw:
            w = csv.writer(fw); w.writerow(HEADERS); w.writerows(rows)
        print(f"⚠️ Basura alta → {out.relative_to(CARPETA)} (original intacto)")
        return out

def process_file(fp: Path):
    txt = read_text_any(fp)
    lines = [ln for ln in txt.replace("\r\n","\n").replace("\r","\n").split("\n") if ln.strip()]
    rows, total, bad = clean_rows(lines)
    if not rows:
        print(f"⚠️ Vacío/ilegible: {fp.relative_to(CARPETA)}")
        return False
    ratio = bad / max(total,1)
    print(f"→ {fp.relative_to(CARPETA)}: {total} filas, {bad} inválidas ({ratio:.1%})")
    write_csv(fp, rows, overwrite = (ratio <= BAD_TOLERANCE))
    return True

def main():
    if not CARPETA.exists():
        print(f"Ruta no encontrada: {CARPETA}")
        return 1
    csvs = list(CARPETA.glob("*.csv"))
    if not csvs:
        # si usas subcarpetas, cambia a rglob("*.csv")
        print("No hay CSV en la raíz del repo.")
        return 0
    for f in csvs:
        process_file(f)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
