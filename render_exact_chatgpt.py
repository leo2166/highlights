import os
import sys
import io
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paleta editorial exacta de la maqueta ChatGPT
NAVY_HEADER_TOP = (8,   32,  75,  255)
NAVY_HEADER_BOT = (4,   18,  46,  255)
NAVY_TAB        = (8,   28,  66,  255)
GOLD_ACCENT     = (225, 175, 45,  255)
GOLD_BORDER     = (225, 185, 75,  255)
WHITE           = (255, 255, 255, 255)
BG_PAGE         = (244, 246, 249, 255) # Gris perla de periódico moderno
BORDER_CARD     = (203, 213, 225, 255) # Slate 300 suave
BORDER_LIGHT    = (226, 232, 240, 255) # Slate 200
TEXT_TITLE      = (5,   11,  20,  255) # Negro editorial profundo (#050B14)
TEXT_BODY       = (30,  41,  59,  255) # Slate 800 (#1E293B)
TEXT_BLUE_NEWS  = (25,  105, 215, 255) # Azul real vibrante exacto de la referencia del usuario (#1969D7)
WARM_BG_START   = (255, 252, 240, 255) # Crema pergamino luminoso
WARM_BG_END     = (254, 243, 218, 255) # Ámbar dorado suave
WARM_BORDER     = (226, 203, 150, 255) # Borde dorado fino tarjetas inferiores

def crear_degradado_vertical(width, height, start_color, end_color):
    base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    for y in range(height):
        factor = y / max(height - 1, 1)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * factor)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * factor)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * factor)
        a = int(start_color[3] + (end_color[3] - start_color[3]) * factor) if len(start_color) > 3 else 255
        draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    return base

def wrap_text(text, font, max_width):
    if not text:
        return []
    cleaned_text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    words = [w for w in cleaned_text.split(' ') if w]
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def cargar_fuente_editorial(nombre_o_path, tamano):
    # 1. Buscar en fonts/ del proyecto
    local_path = os.path.join(BASE_DIR, "fonts", nombre_o_path)
    if os.path.exists(local_path):
        try:
            return ImageFont.truetype(local_path, int(tamano))
        except Exception:
            pass
    # 2. Buscar en C:\Windows\Fonts
    win_path = os.path.join(r"C:\Windows\Fonts", nombre_o_path)
    if os.path.exists(win_path):
        try:
            return ImageFont.truetype(win_path, int(tamano))
        except Exception:
            pass
    # 3. Ruta directa
    if os.path.exists(nombre_o_path):
        try:
            return ImageFont.truetype(nombre_o_path, int(tamano))
        except Exception:
            pass
    # 4. Fallback seguro
    try:
        return ImageFont.truetype("arialbd.ttf", int(tamano))
    except Exception:
        return ImageFont.load_default()

def pegar_imagen_redondeada(canvas, img_path, box, radio=6):
    x1, y1, x2, y2 = box
    w = max(int(x2 - x1), 10)
    h = max(int(y2 - y1), 10)
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
        print(f"Error procesando imagen {img_path}: {e}")

