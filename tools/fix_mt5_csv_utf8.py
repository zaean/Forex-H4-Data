# -*- coding: utf-8 -*-
import csv
import os
from pathlib import Path  # ✅ IMPORTANTE: evita el NameError
from datetime import datetime

HEADERS = ["datetime", "open", "high", "low", "close", "volume"]

def detect_sep(lines):
    """Detecta el separador usado (coma o punto y coma)."""
    if not lines:
        return ","
    sample = lines[0]
    if ";" in sample and sample.count(";") > sample.count(","):
        return ";"
    return ","

def is_number(x: str):
    try:
        float(x)
        return True
    except:
        return False

def looks_like_header(parts):
    header_keywords = {"datetime", "open", "high", "low", "close"}
    return any(h.lower() in header_keywords for h in parts)

def read_text_safe(p: Path):
    """Lee un archivo con auto detección de codificación."""
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return p.read_text(encoding=enc)
        except Exception:
            continue
    return None

def normalize_date(s: str) -> str:
    """Convierte fechas tipo '1993.04.12 00:00' → '1993-04-12 00:00'."""
    s = s.strip()
    if len(s) >= 16 and s[4] == "." and s[7] == "." and s[10] == " ":
        return f"{s[0:4]}-{s[5:7]}-{s[8:10]} {s[11:16]}"
    if len(s) == 10 and s[4] == "." and s[7] == ".":
        return f"{s[0:4]}-{s[5:7]}-{s[8:10]} 00:00"
    return s

def convert_file(csv_path: Path):
    txt = read_text_safe(csv_path)
    if not txt or not txt.strip():
        print(f"⚠️ {csv_path.name}: vacío o ilegible (omitido)")
        return

    lines = txt.replace("\r\n","\n").replace("\r","\n").split("\n")
    non_empty = [ln for ln in lines if ln.strip()]
    sep = detect_sep(non_empty)

    rows_out = []
    added = 0
    bad = 0
    header_seen = False

    for ln in lines:
        if not ln or not ln.strip():
            continue
        parts = [p.strip() for p in ln.split(sep)]
        if not header_seen and looks_like_header(parts):
            header_seen = True
            continue
        parts = (parts + [""]*6)[:6]

        dt_raw = parts[0]
        o,h,l,c = parts[1:5]

        if not all(is_number(x) for x in (o,h,l,c)):
            bad += 1
            continue

        dt_norm = normalize_date(dt_raw)
        if not dt_norm or len(dt_norm) < 10:
            bad += 1
            continue

        vol = parts[5].strip()
        if not is_number(vol):
            vol = "0"

        rows_out.append([dt_norm, o, h, l, c, vol])
        added += 1

    if not rows_out:
        print(f"❗ {csv_path.name}: no se encontraron filas válidas (sep='{sep}') — revisa el origen")
        return

    out_text = ",".join(HEADERS) + "\n" + "\n".join([",".join(r) for r in rows_out])
    csv_path.write_text(out_text, encoding="utf-8")
    print(f"✅ {csv_path.name} → UTF-8 normalizado ({added} filas, {bad} descartadas)")

def main():
    repo = Path(__file__).resolve().parent.parent
    for f in repo.glob("*.csv"):
        convert_file(f)

if __name__ == "__main__":
    main()
