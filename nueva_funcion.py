# ══════════════════════════════════════════════════════════════════════════════
# 2. PORTADA EDITORIAL «NOTICIAS DEL DÍA» 1080×1080 (Periódico Moderno)
# ══════════════════════════════════════════════════════════════════════════════
def pegar_imagen_redondeada_ed(canvas, img_path, box, radio=6):
    """Ajusta y recorta una imagen con esquinas redondeadas y la pega en el lienzo."""
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    if not img_path or not os.path.exists(img_path):
        return
    try:
        im = Image.open(img_path).convert("RGBA")
        im_ratio = im.width / im.height
        target_ratio = w / h
        if im_ratio > target_ratio:
            new_h = h
            new_w = int(h * im_ratio)
        else:
            new_w = w
            new_h = int(w / im_ratio)
        im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
        crop_x = (new_w - w) // 2
        crop_y = (new_h - h) // 2
        im = im.crop((crop_x, crop_y, crop_x + w, crop_y + h))
        mask = Image.new("L", (w, h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, w, h], radius=radio, fill=255)
        canvas.paste(im, (x1, y1), mask)
    except Exception as e:
        print("Advertencia pegando imagen " + str(img_path) + ": " + str(e))


def dibujar_pestana_editorial(draw, x, y, ancho, alto, texto, font, corte=16):
    """Dibuja pestaña azul marino con corte sesgado y filete dorado."""
    puntos = [(x, y), (x + ancho, y), (x + ancho - corte, y + alto), (x, y + alto)]
    draw.polygon(puntos, fill=(8, 28, 66, 255))
    draw.line([(x + ancho, y), (x + ancho - corte, y + alto)], fill=GOLD_ACCENT, width=3)
    draw.text((x + 10, y + alto // 2), texto, fill=(255, 255, 255, 255), font=font, anchor="lm")


def crear_boletin_grafico_cuadrado(datos_bcv, datos_noticia, datos_db):
    """
    Genera la portada editorial NOTICIAS DEL DIA 1080x1080 px.
    Estiloperiodico moderno: cabecera azul marino, globo terraqueo,
    franja de cotizaciones en tiempo real, 5 noticias (2+3), frase universal,
    efemerides de Venezuela y pie institucional dorado.
    Conserva la misma firma de argumentos que la version anterior.
    """
    import re as _re
    print("[PORTADA EDITORIAL 1080x1080] Maquetando NOTICIAS DEL DIA...")

    W, H = 1080, 1080
    canvas = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # ── FUENTES EDITORIALES ──
    def carga(nombre, tam):
        return cargar_fuente(os.path.join("C:\\Windows\\Fonts", nombre), tam)

    f_header_title = carga("georgiab.ttf",  52)
    f_header_sub   = carga("georgiai.ttf",  22)
    f_date_day     = carga("segoeui.ttf",   15)
    f_date_num     = carga("segoeuib.ttf",  46)
    f_date_month   = carga("segoeuib.ttf",  15)
    f_date_year    = carga("segoeuib.ttf",  13)
    f_tab          = carga("segoeuib.ttf",  14)
    f_tab_lg       = carga("segoeuib.ttf",  15)
    f_cot_tag      = carga("segoeuib.ttf",  15)
    f_rate_title   = carga("segoeuib.ttf",  14)
    f_rate_val     = carga("segoeuib.ttf",  25)
    f_news_t1      = carga("georgiab.ttf",  18)
    f_news_r1      = carga("segoeui.ttf",   13)
    f_news_t2      = carga("georgiab.ttf",  15)
    f_news_r2      = carga("segoeui.ttf",   12)
    f_frase_text   = carga("georgiaz.ttf",  22)
    f_frase_author = carga("segoeuib.ttf",  14)
    f_efem_date    = carga("georgiab.ttf",  19)
    f_efem_body    = carga("segoeui.ttf",   14)
    f_footer       = carga("segoeuib.ttf",  13)

    ahora = datetime.now()
    dias_s  = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    dias_es = ["Lunes", "Martes", "Mi\u00e9rcoles", "Jueves", "Viernes", "S\u00e1bado", "Domingo"]
    meses_s = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    dia_nombre = dias_es[ahora.weekday()]
    dia_num    = str(ahora.day)
    mes_nombre = meses_s[ahora.month - 1]
    ano_str    = str(ahora.year)

    # ══════════════════════════════════════════════════════════════
    # A. CABECERA (Y: 0-145)
    # ══════════════════════════════════════════════════════════════
    HH = 145
    header_grad = crear_degradado_vertical(W, HH, (8, 32, 75, 255), (4, 18, 46, 255))
    canvas.paste(header_grad, (0, 0))
    draw.line([(0, 1), (W, 1)],       fill=(225, 185, 75, 255), width=2)
    draw.line([(0, HH-2), (W, HH-2)], fill=(225, 185, 75, 255), width=3)

    globe_path = os.path.join(BASE_DIR, "assets", "general", "globe.png")
    if os.path.exists(globe_path):
        try:
            gim = Image.open(globe_path).convert("RGBA")
            gim = gim.resize((150, 125), Image.Resampling.LANCZOS)
            canvas.paste(gim, (12, 10), gim)
        except Exception:
            pass

    cx_hdr = (170 + 910) // 2
    draw.text((cx_hdr, 48),  "NOTICIAS DEL D\u00cdA",                  fill=(255,255,255,255), font=f_header_title, anchor="mm")
    draw.text((cx_hdr, 104), "La actualidad en una sola mirada", fill=(241,245,249,255), font=f_header_sub,   anchor="mm")

    bx1, by1, bx2, by2 = 915, 12, 1055, 132
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=12, fill=(255,255,255,255))
    cx_b = (bx1 + bx2) // 2
    draw.text((cx_b, by1+18),  dia_nombre, fill=(51,65,85,255),  font=f_date_day,   anchor="mm")
    draw.text((cx_b, by1+54),  dia_num,    fill=(6,24,58,255),   font=f_date_num,   anchor="mm")
    draw.text((cx_b, by1+90),  mes_nombre, fill=(15,23,42,255),  font=f_date_month, anchor="mm")
    draw.text((cx_b, by1+109), ano_str,    fill=(71,85,105,255), font=f_date_year,  anchor="mm")

    # ══════════════════════════════════════════════════════════════
    # B. FRANJA DE COTIZACIONES (Y: 154-232)
    # ══════════════════════════════════════════════════════════════
    y_cot, h_cot = 154, 78
    draw.rectangle([0, y_cot, W, y_cot+h_cot], fill=(255,255,255,255), outline=(226,232,240,255), width=1)

    w_tab_cot, corte_cot = 205, 22
    puntos_cot = [(10, y_cot+6), (10+w_tab_cot, y_cot+6),
                  (10+w_tab_cot-corte_cot, y_cot+h_cot-6), (10, y_cot+h_cot-6)]
    draw.polygon(puntos_cot, fill=(8,28,66,255))
    draw.line([(10+w_tab_cot, y_cot+6), (10+w_tab_cot-corte_cot, y_cot+h_cot-6)], fill=GOLD_ACCENT, width=4)
    draw.text((22, y_cot+24), "COTIZACIONES", fill=(255,255,255,255), font=f_cot_tag, anchor="lm")
    draw.text((22, y_cot+48), "DEL D\u00cdA",      fill=(255,255,255,255), font=f_cot_tag, anchor="lm")

    usd_val = datos_bcv.get("usd",     "No disp.") + " Bs"
    eur_val = datos_bcv.get("eur",     "No disp.") + " Bs"
    bin_val = datos_bcv.get("binance", "No disp.") + " Bs"
    div_blocks = [
        {"x": 235, "icon": os.path.join(BASE_DIR,"assets","icons","usd.png"),     "title": "D\u00d3LAR BCV",   "val": usd_val},
        {"x": 510, "icon": os.path.join(BASE_DIR,"assets","icons","eur.png"),     "title": "EURO BCV",    "val": eur_val},
        {"x": 775, "icon": os.path.join(BASE_DIR,"assets","icons","binance.png"), "title": "BINANCE P2P", "val": bin_val},
    ]
    for blk in div_blocks:
        if os.path.exists(blk["icon"]):
            try:
                ico = Image.open(blk["icon"]).convert("RGBA")
                ico = ico.resize((44, 44), Image.Resampling.LANCZOS)
                canvas.paste(ico, (blk["x"], y_cot+16), ico)
            except Exception:
                pass
        tx = blk["x"] + 54
        draw.text((tx, y_cot+25), blk["title"], fill=(15,23,42,255), font=f_rate_title, anchor="lm")
        draw.text((tx, y_cot+52), blk["val"],   fill=(6,24,58,255),  font=f_rate_val,   anchor="lm")

    # ══════════════════════════════════════════════════════════════
    # C. NOTICIAS: 5 piezas en cuadricula 2+3
    # ══════════════════════════════════════════════════════════════
    CATS_DEFAULT = ["VENEZUELA", "ECONOM\u00cdA", "INTERNACIONALES", "MARACAIBO", "SALUD"]
    base_assets  = os.path.join(BASE_DIR, "assets", "categories")

    noticias_raw = datos_db.get("titulares_medios", [])
    noticias_5 = []
    for i in range(5):
        cat_def = CATS_DEFAULT[i]
        img_def = os.path.join(base_assets, cat_def.lower().replace("\u00ed","i").replace("\u00f3","o") + ".jpg")
        # Intentar nombre con acento primero, luego sin acento
        if not os.path.exists(img_def):
            img_def = os.path.join(base_assets, "venezuela.jpg")
        if i < len(noticias_raw):
            item = dict(noticias_raw[i])
            if "categoria" not in item:
                item["categoria"] = cat_def
            if not item.get("imagen_local") or not os.path.exists(item.get("imagen_local", "")):
                item["imagen_local"] = img_def
            if not item.get("resumen"):
                item["resumen"] = "Informacion destacada del sector y su impacto en el acontecer nacional."
            noticias_5.append(item)
        else:
            noticias_5.append({
                "categoria": cat_def,
                "titular":   "Actualidad en " + cat_def.lower(),
                "resumen":   "Reporte especial sobre el desarrollo de este sector clave.",
                "imagen_local": img_def,
            })

    # Helper para obtener asset por categoria
    def asset_cat(cat):
        mapa = {
            "VENEZUELA": "venezuela.jpg",
            "ECONOM\u00cdA": "economia.jpg",
            "ECONOMIA": "economia.jpg",
            "INTERNACIONALES": "internacionales.jpg",
            "MARACAIBO": "maracaibo.jpg",
            "SALUD": "salud.jpg",
        }
        fname = mapa.get(cat.upper(), "venezuela.jpg")
        return os.path.join(base_assets, fname)

    # Fila 1: 2 noticias (Y: 244-484)
    y_r1, h_r1, w_r1 = 244, 240, 522

    for col_idx in range(2):
        n = noticias_5[col_idx]
        x0 = 12 + col_idx * (w_r1 + 12)
        draw.rounded_rectangle([x0, y_r1, x0+w_r1, y_r1+h_r1],
                                radius=8, fill=(255,255,255,255), outline=(203,213,225,255), width=1)
        dibujar_pestana_editorial(draw, x0, y_r1, 155, 30, n.get("categoria",""), f_tab)
        img_n = n.get("imagen_local") or asset_cat(n.get("categoria","VENEZUELA"))
        pegar_imagen_redondeada_ed(canvas, img_n, [x0+10, y_r1+38, x0+206, y_r1+h_r1-10], radio=6)
        t_lines = wrap_text(n.get("titular", ""), f_news_t1, 290)
        ty = y_r1 + 44
        for line in t_lines[:3]:
            draw.text((x0+218, ty), line, fill=(15,23,42,255), font=f_news_t1, anchor="lt")
            ty += 23
        r_lines = wrap_text(n.get("resumen", ""), f_news_r1, 290)
        ty += 6
        for line in r_lines[:3]:
            draw.text((x0+218, ty), line, fill=(51,65,85,255), font=f_news_r1, anchor="lt")
            ty += 18

    # Fila 2: 3 noticias (Y: 494-745)
    y_r2, h_r2, w_r2, gap_r2 = 494, 251, 344, 12
    for idx, noti in enumerate(noticias_5[2:5]):
        nx = 12 + idx * (w_r2 + gap_r2)
        draw.rounded_rectangle([nx, y_r2, nx+w_r2, y_r2+h_r2],
                                radius=8, fill=(255,255,255,255), outline=(203,213,225,255), width=1)
        dibujar_pestana_editorial(draw, nx, y_r2, 148, 28, noti.get("categoria",""), f_tab)
        img_n2 = noti.get("imagen_local") or asset_cat(noti.get("categoria","VENEZUELA"))
        pegar_imagen_redondeada_ed(canvas, img_n2, [nx+8, y_r2+36, nx+128, y_r2+h_r2-8], radio=6)
        tx_pos = nx + 136
        tw_max = w_r2 - 144
        t_lines = wrap_text(noti.get("titular", ""), f_news_t2, tw_max)
        ty = y_r2 + 40
        for line in t_lines[:3]:
            draw.text((tx_pos, ty), line, fill=(15,23,42,255), font=f_news_t2, anchor="lt")
            ty += 20
        r_lines = wrap_text(noti.get("resumen", ""), f_news_r2, tw_max)
        ty += 6
        for line in r_lines[:3]:
            draw.text((tx_pos, ty), line, fill=(51,65,85,255), font=f_news_r2, anchor="lt")
            ty += 16

    # ══════════════════════════════════════════════════════════════
    # D. FRASE UNIVERSAL + EFEMERIDES (Y: 757-1025)
    # ══════════════════════════════════════════════════════════════
    y_bot, h_bot, w_bot = 757, 268, 522

    # Frase Universal (izquierda)
    grad_frase = crear_degradado_vertical(w_bot, h_bot, (255,253,247,255), (254,247,234,255))
    canvas.paste(grad_frase, (12, y_bot))
    draw.rounded_rectangle([12, y_bot, 12+w_bot, y_bot+h_bot], radius=8, outline=(203,213,225,255), width=1)
    dibujar_pestana_editorial(draw, 12, y_bot, 220, 32, "LA FRASE UNIVERSAL", f_tab_lg)
    pegar_imagen_redondeada_ed(canvas, os.path.join(BASE_DIR,"assets","general","frase_viajero.jpg"),
                               [24, y_bot+42, 175, y_bot+h_bot-12], radio=6)
    pensa = datos_db.get("pensamiento", {})
    f_txt = pensa.get("texto", "La vida es un viaje, no un destino")
    f_aut = pensa.get("autor", "An\u00f3nimo")
    frase_q = '"' + f_txt + '"'
    frase_lines = wrap_text(frase_q, f_frase_text, 310)
    total_h = len(frase_lines[:4]) * 28 + 24
    ty = y_bot + 42 + max((h_bot - 54 - total_h) // 2, 0)
    for line in frase_lines[:4]:
        draw.text((188, ty), line, fill=(15,23,42,255), font=f_frase_text, anchor="lt")
        ty += 28
    if f_aut and f_aut.lower() not in ("an\u00f3nimo", "anonimo"):
        draw.text((188, ty+6), "— " + f_aut, fill=(6,24,58,255), font=f_frase_author, anchor="lt")

    # Efemerides de Venezuela (derecha)
    x_efem = 12 + w_bot + 12
    grad_efem = crear_degradado_vertical(w_bot, h_bot, (255,253,247,255), (254,247,234,255))
    canvas.paste(grad_efem, (x_efem, y_bot))
    draw.rounded_rectangle([x_efem, y_bot, x_efem+w_bot, y_bot+h_bot], radius=8, outline=(203,213,225,255), width=1)
    dibujar_pestana_editorial(draw, x_efem, y_bot, 240, 32, "EFEM\u00c9RIDES DE VENEZUELA", f_tab_lg)
    pegar_imagen_redondeada_ed(canvas, os.path.join(BASE_DIR,"assets","general","efemeride_bolivar.jpg"),
                               [x_efem+12, y_bot+42, x_efem+155, y_bot+h_bot-12], radio=6)

    efem_raw = datos_db.get("efemeride_venezuela", "")
    if isinstance(efem_raw, dict):
        efem_raw = efem_raw.get("texto", "")
    match_ano = _re.search(r'\((\d{4})\)', efem_raw)
    ano_efem  = match_ano.group(1) if match_ano else ano_str
    explicacion = _re.sub(r'\(\d{4}\)', '', efem_raw)
    if "|" in explicacion:
        partes = explicacion.split("|", 1)
        explicacion = partes[0].strip() + ". " + partes[1].strip()
    explicacion = _re.sub(r'\s+', ' ', explicacion).strip()

    fecha_efem_hdr = dia_num + " de " + mes_nombre.lower() + " de " + ano_efem
    tx_efem_txt = x_efem + 168
    tw_efem = w_bot - 180
    draw.text((tx_efem_txt, y_bot+46), fecha_efem_hdr, fill=(15,23,42,255), font=f_efem_date, anchor="lt")
    efem_lines = wrap_text(explicacion, f_efem_body, tw_efem)
    ty = y_bot + 78
    for line in efem_lines[:4]:
        draw.text((tx_efem_txt, ty), line, fill=(51,65,85,255), font=f_efem_body, anchor="lt")
        ty += 22

    # ══════════════════════════════════════════════════════════════
    # E. PIE EDITORIAL (Y: 1038-1080)
    # ══════════════════════════════════════════════════════════════
    y_foot = 1038
    draw.rectangle([0, y_foot, W, H], fill=(6,24,58,255))
    draw.line([(0, y_foot), (W, y_foot)], fill=(225,185,75,255), width=2)
    foot_text = "Fuentes: Medios Nacionales | Generado Autom\u00e1ticamente \u00b7 \u00a9 Ing. LF"
    bbox_ft   = f_footer.getbbox(foot_text)
    ft_w      = bbox_ft[2] - bbox_ft[0]
    cx_ft     = W // 2
    draw.line([(80, y_foot+21), (cx_ft-(ft_w//2)-20, y_foot+21)], fill=(225,185,75,255), width=2)
    draw.line([(cx_ft+(ft_w//2)+20, y_foot+21), (W-80, y_foot+21)], fill=(225,185,75,255), width=2)
    draw.text((cx_ft, y_foot+21), foot_text, fill=(241,245,249,255), font=f_footer, anchor="mm")

    # Guardar resultado
    nombre          = "boletin_highlights_cuadrado.png"
    ruta_backup     = os.path.join(BASE_DIR, nombre)
    ruta_escritorio = os.path.join(ESCRITORIO, nombre)
    return guardar_imagen_con_reintento(canvas, ruta_escritorio, ruta_backup, "Portada Noticias del Dia (1080x1080)")