def dibujar_pestana_editorial(draw, x, y, texto, font, min_ancho=140, alto=30, corte=16):
    """Dibuja pestaña azul marino con corte diagonal y filete dorado sin cortar el texto."""
    bbox = font.getbbox(texto)
    tw = bbox[2] - bbox[0]
    ancho = max(min_ancho, tw + 24 + corte)
    puntos = [(x, y), (x + ancho, y), (x + ancho - corte, y + alto), (x, y + alto)]
    draw.polygon(puntos, fill=NAVY_TAB)
    draw.line([(x + ancho, y), (x + ancho - corte, y + alto)], fill=GOLD_ACCENT, width=3)
    draw.text((x + 12, y + alto // 2), texto, fill=WHITE, font=font, anchor="lm")

def renderizar_boletin_exacto_chatgpt(W, H, datos_bcv, noticias_5, pensamiento, efemeride, output_path):
    canvas = Image.new("RGBA", (W, H), BG_PAGE)
    draw = ImageDraw.Draw(canvas)

    es_1080 = (H <= 1100)
    es_1350 = (1100 < H <= 1400)
    es_1920 = (H > 1400)

    # --- 1. CONFIGURACIÓN GEOMÉTRICA Y TIPOGRÁFICA SEGÚN FORMATO ---
    if es_1080:
        f_header_title = cargar_fuente_editorial("georgiab.ttf", 52)
        f_header_sub   = cargar_fuente_editorial("georgiai.ttf", 22)
        f_date_day     = cargar_fuente_editorial("segoeui.ttf", 15)
        f_date_num     = cargar_fuente_editorial("segoeuib.ttf", 46)
        f_date_month   = cargar_fuente_editorial("segoeuib.ttf", 15)
        f_date_year    = cargar_fuente_editorial("segoeuib.ttf", 13)

        f_tab          = cargar_fuente_editorial("segoeuib.ttf", 14)
        f_tab_lg       = cargar_fuente_editorial("segoeuib.ttf", 15)
        f_rate_tag     = cargar_fuente_editorial("segoeuib.ttf", 15)
        f_rate_title   = cargar_fuente_editorial("segoeuib.ttf", 14)
        f_rate_val     = cargar_fuente_editorial("Oswald-Bold.ttf", 25)

        # Títulos: Georgia Bold (serif elegante de periódico)
        # Resúmenes: Segoe UI Bold Italic en azul corporativo (como la imagen de referencia)
        f_news_t1      = cargar_fuente_editorial("Oswald-Bold.ttf", 21)
        f_news_r1      = cargar_fuente_editorial("segoeuib.ttf", 13.5)
        f_news_t2      = cargar_fuente_editorial("Oswald-Bold.ttf", 17.5)
        f_news_r2      = cargar_fuente_editorial("segoeuib.ttf", 12.5)

        f_frase_text   = cargar_fuente_editorial("georgiaz.ttf", 22)
        f_frase_author = cargar_fuente_editorial("segoeuib.ttf", 14)
        f_efem_date    = cargar_fuente_editorial("georgiab.ttf", 19)
        f_efem_body    = cargar_fuente_editorial("segoeuib.ttf", 13.5)
        f_footer       = cargar_fuente_editorial("segoeuib.ttf", 13)

        h_header = 145
        y_cot, h_cot = 154, 78
        y_r1, h_r1, w_r1 = 242, 244, 522
        y_r2, h_r2, w_r2 = 496, 250, 344
        y_bot, h_bot, w_bot = 756, 268, 522
        y_footer, h_footer = 1034, 46

    elif es_1350:
        f_header_title = cargar_fuente_editorial("georgiab.ttf", 54)
        f_header_sub   = cargar_fuente_editorial("georgiai.ttf", 23)
        f_date_day     = cargar_fuente_editorial("segoeui.ttf", 16)
        f_date_num     = cargar_fuente_editorial("segoeuib.ttf", 48)
        f_date_month   = cargar_fuente_editorial("segoeuib.ttf", 16)
        f_date_year    = cargar_fuente_editorial("segoeuib.ttf", 14)

        f_tab          = cargar_fuente_editorial("segoeuib.ttf", 15)
        f_tab_lg       = cargar_fuente_editorial("segoeuib.ttf", 16)
        f_rate_tag     = cargar_fuente_editorial("segoeuib.ttf", 16)
        f_rate_title   = cargar_fuente_editorial("segoeuib.ttf", 15)
        f_rate_val     = cargar_fuente_editorial("Oswald-Bold.ttf", 26)

        f_news_t1      = cargar_fuente_editorial("Oswald-Bold.ttf", 23)
        f_news_r1      = cargar_fuente_editorial("segoeuib.ttf", 14)
        f_news_t2      = cargar_fuente_editorial("Oswald-Bold.ttf", 18.5)
        f_news_r2      = cargar_fuente_editorial("segoeuib.ttf", 13)

        f_frase_text   = cargar_fuente_editorial("georgiaz.ttf", 24)
        f_frase_author = cargar_fuente_editorial("segoeuib.ttf", 15)
        f_efem_date    = cargar_fuente_editorial("georgiab.ttf", 21)
        f_efem_body    = cargar_fuente_editorial("segoeuib.ttf", 14)
        f_footer       = cargar_fuente_editorial("segoeuib.ttf", 14)

        h_header = 155
        y_cot, h_cot = 168, 88
        y_r1, h_r1, w_r1 = 270, 300, 522
        y_r2, h_r2, w_r2 = 584, 315, 344
        y_bot, h_bot, w_bot = 914, 370, 522
        y_footer, h_footer = 1298, 52

    else: # H=1920 (Vertical Móvil Pantalla Completa)
        f_header_title = cargar_fuente_editorial("georgiab.ttf", 60)
        f_header_sub   = cargar_fuente_editorial("georgiai.ttf", 26)
        f_date_day     = cargar_fuente_editorial("segoeui.ttf", 18)
        f_date_num     = cargar_fuente_editorial("segoeuib.ttf", 56)
        f_date_month   = cargar_fuente_editorial("segoeuib.ttf", 18)
        f_date_year    = cargar_fuente_editorial("segoeuib.ttf", 15)

        f_tab          = cargar_fuente_editorial("segoeuib.ttf", 17)
        f_tab_lg       = cargar_fuente_editorial("segoeuib.ttf", 18)
        f_rate_tag     = cargar_fuente_editorial("segoeuib.ttf", 18)
        f_rate_title   = cargar_fuente_editorial("segoeuib.ttf", 17)
        f_rate_val     = cargar_fuente_editorial("Oswald-Bold.ttf", 30)

        f_news_t1      = cargar_fuente_editorial("Oswald-Bold.ttf", 27)
        f_news_r1      = cargar_fuente_editorial("segoeuib.ttf", 16.5)
        f_news_t2      = cargar_fuente_editorial("Oswald-Bold.ttf", 21)
        f_news_r2      = cargar_fuente_editorial("segoeuib.ttf", 15)

        f_frase_text   = cargar_fuente_editorial("georgiaz.ttf", 30)
        f_frase_author = cargar_fuente_editorial("segoeuib.ttf", 18)
        f_efem_date    = cargar_fuente_editorial("georgiab.ttf", 25)
        f_efem_body    = cargar_fuente_editorial("segoeuib.ttf", 17)
        f_footer       = cargar_fuente_editorial("segoeuib.ttf", 16)

        h_header = 180
        y_cot, h_cot = 196, 110
        y_r1, h_r1, w_r1 = 324, 420, 522
        y_r2, h_r2, w_r2 = 762, 450, 344
        y_bot, h_bot, w_bot = 1232, 600, 522
        y_footer, h_footer = 1850, 70

    # Fecha
    ahora = datetime.now()
    dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    dia_nombre = dias_es[ahora.weekday()]
    dia_num    = str(ahora.day)
    mes_nombre = meses_es[ahora.month - 1]
    ano_str    = str(ahora.year)

    # --- A. CABECERA EDITORIAL ---
    header_grad = crear_degradado_vertical(W, h_header, NAVY_HEADER_TOP, NAVY_HEADER_BOT)
    canvas.paste(header_grad, (0, 0))
    draw.line([(0, 1), (W, 1)], fill=GOLD_BORDER, width=2)
    draw.line([(0, h_header - 2), (W, h_header - 2)], fill=GOLD_BORDER, width=3)

    globe_path = os.path.join(BASE_DIR, "assets", "general", "globe.png")
    if os.path.exists(globe_path):
        try:
            g_w = 175 if es_1920 else (155 if es_1350 else 150)
            g_h = 150 if es_1920 else (130 if es_1350 else 125)
            gim = Image.open(globe_path).convert("RGBA")
            gim = gim.resize((g_w, g_h), Image.Resampling.LANCZOS)
            canvas.paste(gim, (14, (h_header - g_h) // 2), gim)
        except Exception:
            pass

    cx_hdr = W // 2 - 10
    cy_title = int(h_header * 0.35)
    cy_sub   = int(h_header * 0.73)
    draw.text((cx_hdr + 1, cy_title + 2), "NOTICIAS DEL DÍA", fill=(0, 10, 25, 200), font=f_header_title, anchor="mm")
    draw.text((cx_hdr, cy_title), "NOTICIAS DEL DÍA", fill=WHITE, font=f_header_title, anchor="mm")
    draw.text((cx_hdr, cy_sub), "La actualidad en una sola mirada", fill=(241, 245, 249, 255), font=f_header_sub, anchor="mm")

    cal_w = 145 if es_1920 else (142 if es_1350 else 140)
    cal_h = h_header - 24
    bx1 = W - cal_w - 18
    by1 = 12
    bx2 = W - 18
    by2 = by1 + cal_h
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=10, fill=WHITE, outline=BORDER_CARD, width=1)
    cx_b = (bx1 + bx2) // 2
    draw.text((cx_b, by1 + int(cal_h * 0.16)), dia_nombre, fill=(51, 65, 85, 255),  font=f_date_day,   anchor="mm")
    draw.text((cx_b, by1 + int(cal_h * 0.46)), dia_num,    fill=NAVY_TAB,           font=f_date_num,   anchor="mm")
    draw.text((cx_b, by1 + int(cal_h * 0.74)), mes_nombre, fill=(15, 23, 42, 255),  font=f_date_month, anchor="mm")
    draw.text((cx_b, by1 + int(cal_h * 0.90)), ano_str,    fill=(100, 116, 139, 255), font=f_date_year, anchor="mm")

    # --- B. FRANJA DE COTIZACIONES ---
    draw.rectangle([0, y_cot, W, y_cot + h_cot], fill=WHITE, outline=BORDER_LIGHT, width=1)
    w_tab_cot = 210 if es_1920 else 200
    corte_cot = 20
    pts_cot = [(10, y_cot + 6), (10 + w_tab_cot, y_cot + 6),
               (10 + w_tab_cot - corte_cot, y_cot + h_cot - 6), (10, y_cot + h_cot - 6)]
    draw.polygon(pts_cot, fill=NAVY_TAB)
    draw.line([(10 + w_tab_cot, y_cot + 6), (10 + w_tab_cot - corte_cot, y_cot + h_cot - 6)], fill=GOLD_ACCENT, width=4)
    draw.text((22, y_cot + int(h_cot * 0.32)), "COTIZACIONES", fill=WHITE, font=f_rate_tag, anchor="lm")
    draw.text((22, y_cot + int(h_cot * 0.68)), "DEL DÍA",      fill=WHITE, font=f_rate_tag, anchor="lm")

    usd_val = str(datos_bcv.get("usd", "888,89")) + " Bs"
    eur_val = str(datos_bcv.get("eur", "989,39")) + " Bs"
    bin_val = str(datos_bcv.get("binance", "1005,20")) + " Bs"

    ico_sz = 52 if es_1920 else (46 if es_1350 else 44)
    div_blocks = [
        {"x": 235 if not es_1920 else 245, "icon": os.path.join(BASE_DIR, "assets", "icons", "usd.png"),     "title": "DÓLAR BCV",   "val": usd_val},
        {"x": 510 if not es_1920 else 525, "icon": os.path.join(BASE_DIR, "assets", "icons", "eur.png"),     "title": "EURO BCV",    "val": eur_val},
        {"x": 780 if not es_1920 else 800, "icon": os.path.join(BASE_DIR, "assets", "icons", "binance.png"), "title": "BINANCE P2P", "val": bin_val},
    ]
    for blk in div_blocks:
        xs = blk["x"]
        if os.path.exists(blk["icon"]):
            try:
                ico = Image.open(blk["icon"]).convert("RGBA")
                ico = ico.resize((ico_sz, ico_sz), Image.Resampling.LANCZOS)
                canvas.paste(ico, (xs, y_cot + (h_cot - ico_sz) // 2), ico)
            except Exception:
                pass
        tx = xs + ico_sz + 10
        draw.text((tx, y_cot + int(h_cot * 0.33)), blk["title"], fill=(100, 116, 139, 255), font=f_rate_title, anchor="lm")
        draw.text((tx, y_cot + int(h_cot * 0.68)), blk["val"],   fill=NAVY_TAB,              font=f_rate_val,   anchor="lm")

    # --- C. SECCIÓN DE 5 NOTICIAS ---
    base_assets = os.path.join(BASE_DIR, "assets", "categories")
    def get_cat_img(cat):
        mapa = {
            "VENEZUELA": "venezuela.jpg",
            "ECONOMÍA": "economia.jpg",
            "ECONOMIA": "economia.jpg",
            "INTERNACIONALES": "internacionales.jpg",
            "MARACAIBO": "maracaibo.jpg",
            "SALUD": "salud.jpg",
        }
        fname = mapa.get(cat.upper(), "venezuela.jpg")
        return os.path.join(base_assets, fname)

    # Fila 1: 2 Noticias Principales
    for col_idx in range(2):
        n = noticias_5[col_idx]
        x0 = 12 + col_idx * (w_r1 + 12)
        draw.rounded_rectangle([x0, y_r1, x0 + w_r1, y_r1 + h_r1],
                               radius=8, fill=WHITE, outline=BORDER_CARD, width=1)
        cat_nom = n.get("categoria", "VENEZUELA")
        dibujar_pestana_editorial(draw, x0, y_r1, cat_nom, f_tab,
                                  min_ancho=150 if not es_1920 else 170,
                                  alto=32 if not es_1920 else 38)

        img_n = n.get("imagen_local") or get_cat_img(cat_nom)
        img_w = 205 if es_1920 else (200 if es_1350 else 190)
        box_img = [x0 + 10, y_r1 + (38 if not es_1920 else 44), x0 + 10 + img_w, y_r1 + h_r1 - 10]
        pegar_imagen_redondeada(canvas, img_n, box_img, radio=6)

        tx = x0 + 10 + img_w + 14
        tw = (x0 + w_r1 - 10) - tx
        titular = n.get("titular", "")
        t_lines = wrap_text(titular, f_news_t1, tw)

        lh_t1 = 30 if es_1920 else (25 if es_1350 else 23)
        ty = y_r1 + (42 if not es_1920 else 48)
        for line in t_lines[:3]:
            draw.text((tx, ty), line, fill=TEXT_TITLE, font=f_news_t1, anchor="lt")
            ty += lh_t1

        resumen = n.get("resumen", "")
        r_lines = wrap_text(resumen, f_news_r1, tw)
        lh_r1 = 22 if es_1920 else (18 if es_1350 else 17)
        ty += (8 if not es_1920 else 12)
        max_r1 = 7 if es_1920 else (6 if es_1350 else 5)
        for line in r_lines[:max_r1]:
            if ty + lh_r1 <= y_r1 + h_r1 - 8:
                draw.text((tx, ty), line, fill=TEXT_BLUE_NEWS, font=f_news_r1, anchor="lt")
                ty += lh_r1

    # Fila 2: 3 Noticias Medianas
    gap_r2 = 12
    for idx, noti in enumerate(noticias_5[2:5]):
        nx = 12 + idx * (w_r2 + gap_r2)
        draw.rounded_rectangle([nx, y_r2, nx + w_r2, y_r2 + h_r2],
                               radius=8, fill=WHITE, outline=BORDER_CARD, width=1)
        cat_nom = noti.get("categoria", "ACTUALIDAD")
        dibujar_pestana_editorial(draw, nx, y_r2, cat_nom, f_tab,
                                  min_ancho=135 if not es_1920 else 155,
                                  alto=30 if not es_1920 else 36)

        img_n2 = noti.get("imagen_local") or get_cat_img(cat_nom)
        img_w2 = 130 if es_1920 else (122 if es_1350 else 115)
        box_img2 = [nx + 8, y_r2 + (36 if not es_1920 else 42), nx + 8 + img_w2, y_r2 + h_r2 - 8]
        pegar_imagen_redondeada(canvas, img_n2, box_img2, radio=6)

        tx2 = nx + 8 + img_w2 + 10
        tw2 = (nx + w_r2 - 8) - tx2
        titular = noti.get("titular", "")
        t_lines2 = wrap_text(titular, f_news_t2, tw2)

        lh_t2 = 24 if es_1920 else (21 if es_1350 else 19)
        ty2 = y_r2 + (38 if not es_1920 else 46)
        for line in t_lines2[:3]:
            draw.text((tx2, ty2), line, fill=TEXT_TITLE, font=f_news_t2, anchor="lt")
            ty2 += lh_t2

        resumen = noti.get("resumen", "")
        r_lines2 = wrap_text(resumen, f_news_r2, tw2)
        lh_r2 = 20 if es_1920 else (17 if es_1350 else 15)
        ty2 += (6 if not es_1920 else 10)
        max_r2 = 8 if es_1920 else (7 if es_1350 else 6)
        for line in r_lines2[:max_r2]:
            if ty2 + lh_r2 <= y_r2 + h_r2 - 6:
                draw.text((tx2, ty2), line, fill=TEXT_BLUE_NEWS, font=f_news_r2, anchor="lt")
                ty2 += lh_r2

    # --- D. FRANJA INFERIOR CÁLIDA ---
    # LA FRASE UNIVERSAL
    grad_frase = crear_degradado_vertical(w_bot, h_bot, WARM_BG_START, WARM_BG_END)
    canvas.paste(grad_frase, (12, y_bot))
    draw.rounded_rectangle([12, y_bot, 12 + w_bot, y_bot + h_bot], radius=8, outline=WARM_BORDER, width=1)
    dibujar_pestana_editorial(draw, 12, y_bot, "LA FRASE UNIVERSAL", f_tab_lg,
                              min_ancho=215 if not es_1920 else 240,
                              alto=32 if not es_1920 else 38)

    img_frase = os.path.join(BASE_DIR, "assets", "general", "frase_viajero.jpg")
    img_wf = 165 if es_1920 else (155 if es_1350 else 145)
    pegar_imagen_redondeada(canvas, img_frase, [24, y_bot + 40, 24 + img_wf, y_bot + h_bot - 12], radio=6)

    tx_f = 24 + img_wf + 16
    tw_f = (12 + w_bot - 12) - tx_f
    p_txt = pensamiento.get("texto", "La vida es un viaje, no un destino")
    p_aut = pensamiento.get("autor", "Anónimo")
    frase_q = f'"{p_txt}"'
    f_lines = wrap_text(frase_q, f_frase_text, tw_f)

    lh_f = 34 if es_1920 else (29 if es_1350 else 27)
    total_hf = len(f_lines[:4]) * lh_f + 30
    ty_f = y_bot + 42 + max((h_bot - 50 - total_hf) // 2, 0)
    for line in f_lines[:4]:
        draw.text((tx_f, ty_f), line, fill=TEXT_TITLE, font=f_frase_text, anchor="lt")
        ty_f += lh_f
    if p_aut and p_aut.lower() not in ("anónimo", "anonimo"):
        draw.text((tx_f, ty_f + 8), f"— {p_aut}", fill=NAVY_TAB, font=f_frase_author, anchor="lt")

    # EFEMÉRIDES DE VENEZUELA
    x_efem = 12 + w_bot + 12
    grad_efem = crear_degradado_vertical(w_bot, h_bot, WARM_BG_START, WARM_BG_END)
    canvas.paste(grad_efem, (x_efem, y_bot))
    draw.rounded_rectangle([x_efem, y_bot, x_efem + w_bot, y_bot + h_bot], radius=8, outline=WARM_BORDER, width=1)
    dibujar_pestana_editorial(draw, x_efem, y_bot, "EFEMÉRIDES DE VENEZUELA", f_tab_lg,
                              min_ancho=235 if not es_1920 else 260,
                              alto=32 if not es_1920 else 38)

    efem_txt = efemeride.get("texto", "") if isinstance(efemeride, dict) else str(efemeride)
    # Búsqueda inteligente de año histórico (4 dígitos que no sea 2026 si hay otro)
    anos_encontrados = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', efem_txt)
    if anos_encontrados:
        ano_candidato = anos_encontrados[0]
        for a in anos_encontrados:
            if a != ano_str:
                ano_candidato = a
                break
        ano_efem = ano_candidato
    else:
        ano_efem = ano_str

    explicacion = re.sub(r'\(\d{4}\)', '', efem_txt)
    if "|" in explicacion:
        partes = explicacion.split("|", 1)
        explicacion = partes[0].strip() + ". " + partes[1].strip()
    explicacion = re.sub(r'\s+', ' ', explicacion).strip()

    box_efem = [x_efem + 12, y_bot + 40, x_efem + 12 + img_wf, y_bot + h_bot - 12]
    w_box_e = box_efem[2] - box_efem[0]
    h_box_e = box_efem[3] - box_efem[1]

    efem_lower = explicacion.lower()
    if any(k in efem_lower for k in ["bolívar", "bolivar", "libertador"]):
        img_efem_path = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
        pegar_imagen_redondeada(canvas, img_efem_path, box_efem, radio=6)
    else:
        escudo_path = os.path.join(BASE_DIR, "assets", "general", "escudo_venezuela.png")
        if os.path.exists(escudo_path):
            try:
                esc = Image.open(escudo_path).convert("RGBA")
                esc_ratio = esc.width / esc.height
                if esc_ratio > (w_box_e / h_box_e):
                    new_w = w_box_e - 10
                    new_h = int(new_w / esc_ratio)
                else:
                    new_h = h_box_e - 10
                    new_w = int(new_h * esc_ratio)
                esc = esc.resize((new_w, new_h), Image.Resampling.LANCZOS)
                px = box_efem[0] + (w_box_e - new_w) // 2
                py = box_efem[1] + (h_box_e - new_h) // 2
                canvas.paste(esc, (px, py), esc)
            except Exception:
                pass

    tx_e = x_efem + 12 + img_wf + 16
    tw_e = (x_efem + w_bot - 12) - tx_e
    fecha_tit = f"{dia_num} de {mes_nombre.lower()} de {ano_efem}"
    draw.text((tx_e, y_bot + (42 if not es_1920 else 52)), fecha_tit, fill=TEXT_TITLE, font=f_efem_date, anchor="lt")

    e_lines = wrap_text(explicacion, f_efem_body, tw_e)
    ty_e = y_bot + (72 if not es_1920 else 92)
    lh_e = 24 if es_1920 else (20 if es_1350 else 18)
    for line in e_lines[:6 if es_1920 else 4]:
        if ty_e + lh_e <= y_bot + h_bot - 8:
            draw.text((tx_e, ty_e), line, fill=TEXT_BLUE_NEWS, font=f_efem_body, anchor="lt")
            ty_e += lh_e

    # --- E. PIE DE PÁGINA INSTITUCIONAL ---
    footer_bg = Image.new("RGBA", (W, h_footer), NAVY_HEADER_BOT)
    canvas.paste(footer_bg, (0, y_footer))
    draw.line([(0, y_footer), (W, y_footer)], fill=GOLD_BORDER, width=2)

    w_dec = 420
    x_dec1 = (W - w_dec) // 2
    draw.line([(x_dec1, y_footer + int(h_footer * 0.8)), (x_dec1 + w_dec, y_footer + int(h_footer * 0.8))], fill=GOLD_ACCENT, width=1)

    draw.text((W // 2, y_footer + int(h_footer * 0.42)),
              "Fuentes: Medios Nacionales | Generado Automáticamente · © Ing. LF",
              fill=WHITE, font=f_footer, anchor="mm")

    canvas_rgb = canvas.convert("RGB")
    canvas_rgb.save(output_path, "PNG", quality=95)
    print(f"✅ [BOLETÍN GENERADO] Guardado con éxito en: {output_path} ({W}x{H} px)")
    return output_path
