# tools/fix_mt5_csv_utf8.py
# Convierte CSVs MT5 a UTF-8 con coma, agrega encabezado estándar y filtra basura.

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HEADERS = ["datetime","open","high","low","close","volume"]

PREFERRED_ENCODINGS = ("utf-16le","utf-8-sig","utf-8","latin-1")

def read_text_safe(p: Path) -> str:
    for enc in PREFERRED_ENCODINGS:
        try:
            txt = p.read_text(encoding=enc)
            if txt is not None:
                return txt
        except Exception:
            continue
    # último recurso
    return p.read_bytes().decode("utf-8","ignore")

def first_non_empty(lines: list[str]) -> str | None:
    for ln in lines:
        if ln and ln.strip():
            return ln
    return None

def detect_sep(sample_lines: list[str]) -> str:
    # Analiza hasta 50 líneas no vacías y elige el separador más frecuente
    counts = {",":0, ";":0, "\t":0}
    for ln in sample_lines[:50]:
        if not ln.strip(): 
            continue
        counts[","] += ln.count(",")
        counts[";"] += ln.count(";")
        counts["\t"] += ln.count("\t")
    # por defecto coma si todos 0
    return max(counts, key=counts.get) if any(counts.values()) else ","

def is_number(s: str) -> bool:
    s = s.strip().replace(" ", "").replace(",", "")
    try:
        float(s)
        return True
    except Exception:
        return False

def looks_like_header(parts: list[str]) -> bool:
    l = ",".join([x.lower() for x in parts])
    return ("datetime" in l and "open" in l and "high" in l and "low" in l and "close" in l)

def convert_file(csv_path: Path):
    txt = read_text_safe(csv_path)
    if not txt or not txt.strip():
        print(f"⚠️ {csv_path.name}: vacío o ilegible (se omite)")
        return

    # normalizar saltos de línea
    lines = txt.replace("\r\n","\n").replace("\r","\n").split("\n")
    # detectar separador con primeras no-vacías
    non_empty = [ln for ln in lines if ln.strip()]
    sep = detect_sep(non_empty)

    rows_out: list[list[str]] = []
    added = 0
    bad = 0

    header_seen = False
    for ln in lines:
        if not ln or not ln.strip():
            continue
        parts = [p.strip() for p in ln.split(sep)]
        # Si parece encabezado, lo ignoramos (vamos a poner el nuestro)
        if not header_seen and looks_like_header(parts):
            header_seen = True
            continue
        # Aseguramos 6 columnas (si hay más, recortamos; si hay menos, completamos)
        parts = (parts + [""]*6)[:6]

        dt = parts[0]
        o,h,l,c = parts[1:5]

        # Validación básica: fecha con yyyy? y separadores y OHLC numéricos
        ok_dt = len(dt) >= 10 and dt[4] in ".-/" and dt[7] in ".-/"
        ok_ohlc = all(is_number(x) for x in (o,h,l,c))

        if ok_dt and ok_ohlc:
            # volumen puede ir vacío; normalizamos vacío a "0"
            vol = parts[5].strip()
            if not is_number(vol):
                vol = "0"
            rows_out.append([dt, o, h, l, c, vol])
            added += 1
        else:
            bad += 1

    if not rows_out:
        print(f"❗ {csv_path.name}: no se encontraron filas válidas (sep='{sep}') — revisa el origen")
        return

    # escribir como UTF-8 con coma
    out_text = ",".join(HEADERS) + "\n" + "\n".join([",".join(r) for r in rows_out])
    csv_path.write_text(out_text, encoding="utf-8")
    print(f"✅ {csv_path.name} → UTF-8 normalizado ({added} filas, {bad} descartadas)")

def main():
    # Solo raíz del repo; si deseas subcarpetas usa rglob("*.csv")
    files = list(REPO.glob("*.csv"))
    if not files:
        print("ℹ️ No hay CSV en la raíz del repositorio. (Usa rglob si están en subcarpetas)")
        return
    for f in files:
        try:
            convert_file(f)
        except Exception as e:
            print(f"❌ Error con {f.name}: {e}")

if __name__ == "__main__":
    main()
