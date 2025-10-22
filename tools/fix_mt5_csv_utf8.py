def normalize_date(s: str) -> str:
    s = s.strip()
    # yyyy.MM.dd HH:mm  -> yyyy-MM-dd HH:mm
    if len(s) >= 16 and s[4] == "." and s[7] == "." and s[10] == " ":
        return f"{s[0:4]}-{s[5:7]}-{s[8:10]} {s[11:16]}"
    # yyyy.MM.dd (sin hora) -> yyyy-MM-dd 00:00
    if len(s) == 10 and s[4] == "." and s[7] == ".":
        return f"{s[0:4]}-{s[5:7]}-{s[8:10]} 00:00"
    # Si ya viene con guiones, déjalo igual
    return s

def convert_file(csv_path: Path):
    txt = read_text_safe(csv_path)
    if not txt or not txt.strip():
        print(f"⚠️ {csv_path.name}: vacío o ilegible (se omite)")
        return

    lines = txt.replace("\r\n","\n").replace("\r","\n").split("\n")
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
        if not header_seen and looks_like_header(parts):
            header_seen = True
            continue
        parts = (parts + [""]*6)[:6]

        dt_raw = parts[0]
        o,h,l,c = parts[1:5]

        ok_ohlc = all(is_number(x) for x in (o,h,l,c))
        if not ok_ohlc:
            bad += 1
            continue

        dt_norm = normalize_date(dt_raw)
        # Validación mínima del resultado
        ok_dt = len(dt_norm) >= 16 and dt_norm[4] == "-" and dt_norm[7] == "-" and dt_norm[10] == " "
        if not ok_dt:
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
