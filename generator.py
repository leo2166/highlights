import re
from PIL import Image, ImageDraw, ImageFont
import os
import math
from datetime import datetime
from config import (
    CANVAS_WIDTH, CANVAS_HEIGHT, BG_GRADIENT_START, BG_GRADIENT_END,
    CARD_BG_COLOR, CARD_BORDER_COLOR, TEXT_PRIMARY_COLOR, TEXT_SECONDARY_COLOR,
    YELLOW_ACCENT_BG, YELLOW_ACCENT_TEXT, HEADER_GOLD_COLOR, CLIMA_CIUDAD,
    FONT_TITLE, FONT_BOLD, FONT_REGULAR, OUTPUT_IMAGE_PATH, BACKUP_IMAGE_PATH,
    FONT_OSWALD_BOLD, FONT_OSWALD_SEMIBOLD, FONT_OSWALD_REGULAR, FONT_ANTON, FONT_SCRIPT,
    ESCRITORIO, BASE_DIR
)

# ══════════════════════════════════════════════════════════════════════════════
# PALETA "WARM MODERN EDITORIAL" (Amigable, Luminosa, Confiable y Elegante)
# ══════════════════════════════════════════════════════════════════════════════
BG_CANVAS_TOP     = (248, 250, 252, 255)  # Slate 50 (blanco perla fresco)
BG_CANVAS_BOTTOM  = (234, 241, 248, 255)  # Slate 100 suave (azul-gris tenue)

# Header y Acentos Principales
NAVY_HEADER_START = (15,  32,  68,  255)  # Azul Zafiro noche
NAVY_HEADER_END   = (28,  58,  116, 255)  # Azul Zafiro institucional
NAVY_PRIMARY      = (22,  48,  98,  255)  # Azul corporativo elegante
GOLD_SUN          = (245, 158, 11,  255)  # Sol ámbar radiante
GOLD_ACCENT       = (217, 119, 6,   255)  # Ámbar dorado cálido
GOLD_SUBTLE       = (254, 243, 199, 255)  # Fondo ámbar muy suave

# Tarjetas y Superficies
CARD_BG           = (255, 255, 255, 255)  # Blanco puro
CARD_BORDER       = (226, 232, 240, 255)  # Borde tenue Slate 200
LINE_DIVIDER      = (241, 245, 249, 255)  # Divisor de renglón

# Tipografía
TEXT_DARK         = (15,  23,  42,  255)  # Slate 900 (casi negro para máxima legibilidad)
TEXT_BODY         = (30,  41,  59,  255)  # Slate 800 (cuerpo de texto suave)
TEXT_MUTED        = (100, 116, 139, 255)  # Slate 500 (fechas y metadatos)

# Divisas (Fondos y Textos Armónicos)
GREEN_USD_BG      = (236, 253, 245, 255)  # Menta suave
GREEN_USD_TXT     = (5,   150, 105, 255)  # Verde esmeralda dólar
BLUE_EUR_BG       = (239, 246, 255, 255)  # Azul cielo suave
BLUE_EUR_TXT      = (37,  99,  235, 255)  # Azul euro
AMBER_BIN_BG      = (254, 243, 199, 255)  # Ámbar suave
AMBER_BIN_TXT     = (217, 119, 6,   255)  # Ámbar Binance


def crear_degradado_vertical(width, height, start_color, end_color):
    """Genera una imagen con degradado vertical lineal suave."""
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
    """Divide un texto en múltiples líneas ajustadas a un ancho máximo en píxeles."""
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


def cargar_fuente(ruta_fuente, tamano, prefer_script=False):
    """Carga fuente TrueType con detección inteligente de fuentes de Windows de respaldo."""
    try:
        if ruta_fuente and os.path.exists(ruta_fuente):
            return ImageFont.truetype(ruta_fuente, tamano)
    except Exception:
        pass
    
    # Fuentes alternativas de Windows
    if prefer_script:
        alternativas = ["segoesc.ttf", "segoescb.ttf", "gabriola.ttf", "comic.ttf", "arial.ttf"]
    else:
        alternativas = ["segoeui.ttf", "segoeuib.ttf", "arial.ttf", "arialbd.ttf", "trebuc.ttf"]
        
    for alt in alternativas:
        alt_path = os.path.join("C:\\Windows\\Fonts", alt)
        if os.path.exists(alt_path):
            try:
                return ImageFont.truetype(alt_path, tamano)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_card(draw, rect, radius=24, fill=CARD_BG, border=CARD_BORDER, shadow=True):
    """Dibuja una tarjeta con esquinas redondeadas y sombra sutil difusa para efecto flotante."""
    x1, y1, x2, y2 = rect
    if shadow:
        # Sombra difusa de 2 capas transparentes
        draw.rounded_rectangle([x1,   y1+4, x2,   y2+4], radius=radius, fill=(15, 23, 42, 8))
        draw.rounded_rectangle([x1+1, y1+8, x2-1, y2+8], radius=radius, fill=(15, 23, 42, 10))
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=border, width=2)


def guardar_imagen_con_reintento(img, ruta_escritorio, ruta_backup, formato_nombre):
    """Guarda en backup local y en Escritorio con reintentos para mitigar bloqueos temporales de OneDrive."""
    import time
    try:
        img.save(ruta_backup, "PNG")
    except Exception as e:
        print(f"⚠️ Error al guardar respaldo de {formato_nombre}: {e}")

    for intento in range(3):
        try:
            img.save(ruta_escritorio, "PNG")
            print(f"🎉 ¡{formato_nombre} guardado exitosamente en el Escritorio!: {ruta_escritorio}")
            return ruta_escritorio
        except Exception:
            if intento < 2:
                time.sleep(0.3)
            else:
                print(f"📁 {formato_nombre} guardado como respaldo en el proyecto: {ruta_backup}")
                return ruta_backup
    return ruta_backup


def obtener_estilo_medio(medio):
    """
    Asigna colores pasteles amigables y distintivos a cada periódico para sus badges.
    Retorna: (color_fondo, color_texto, nombre_limpio)
    """
    m = (medio or "").upper()
    if "NACIONAL" in m:
        return (224, 242, 254, 255), (3,   105, 161, 255), "EL NACIONAL"       # Azul cielo suave
    elif "PATILLA" in m:
        return (255, 237, 213, 255), (194, 65,  12,  255), "LA PATILLA"        # Naranja cálido
    elif "PITAZO" in m:
        return (254, 226, 226, 255), (185, 28,  28,  255), "EL PITAZO"         # Rojo coral suave
    elif "COCUYO" in m:
        return (209, 250, 229, 255), (4,   120, 87,  255), "EFECTO COCUYO"     # Menta esmeralda
    elif "NOTICIA AL D" in m or "NOTICIA AL DIA" in m:
        return (224, 231, 255, 255), (67,  56,  202, 255), "NOTICIA AL DÍA"    # Índigo suave
    elif "BBC" in m:
        return (254, 226, 226, 255), (185, 28,  28,  255), "BBC MUNDO"         # Rojo sobrio
    elif "TAL CUAL" in m or "TALCUAL" in m:
        return (254, 243, 199, 255), (180, 83,  9,   255), "TAL CUAL"          # Ámbar suave
    elif "RUNRUN" in m:
        return (243, 232, 255, 255), (126, 34,  206, 255), "RUNRUNES"          # Violeta suave
    elif "DIARIO" in m:
        return (236, 253, 245, 255), (4,   120, 87,  255), "EL DIARIO"         # Verde suave
    elif "FINANZAS" in m:
        return (236, 253, 245, 255), (4,   120, 87,  255), "FINANZAS DIGITAL"   # Verde esmeralda suave
    elif "BANCA" in m or "NEGOCIOS" in m:
        return (224, 242, 254, 255), (3,   105, 161, 255), "BANCA Y NEGOCIOS"   # Azul corporativo suave
    elif "VERDAD" in m:
        return (255, 241, 242, 255), (190, 18,  60,  255), "LA VERDAD"         # Rosa cálido
    else:
        return (241, 245, 249, 255), (51,  65,  85,  255), m[:18]             # Slate neutro


# ══════════════════════════════════════════════════════════════════════════════
# 1. BOLETÍN VERTICAL 1080×1920 (Formato Pantalla / WhatsApp Status / Stories)
# ══════════════════════════════════════════════════════════════════════════════
def crear_boletin_grafico(datos_bcv, datos_noticia, datos_db):
    """
    Genera el Flyer vertical 1080×1920 px con el nuevo diseño 'Warm Modern Editorial'.
    Optimizado para 5 periódicos prioritarios con espaciado amplio y tipografía legible.
    """
    print("🎨 [BOLETÍN VERTICAL 1080x1920] Maquetando con diseño 'Warm Modern Editorial'...")

    W, H = 1080, 1920

    # Fuentes
    font_hero            = cargar_fuente(FONT_OSWALD_BOLD,   76)
    font_saludo_script   = cargar_fuente(os.path.join("C:\\Windows\\Fonts", "segoesc.ttf"), 38, prefer_script=True)
    font_date            = cargar_fuente(FONT_BOLD,          22)
    font_clima_badge     = cargar_fuente(FONT_BOLD,          22)
    font_badge           = cargar_fuente(FONT_BOLD,          22)
    font_subtitulo       = cargar_fuente(FONT_OSWALD_BOLD,   24)
    font_divisa_lbl      = cargar_fuente(FONT_BOLD,          20)
    font_divisa_val      = cargar_fuente(FONT_OSWALD_BOLD,   42)
    font_symbol          = cargar_fuente(FONT_BOLD,          32)
    font_quotes          = cargar_fuente(FONT_TITLE,         68)
    font_pensamiento     = cargar_fuente(FONT_REGULAR,       26)
    font_author          = cargar_fuente(FONT_BOLD,          22)
    font_efemeride       = cargar_fuente(FONT_REGULAR,       22)
    font_efemeride_bold  = cargar_fuente(FONT_BOLD,          22)
    font_section_title   = cargar_fuente(FONT_OSWALD_BOLD,   28)
    font_num_circle      = cargar_fuente(FONT_BOLD,          20)
    font_medio_tag       = cargar_fuente(FONT_BOLD,          18)
    font_titular         = cargar_fuente(FONT_BOLD,          28)
    font_footer          = cargar_fuente(FONT_BOLD,          20)

    # 1. Fondo del lienzo con degradado suave
    img = crear_degradado_vertical(W, H, BG_CANVAS_TOP, BG_CANVAS_BOTTOM)
    draw = ImageDraw.Draw(img)

    ahora = datetime.now()
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses_ano   = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha_formateada = f"{dias_semana[ahora.weekday()]}, {ahora.day} de {meses_ano[ahora.month - 1]} de {ahora.year}"
    hora_formateada  = ahora.strftime("%I:%M %p")

    # ═══════════════════════════════════════════════════════════════════════
    # A. CABECERA MODERNA (y=0 → 195)
    # ═══════════════════════════════════════════════════════════════════════
    header_h = 195
    header_grad = crear_degradado_vertical(W, header_h, NAVY_HEADER_START, NAVY_HEADER_END)
    img.paste(header_grad, (0, 0))

    # Textura tenue de micropuntos decorativos
    for px in range(W - 320, W - 25, 18):
        for py in range(90, header_h - 15, 18):
            draw.point((px, py), fill=(255, 255, 255, 35))

    # Doble línea decorativa inferior (dorada y translúcida)
    draw.line([(0, header_h - 3), (W, header_h - 3)], fill=GOLD_ACCENT, width=4)
    draw.line([(0, header_h - 7), (W, header_h - 7)], fill=(245, 158, 11, 100), width=2)

    # Título "HIGHLIGHTS"
    draw.text((44, 46), "HIGHLIGHTS", fill=(255, 255, 255, 255), font=font_hero, anchor="lt")
    draw.text((46, 126), "RESUMEN INFORMATIVO DIARIO", fill=(203, 213, 225, 255), font=font_badge, anchor="lt")

    # Sol radiante y saludo "¡Buenos Días!"
    sun_x, sun_y, sun_r = W - 75, 95, 24
    draw.ellipse([sun_x-sun_r, sun_y-sun_r, sun_x+sun_r, sun_y+sun_r], fill=GOLD_SUN)
    # Rayos del sol
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = sun_x + int((sun_r + 4) * math.cos(rad))
        y1 = sun_y + int((sun_r + 4) * math.sin(rad))
        x2 = sun_x + int((sun_r + 14) * math.cos(rad))
        y2 = sun_y + int((sun_r + 14) * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=GOLD_SUN, width=3)

    draw.text((sun_x - sun_r - 24, sun_y), "¡Buenos Días!", fill=(255, 255, 255, 255),
              font=font_saludo_script, anchor="rm")

    # ═══════════════════════════════════════════════════════════════════════
    # FILA DE FECHA Y ESTADO DEL TIEMPO (y=215 → 265)
    # ═══════════════════════════════════════════════════════════════════════
    MX = 40
    y_sub = 215
    # Icono de calendario estilizado
    cal_x, cal_y = MX + 4, y_sub + 12
    draw.rounded_rectangle([cal_x, cal_y - 12, cal_x + 26, cal_y + 14], radius=5, outline=NAVY_PRIMARY, width=2)
    draw.line([(cal_x, cal_y - 4), (cal_x + 26, cal_y - 4)], fill=NAVY_PRIMARY, width=2)
    draw.text((cal_x + 36, y_sub + 12), fecha_formateada, fill=TEXT_DARK, font=font_date, anchor="lm")

    # Píldora de Clima Maracaibo a la derecha
    clima = datos_db.get("clima", [])
    clima_str = f"🌤️ {CLIMA_CIUDAD} · {hora_formateada}"
    if clima:
        c0 = clima[0]
        desc = c0.get("descripcion", "Despejado")
        temp = c0.get("temp_max", "--")
        clima_str = f"🌤️ {temp}°C {desc} · {CLIMA_CIUDAD}"
        
    c_bbox = font_clima_badge.getbbox(clima_str)
    c_w = c_bbox[2] - c_bbox[0]
    badge_rx2 = W - MX
    badge_rx1 = badge_rx2 - c_w - 30
    draw.rounded_rectangle([badge_rx1, y_sub - 3, badge_rx2, y_sub + 27], radius=15, fill=(241, 245, 249, 255), outline=CARD_BORDER, width=1)
    draw.text((badge_rx1 + 15, y_sub + 12), clima_str, fill=NAVY_PRIMARY, font=font_clima_badge, anchor="lm")

    # ═══════════════════════════════════════════════════════════════════════
    # B. PARIDAD CAMBIARIA (y=268 → 490)
    # ═══════════════════════════════════════════════════════════════════════
    y_pari = 268
    pari_h = 222
    draw_card(draw, [MX, y_pari, W - MX, y_pari + pari_h], radius=24)

    # Cápsula de título central
    badge_w, badge_h_px = 480, 48
    bx1 = (W - badge_w) // 2
    by1 = y_pari + 8
    draw.rounded_rectangle([bx1, by1, bx1 + badge_w, by1 + badge_h_px], radius=24, fill=NAVY_PRIMARY)
    draw.text((W // 2, by1 + 24), "PARIDAD CAMBIARIA (Bs.)", fill=(255, 255, 255, 255), font=font_badge, anchor="mm")

    # 3 Columnas para divisas
    col_w = (W - 2 * MX) // 3
    divisas = [
        {"lbl": "Dólar BCV",   "sym": "$", "val": datos_bcv.get("usd", "N/D"),     "bg": GREEN_USD_BG, "txt": GREEN_USD_TXT},
        {"lbl": "Euro BCV",    "sym": "€", "val": datos_bcv.get("eur", "N/D"),     "bg": BLUE_EUR_BG,  "txt": BLUE_EUR_TXT},
        {"lbl": "Binance P2P", "sym": "₮", "val": datos_bcv.get("binance", "N/D"), "bg": AMBER_BIN_BG, "txt": AMBER_BIN_TXT},
    ]

    y_content_pari = y_pari + 76
    for i, item in enumerate(divisas):
        col_x = MX + i * col_w
        if i > 0:
            draw.line([(col_x, y_pari + 70), (col_x, y_pari + pari_h - 26)], fill=CARD_BORDER, width=2)
        
        # Círculo del símbolo
        cc_x = col_x + 56
        cc_y = y_content_pari + 36
        cc_r = 34
        draw.ellipse([cc_x - cc_r, cc_y - cc_r, cc_x + cc_r, cc_y + cc_r], fill=item["bg"])
        draw.text((cc_x, cc_y), item["sym"], fill=item["txt"], font=font_symbol, anchor="mm")

        # Textos: Etiqueta y Valor grande
        tx = cc_x + 46
        draw.text((tx, y_content_pari + 10), item["lbl"], fill=TEXT_MUTED, font=font_divisa_lbl, anchor="lt")
        draw.text((tx, y_content_pari + 36), item["val"], fill=TEXT_DARK,  font=font_divisa_val, anchor="lt")

    # Fecha valor oficial
    fecha_bcv = datos_bcv.get("fecha", ahora.strftime("%d/%m/%Y"))
    draw.text((W // 2, y_pari + pari_h - 14), f"✓ Fecha Valor Oficial BCV: {fecha_bcv}",
              fill=GOLD_ACCENT, font=font_divisa_lbl, anchor="mm")

    # ═══════════════════════════════════════════════════════════════════════
    # C. PENSAMIENTO UNIVERSAL & EFEMÉRIDES VENEZUELA (y=508 → 868)
    # ═══════════════════════════════════════════════════════════════════════
    y_bloque2 = 508
    bloque2_h = 360
    gap = 20
    w_card_half = (W - 2 * MX - gap) // 2

    c_p_left  = MX
    c_p_right = c_p_left + w_card_half
    c_e_left  = c_p_right + gap
    c_e_right = W - MX

    # ── Tarjeta Pensamiento Universal ──
    draw_card(draw, [c_p_left, y_bloque2, c_p_right, y_bloque2 + bloque2_h], radius=22)
    draw.rounded_rectangle([c_p_left, y_bloque2, c_p_right, y_bloque2 + 52], radius=22, fill=NAVY_PRIMARY)
    draw.rectangle([c_p_left, y_bloque2 + 32, c_p_right, y_bloque2 + 52], fill=NAVY_PRIMARY)
    draw.text((c_p_left + 24, y_bloque2 + 26), "💡 PENSAMIENTO DEL DÍA", fill=(255, 255, 255, 255),
              font=font_subtitulo, anchor="lm")

    pensamiento = datos_db.get("pensamiento", {"texto": "El éxito es la suma de pequeños esfuerzos repetidos día tras día.", "autor": "Robert Collier"})
    texto_p = pensamiento.get("texto", "")
    autor_p = pensamiento.get("autor", "Anónimo")

    # Gran comilla de apertura estilizada
    draw.text((c_p_left + 20, y_bloque2 + 64), "“", fill=NAVY_PRIMARY, font=font_quotes, anchor="lt")
    
    wrapped_p = wrap_text(texto_p, font_pensamiento, w_card_half - 72)
    py = y_bloque2 + 78
    for line in wrapped_p[:7]:
        draw.text((c_p_left + 58, py), line, fill=TEXT_BODY, font=font_pensamiento)
        py += 36
    draw.text((c_p_right - 24, y_bloque2 + bloque2_h - 22), f"— {autor_p}", fill=NAVY_PRIMARY, font=font_author, anchor="rm")

    # ── Tarjeta Efemérides Venezuela ──
    draw_card(draw, [c_e_left, y_bloque2, c_e_right, y_bloque2 + bloque2_h], radius=22)
    draw.rounded_rectangle([c_e_left, y_bloque2, c_e_right, y_bloque2 + 52], radius=22, fill=GOLD_ACCENT)
    draw.rectangle([c_e_left, y_bloque2 + 32, c_e_right, y_bloque2 + 52], fill=GOLD_ACCENT)
    draw.text((c_e_left + 24, y_bloque2 + 26), "🇻🇪 EFEMÉRIDES VENEZUELA", fill=(255, 255, 255, 255),
              font=font_subtitulo, anchor="lm")

    efemeride_v = datos_db.get("efemeride_venezuela", "Hoy conmemoramos importantes acontecimientos en la historia de Venezuela.")
    wrapped_e = wrap_text(efemeride_v, font_efemeride, w_card_half - 44)
    ey = y_bloque2 + 74
    for idx, line in enumerate(wrapped_e[:8]):
        f_use = font_efemeride_bold if (idx == 0 and any(c in line for c in [":", "(", "."])) else font_efemeride
        draw.text((c_e_left + 22, ey), line, fill=TEXT_BODY, font=f_use)
        ey += 33

    # ═══════════════════════════════════════════════════════════════════════
    # D. TITULARES DE HOY (5 PERIODICOS PRIORITARIOS) (y=888 → 1828)
    # ═══════════════════════════════════════════════════════════════════════
    y_tit = 888
    tit_h = 940
    draw_card(draw, [MX, y_tit, W - MX, y_tit + tit_h], radius=24)

    # Cabecera de Titulares
    header_tit_h = 60
    draw.rounded_rectangle([MX, y_tit, W - MX, y_tit + header_tit_h], radius=24, fill=NAVY_PRIMARY)
    draw.rectangle([MX, y_tit + 38, W - MX, y_tit + header_tit_h], fill=NAVY_PRIMARY)
    draw.text((MX + 28, y_tit + 30), "📰 TITULARES DESTACADOS", fill=(255, 255, 255, 255), font=font_section_title, anchor="lm")
    draw.text((W - MX - 28, y_tit + 30), "5 MEDIOS PRINCIPALES", fill=(203, 213, 225, 255), font=font_medio_tag, anchor="rm")

    titulares = datos_db.get("titulares_medios", [])
    num_titulares = min(len(titulares), 5) if titulares else 0
    max_tw = (W - 2 * MX) - 130

    if not titulares:
        draw.text((W // 2, y_tit + 200), "No hay titulares disponibles en este momento.", fill=TEXT_MUTED, font=font_pensamiento, anchor="mm")
    else:
        espacio_util = tit_h - header_tit_h - 20
        paso = espacio_util // num_titulares

        for i, item in enumerate(titulares[:num_titulares]):
            item_y = y_tit + header_tit_h + 14 + (i * paso)

            # Círculo numerado moderno
            num_cx, num_cy, num_r = MX + 44, item_y + 38, 22
            draw.ellipse([num_cx - num_r, num_cy - num_r, num_cx + num_r, num_cy + num_r], fill=NAVY_PRIMARY)
            draw.text((num_cx, num_cy), str(i + 1), fill=(255, 255, 255, 255), font=font_num_circle, anchor="mm")

            # Badge pill del medio con su color propio
            medio_raw = item.get("medio", "")
            bg_badge, txt_badge, nombre_limpio = obtener_estilo_medio(medio_raw)
            badge_x = MX + 82
            badge_y = item_y + 4
            
            # Medir ancho del badge
            mb_box = font_medio_tag.getbbox(nombre_limpio)
            bw = (mb_box[2] - mb_box[0]) + 20
            draw.rounded_rectangle([badge_x, badge_y, badge_x + bw, badge_y + 28], radius=14, fill=bg_badge)
            draw.text((badge_x + 10, badge_y + 14), nombre_limpio, fill=txt_badge, font=font_medio_tag, anchor="lm")

            # Titular con texto amplio en hasta 3 líneas
            titular_raw = item.get("titular", "").strip()
            lines = wrap_text(titular_raw, font_titular, max_tw)
            ty = item_y + 42
            for l_idx, line in enumerate(lines[:3]):
                if l_idx == 2 and len(lines) > 3:
                    if len(line) > 5:
                        line = line[:-3] + "..."
                draw.text((badge_x, ty), line, fill=TEXT_DARK, font=font_titular, anchor="lt")
                ty += 36

            # Línea divisoria tenue entre titulares
            if i < num_titulares - 1:
                div_y = item_y + paso - 4
                draw.line([(MX + 24, div_y), (W - MX - 24, div_y)], fill=LINE_DIVIDER, width=2)

    # ═══════════════════════════════════════════════════════════════════════
    # E. FOOTER CÁPSULA FLOTANTE (y=1844 → 1900)
    # ═══════════════════════════════════════════════════════════════════════
    footer_w = 680
    footer_h = 52
    fx1 = (W - footer_w) // 2
    fy1 = H - 74
    fx2 = fx1 + footer_w
    fy2 = fy1 + footer_h
    draw.rounded_rectangle([fx1, fy1, fx2, fy2], radius=26, fill=NAVY_HEADER_START, outline=GOLD_ACCENT, width=2)
    draw.text((W // 2, fy1 + 26), "Highlights Diario · Generado Automáticamente · © Ing. LF",
              fill=(241, 245, 249, 240), font=font_footer, anchor="mm")

    # Guardar imagen vertical
    return guardar_imagen_con_reintento(img, OUTPUT_IMAGE_PATH, BACKUP_IMAGE_PATH, "Flyer Vertical")




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
    f_news_r1      = carga("segoeuiz.ttf",  13)
    f_news_t2      = carga("georgiab.ttf",  15)
    f_news_r2      = carga("segoeuiz.ttf",  12)
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
            draw.text((x0+218, ty), line, fill=(0,0,0,255), font=f_news_r1, anchor="lt")
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
            draw.text((tx_pos, ty), line, fill=(0,0,0,255), font=f_news_r2, anchor="lt")
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

    # Selección de imagen de efeméride: si menciona a Bolívar retrato, si no el Escudo Nacional
    efem_lower = explicacion.lower()
    box_efem = [x_efem + 12, y_bot + 42, x_efem + 155, y_bot + h_bot - 12]
    w_box_e = box_efem[2] - box_efem[0]
    h_box_e = box_efem[3] - box_efem[1]

    if any(k in efem_lower for k in ["bolívar", "bolivar", "libertador"]):
        img_efem_path = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
        pegar_imagen_redondeada_ed(canvas, img_efem_path, box_efem, radio=6)
    else:
        # Símbolo Patrio: Escudo Nacional de Venezuela (escalado proporcionalmente con transparencia)
        escudo_path = os.path.join(BASE_DIR, "assets", "general", "escudo_venezuela.png")
        if os.path.exists(escudo_path):
            try:
                im_esc = Image.open(escudo_path).convert("RGBA")
                im_esc.thumbnail((w_box_e - 6, h_box_e - 6), Image.Resampling.LANCZOS)
                px_esc = box_efem[0] + (w_box_e - im_esc.width) // 2
                py_esc = box_efem[1] + (h_box_e - im_esc.height) // 2
                canvas.paste(im_esc, (px_esc, py_esc), im_esc)
            except Exception as e_esc:
                print("Error pegando Escudo:", e_esc)
                img_efem_path = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
                pegar_imagen_redondeada_ed(canvas, img_efem_path, box_efem, radio=6)
        else:
            img_efem_path = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
            pegar_imagen_redondeada_ed(canvas, img_efem_path, box_efem, radio=6)

    fecha_efem_hdr = dia_num + " de " + mes_nombre.lower() + " de " + ano_efem
    tx_efem_txt = x_efem + 168
    tw_efem = w_bot - 180
    draw.text((tx_efem_txt, y_bot+46), fecha_efem_hdr, fill=(15,23,42,255), font=f_efem_date, anchor="lt")
    efem_lines = wrap_text(explicacion, f_efem_body, tw_efem)
    ty = y_bot + 78
    for line in efem_lines[:4]:
        draw.text((tx_efem_txt, ty), line, fill=(15,23,42,255), font=f_efem_body, anchor="lt")
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


# ══════════════════════════════════════════════════════════════════════════════
# 3. BOLETÍN 1200×1500 (Proporción 4:5 Instagram / LinkedIn)
# ══════════════════════════════════════════════════════════════════════════════
def crear_boletin_1200x1500(datos_bcv, datos_noticia, datos_db):
    """
    Boletín vertical 1200×1500 px (4:5) para Instagram Feed y LinkedIn.
    """
    print("🎨 [BOLETÍN 1200x1500] Maquetando versión 4:5...")

    W, H = 1200, 1500

    font_hero            = cargar_fuente(FONT_OSWALD_BOLD,   74)
    font_saludo_script   = cargar_fuente(os.path.join("C:\\Windows\\Fonts", "segoesc.ttf"), 36, prefer_script=True)
    font_date            = cargar_fuente(FONT_BOLD,          22)
    font_badge           = cargar_fuente(FONT_BOLD,          22)
    font_subtitulo       = cargar_fuente(FONT_OSWALD_BOLD,   24)
    font_divisa_lbl      = cargar_fuente(FONT_BOLD,          20)
    font_divisa_val      = cargar_fuente(FONT_OSWALD_BOLD,   40)
    font_symbol          = cargar_fuente(FONT_BOLD,          30)
    font_quotes          = cargar_fuente(FONT_TITLE,         62)
    font_pensamiento     = cargar_fuente(FONT_REGULAR,       24)
    font_author          = cargar_fuente(FONT_BOLD,          20)
    font_efemeride       = cargar_fuente(FONT_REGULAR,       21)
    font_efemeride_bold  = cargar_fuente(FONT_BOLD,          21)
    font_section_title   = cargar_fuente(FONT_OSWALD_BOLD,   26)
    font_num_circle      = cargar_fuente(FONT_BOLD,          19)
    font_medio_tag       = cargar_fuente(FONT_BOLD,          17)
    font_titular         = cargar_fuente(FONT_BOLD,          25)
    font_footer          = cargar_fuente(FONT_BOLD,          19)

    img = crear_degradado_vertical(W, H, BG_CANVAS_TOP, BG_CANVAS_BOTTOM)
    draw = ImageDraw.Draw(img)

    ahora = datetime.now()
    dias_s = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    meses  = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
              "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    fecha_str = f"{dias_s[ahora.weekday()]}, {ahora.day} de {meses[ahora.month-1]} de {ahora.year}"
    hora_str  = ahora.strftime("%I:%M %p")

    # Header
    HH = 165
    head_grad = crear_degradado_vertical(W, HH, NAVY_HEADER_START, NAVY_HEADER_END)
    img.paste(head_grad, (0, 0))
    draw.line([(0, HH - 3), (W, HH - 3)], fill=GOLD_ACCENT, width=4)

    draw.text((44, 34), "HIGHLIGHTS", fill=(255, 255, 255, 255), font=font_hero, anchor="lt")
    draw.text((46, 110), f"{fecha_str} · {hora_str}", fill=(203, 213, 225, 255), font=font_date, anchor="lt")

    # Sol y Saludo
    sx, sy, sr = W - 72, 82, 22
    draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=GOLD_SUN)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = sx + int((sr + 3) * math.cos(rad))
        y1 = sy + int((sr + 3) * math.sin(rad))
        x2 = sx + int((sr + 12) * math.cos(rad))
        y2 = sy + int((sr + 12) * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=GOLD_SUN, width=2)
    draw.text((sx - sr - 20, sy), "¡Buenos Días!", fill=(255, 255, 255, 255), font=font_saludo_script, anchor="rm")

    # Paridad
    MX = 44
    y_par = 180
    par_h = 186
    draw_card(draw, [MX, y_par, W - MX, y_par + par_h], radius=22)

    bw, bh = 480, 42
    bx1 = (W - bw) // 2
    by1 = y_par + 8
    draw.rounded_rectangle([bx1, by1, bx1 + bw, by1 + bh], radius=21, fill=NAVY_PRIMARY)
    draw.text((W // 2, by1 + 21), "PARIDAD CAMBIARIA (Bs.)", fill=(255, 255, 255, 255), font=font_badge, anchor="mm")

    col_w = (W - 2 * MX) // 3
    divisas = [
        {"lbl": "Dólar BCV",   "sym": "$", "val": datos_bcv.get("usd", "N/D"),     "bg": GREEN_USD_BG, "txt": GREEN_USD_TXT},
        {"lbl": "Euro BCV",    "sym": "€", "val": datos_bcv.get("eur", "N/D"),     "bg": BLUE_EUR_BG,  "txt": BLUE_EUR_TXT},
        {"lbl": "Binance P2P", "sym": "₮", "val": datos_bcv.get("binance", "N/D"), "bg": AMBER_BIN_BG, "txt": AMBER_BIN_TXT},
    ]

    yc = y_par + 66
    for i, div in enumerate(divisas):
        cx = MX + i * col_w
        if i > 0:
            draw.line([(cx, y_par + 62), (cx, y_par + par_h - 22)], fill=CARD_BORDER, width=2)
        cc_x, cc_y, cr = cx + 52, yc + 32, 28
        draw.ellipse([cc_x-cr, cc_y-cr, cc_x+cr, cc_y+cr], fill=div["bg"])
        draw.text((cc_x, cc_y), div["sym"], fill=div["txt"], font=font_symbol, anchor="mm")
        tx = cc_x + 40
        draw.text((tx, yc + 6),  div["lbl"], fill=TEXT_MUTED, font=font_divisa_lbl, anchor="lt")
        draw.text((tx, yc + 30), div["val"], fill=TEXT_DARK,  font=font_divisa_val, anchor="lt")

    # Pensamiento & Efemérides
    y_c2 = 382
    c2_h = 310
    gap = 20
    hw = (W - 2 * MX - gap) // 2

    # Pensamiento
    px1, px2 = MX, MX + hw
    draw_card(draw, [px1, y_c2, px2, y_c2 + c2_h], radius=20)
    draw.rounded_rectangle([px1, y_c2, px2, y_c2 + 46], radius=20, fill=NAVY_PRIMARY)
    draw.rectangle([px1, y_c2 + 28, px2, y_c2 + 46], fill=NAVY_PRIMARY)
    draw.text((px1 + 22, y_c2 + 23), "💡 PENSAMIENTO DEL DÍA", fill=(255, 255, 255, 255), font=font_subtitulo, anchor="lm")

    pensamiento = datos_db.get("pensamiento", {"texto": "El secreto del cambio es enfocar toda tu energía no en luchar contra lo viejo, sino en construir lo nuevo.", "autor": "Sócrates"})
    draw.text((px1 + 18, y_c2 + 58), "“", fill=NAVY_PRIMARY, font=font_quotes, anchor="lt")
    wrapped_p = wrap_text(pensamiento.get("texto", ""), font_pensamiento, hw - 64)
    py_txt = y_c2 + 68
    for line in wrapped_p[:6]:
        draw.text((px1 + 52, py_txt), line, fill=TEXT_BODY, font=font_pensamiento)
        py_txt += 32
    draw.text((px2 - 20, y_c2 + c2_h - 18), f"— {pensamiento.get('autor', 'Anónimo')}", fill=NAVY_PRIMARY, font=font_author, anchor="rm")

    # Efemérides
    ex1, ex2 = MX + hw + gap, W - MX
    draw_card(draw, [ex1, y_c2, ex2, y_c2 + c2_h], radius=20)
    draw.rounded_rectangle([ex1, y_c2, ex2, y_c2 + 46], radius=20, fill=GOLD_ACCENT)
    draw.rectangle([ex1, y_c2 + 28, ex2, y_c2 + 46], fill=GOLD_ACCENT)
    draw.text((ex1 + 22, y_c2 + 23), "🇻🇪 EFEMÉRIDES VENEZUELA", fill=(255, 255, 255, 255), font=font_subtitulo, anchor="lm")

    efem_v = datos_db.get("efemeride_venezuela", "Hoy conmemoramos importantes acontecimientos en Venezuela.")
    wrapped_v = wrap_text(efem_v, font_efemeride, hw - 40)
    vy = y_c2 + 66
    for idx, line in enumerate(wrapped_v[:7]):
        f_u = font_efemeride_bold if (idx == 0 and any(c in line for c in [":", "(", "."])) else font_efemeride
        draw.text((ex1 + 20, vy), line, fill=TEXT_BODY, font=f_u)
        vy += 30

    # Titulares (5 Medios)
    y_tit = 708
    tit_h = 718
    draw_card(draw, [MX, y_tit, W - MX, y_tit + tit_h], radius=22)
    draw.rounded_rectangle([MX, y_tit, W - MX, y_tit + 52], radius=22, fill=NAVY_PRIMARY)
    draw.rectangle([MX, y_tit + 32, W - MX, y_tit + 52], fill=NAVY_PRIMARY)
    draw.text((MX + 28, y_tit + 26), "📰 TITULARES DESTACADOS (5 MEDIOS)", fill=(255, 255, 255, 255), font=font_section_title, anchor="lm")

    titulares = datos_db.get("titulares_medios", [])
    n_tit = min(len(titulares), 5)
    max_tw = (W - 2 * MX) - 110

    if not titulares:
        draw.text((W // 2, y_tit + 180), "No hay titulares disponibles.", fill=TEXT_MUTED, font=font_pensamiento, anchor="mm")
    else:
        espacio = tit_h - 60
        paso = espacio // n_tit

        for i, item in enumerate(titulares[:n_tit]):
            iy = y_tit + 58 + i * paso

            ncx, ncy, nr = MX + 36, iy + 34, 19
            draw.ellipse([ncx-nr, ncy-nr, ncx+nr, ncy+nr], fill=NAVY_PRIMARY)
            draw.text((ncx, ncy), str(i + 1), fill=(255, 255, 255, 255), font=font_num_circle, anchor="mm")

            medio_raw = item.get("medio", "")
            bg_badge, txt_badge, nombre_limpio = obtener_estilo_medio(medio_raw)
            bx = MX + 70
            
            mb_box = font_medio_tag.getbbox(nombre_limpio)
            bw = (mb_box[2] - mb_box[0]) + 18
            draw.rounded_rectangle([bx, iy + 4, bx + bw, iy + 26], radius=12, fill=bg_badge)
            draw.text((bx + 9, iy + 15), nombre_limpio, fill=txt_badge, font=font_medio_tag, anchor="lm")

            titular_raw = item.get("titular", "").strip()
            lines = wrap_text(titular_raw, font_titular, max_tw)
            ty = iy + 36
            for l_idx, line in enumerate(lines[:3]):
                if l_idx == 2 and len(lines) > 3:
                    if len(line) > 5:
                        line = line[:-3] + "..."
                draw.text((bx, ty), line, fill=TEXT_DARK, font=font_titular, anchor="lt")
                ty += 32

            if i < n_tit - 1:
                dy = iy + paso - 3
                draw.line([(MX + 20, dy), (W - MX - 20, dy)], fill=LINE_DIVIDER, width=2)

    # Footer
    fw = 620
    fh = 48
    fx1 = (W - fw) // 2
    fy1 = H - 62
    draw.rounded_rectangle([fx1, fy1, fx1 + fw, fy1 + fh], radius=24, fill=NAVY_HEADER_START, outline=GOLD_ACCENT, width=2)
    draw.text((W // 2, fy1 + 24), "Highlights Diario · Generado Automáticamente · © Ing. LF",
              fill=(241, 245, 249, 230), font=font_footer, anchor="mm")

    nombre = "boletin_highlights_1200x1500.png"
    ruta_backup = os.path.join(BASE_DIR, nombre)
    ruta_escritorio = os.path.join(ESCRITORIO, nombre)
    return guardar_imagen_con_reintento(img, ruta_escritorio, ruta_backup, "Boletín 1200×1500")


if __name__ == "__main__":
    test_bcv = {"usd": "520,91", "eur": "604,16", "binance": "580,20", "fecha": "Domingo, 25 Octubre 2026"}
    test_noticia = {"titulo": "Comercio binacional y nuevos acuerdos impulsan dinamismo en la frontera venezolana.", "link": "https://www.bancaynegocios.com/"}
    test_db = {
        "pensamiento": {"texto": "El secreto del cambio es enfocar toda tu energía no en luchar contra lo viejo, sino en construir lo nuevo.", "autor": "Sócrates"},
        "efemeride_universal": "Día Mundial de las Personas de Talla Baja y diversas conmemoraciones de la ciencia y la cultura.",
        "efemeride_venezuela": "1888: Nace en Maracaibo el reconocido escritor y jurista Rafael Belloso Chacín, ilustre zuliano.",
        "clima": [{"temp_max": "33.2", "temp_min": "26.1", "descripcion": "Parcialmente Despejado", "emoji": "🌤️"}],
        "titulares_medios": [
            {"medio": "El Nacional", "titular": "Sector manufacturero proyecta crecimiento moderado para el cierre del último trimestre."},
            {"medio": "La Patilla", "titular": "Reportan normalización paulatina del suministro de combustible en el occidente del país."},
            {"medio": "El Pitazo", "titular": "Comunidades del Zulia avanzan en proyectos de autogestión de agua potable y alumbrado."},
            {"medio": "Efecto Cocuyo", "titular": "Expertos económicos debaten propuestas de simplificación tributaria en Caracas."},
            {"medio": "Noticia al Día", "titular": "Avanzan con éxito las obras de recuperación en la Vereda del Lago de Maracaibo."}
        ]
    }
    crear_boletin_grafico(test_bcv, test_noticia, test_db)
    crear_boletin_grafico_cuadrado(test_bcv, test_noticia, test_db)
    crear_boletin_1200x1500(test_bcv, test_noticia, test_db)


# Constantes compartidas para formatos editoriales
BG_PAGE          = (248, 250, 252, 255)
NAVY_DEEP        = (6,   24,  58,  255)
NAVY_HEADER_TOP  = (8,   32,  75,  255)
NAVY_HEADER_BOT  = (4,   18,  46,  255)
GOLD_ACCENT      = (212, 175, 55,  255)
GOLD_BORDER      = (225, 185, 75,  255)
WHITE            = (255, 255, 255, 255)
BORDER_CARD      = (203, 213, 225, 255)
BORDER_LIGHT     = (226, 232, 240, 255)

def crear_boletin_editorial_vertical_1080x1920(datos_bcv, noticias_5, pensamiento, efemeride, output_path):
    """
    Maqueta el boletín en formato VERTICAL COMPLETO 1080×1920 px (9:16).
    Diseñado específicamente para verse a pantalla completa en smartphones sin barras negras,
    con fuentes GRANDES y legibles a primera vista desde WhatsApp.
    """
    print("🎨 [BOLETÍN VERTICAL 1080×1920] Maquetando con diseño Editorial de Alta Legibilidad...")

    W, H = 1080, 1920
    canvas = Image.new("RGBA", (W, H), BG_PAGE)
    draw = ImageDraw.Draw(canvas)

    # ── TIPOGRAFÍAS MAXIMIZADAS PARA MÓVIL ──
    f_header_title = cargar_fuente("georgiab.ttf",  54)
    f_header_sub   = cargar_fuente("georgiai.ttf",  24)
    f_date_day     = cargar_fuente("segoeui.ttf",   16)
    f_date_num     = cargar_fuente("segoeuib.ttf",  48)
    f_date_month   = cargar_fuente("segoeuib.ttf",  16)
    f_date_year    = cargar_fuente("segoeuib.ttf",  14)

    f_tab          = cargar_fuente("segoeuib.ttf",  16)
    f_tab_lg       = cargar_fuente("segoeuib.ttf",  17)
    f_rate_title   = cargar_fuente("segoeuib.ttf",  16)
    f_rate_val     = cargar_fuente("segoeuib.ttf",  28)

    # Noticias (fuentes mucho más grandes: 23pt y 17pt)
    f_news_title   = cargar_fuente("georgiab.ttf",  23)
    f_news_body    = cargar_fuente("segoeuiz.ttf",  17) # Bold Italic para legibilidad y elegancia
    f_news_medio   = cargar_fuente("segoeuib.ttf",  14)

    # Frase y Efemérides
    f_frase_text   = cargar_fuente("georgiaz.ttf",  25)
    f_frase_author = cargar_fuente("segoeuib.ttf",  18)
    f_efem_date    = cargar_fuente("georgiab.ttf",  22)
    f_efem_body    = cargar_fuente("segoeui.ttf",   18)

    f_footer       = cargar_fuente("segoeuib.ttf",  15)

    ahora = datetime.now()
    dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    dia_nombre = dias_es[ahora.weekday()]
    dia_num    = str(ahora.day)
    mes_nombre = meses_es[ahora.month - 1]
    ano_str    = str(ahora.year)

    # ══════════════════════════════════════════════════════════════
    # 1. CABECERA EDITORIAL (Y: 0 a 175)
    # ══════════════════════════════════════════════════════════════
    HH = 175
    header_grad = crear_degradado_vertical(W, HH, NAVY_HEADER_TOP, NAVY_HEADER_BOT)
    canvas.paste(header_grad, (0, 0))
    draw.line([(0, 1), (W, 1)], fill=GOLD_BORDER, width=3)
    draw.line([(0, HH - 2), (W, HH - 2)], fill=GOLD_BORDER, width=4)

    # Globo terráqueo
    globe_path = os.path.join(BASE_DIR, "assets", "general", "globe.png")
    if os.path.exists(globe_path):
        try:
            gim = Image.open(globe_path).convert("RGBA")
            gim = gim.resize((160, 140), Image.Resampling.LANCZOS)
            canvas.paste(gim, (18, 16), gim)
        except Exception:
            pass

    # Títulos centrales
    cx_hdr = W // 2 - 15
    draw.text((cx_hdr, 58), "NOTICIAS DEL DÍA", fill=WHITE, font=f_header_title, anchor="mm")
    draw.text((cx_hdr, 122), "La actualidad en una sola mirada", fill=(241, 245, 249, 255), font=f_header_sub, anchor="mm")

    # Calendario a la derecha
    bx1, by1, bx2, by2 = W - 145, 16, W - 18, HH - 16
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=10, fill=WHITE, outline=BORDER_CARD, width=1)
    cx_b = (bx1 + bx2) // 2
    draw.text((cx_b, by1 + 22), dia_nombre, fill=(51, 65, 85, 255), font=f_date_day, anchor="mm")
    draw.text((cx_b, by1 + 62), dia_num, fill=NAVY_DEEP, font=f_date_num, anchor="mm")
    draw.text((cx_b, by1 + 104), mes_nombre, fill=(15, 23, 42, 255), font=f_date_month, anchor="mm")
    draw.text((cx_b, by1 + 125), ano_str, fill=(71, 85, 105, 255), font=f_date_year, anchor="mm")

    # ══════════════════════════════════════════════════════════════
    # 2. FRANJA DE COTIZACIONES EN TIEMPO REAL (Y: 190 a 290)
    # ══════════════════════════════════════════════════════════════
    y_cot, h_cot = 190, 100
    draw.rectangle([0, y_cot, W, y_cot + h_cot], fill=WHITE, outline=BORDER_LIGHT, width=1)

    # Pestaña "COTIZACIONES DEL DÍA"
    w_tab_cot, corte_cot = 195, 16
    pts_cot = [(0, y_cot), (w_tab_cot, y_cot), (w_tab_cot - corte_cot, y_cot + h_cot), (0, y_cot + h_cot)]
    draw.polygon(pts_cot, fill=NAVY_DEEP)
    draw.line([(w_tab_cot, y_cot), (w_tab_cot - corte_cot, y_cot + h_cot)], fill=GOLD_ACCENT, width=4)
    draw.text((18, y_cot + 32), "COTIZACIONES", fill=WHITE, font=f_tab_lg, anchor="lm")
    draw.text((18, y_cot + 65), "DEL DÍA", fill=WHITE, font=f_tab_lg, anchor="lm")

    # Bloques de divisas con iconos 50x50 y valores grandes
    icon_usd = os.path.join(BASE_DIR, "assets", "icons", "usd.png")
    icon_eur = os.path.join(BASE_DIR, "assets", "icons", "eur.png")
    icon_bin = os.path.join(BASE_DIR, "assets", "icons", "binance.png")

    usd_val = str(datos_bcv.get("usd", "888,89")) + " Bs"
    eur_val = str(datos_bcv.get("eur", "989,39")) + " Bs"
    bin_val = str(datos_bcv.get("binance", "1005,00")) + " Bs"

    div_blocks = [
        {"x": 230, "icon": icon_usd, "title": "DÓLAR BCV",   "val": usd_val},
        {"x": 515, "icon": icon_eur, "title": "EURO BCV",    "val": eur_val},
        {"x": 800, "icon": icon_bin, "title": "BINANCE P2P", "val": bin_val}
    ]

    for blk in div_blocks:
        xs = blk["x"]
        if os.path.exists(blk["icon"]):
            try:
                ico = Image.open(blk["icon"]).convert("RGBA")
                ico = ico.resize((50, 50), Image.Resampling.LANCZOS)
                canvas.paste(ico, (xs, y_cot + 25), ico)
            except Exception:
                pass
        tx = xs + 62
        draw.text((tx, y_cot + 36), blk["title"], fill=(15, 23, 42, 255), font=f_rate_title, anchor="lm")
        draw.text((tx, y_cot + 68), blk["val"],   fill=NAVY_DEEP, font=f_rate_val, anchor="lm")

    # ══════════════════════════════════════════════════════════════
    # 3. SECCIÓN DE 5 NOTICIAS APILADAS EN ANCHO COMPLETO (Y: 308 a 1358)
    #    Cada tarjeta tiene 1056 px de ancho, con foto a la izq y texto ancho a la der.
    #    ¡Legibilidad absoluta a primera vista!
    # ══════════════════════════════════════════════════════════════
    y_news_start = 308
    card_h = 198
    card_gap = 12
    card_w = W - 24 # 1056 px

    for idx, noti in enumerate(noticias_5[:5]):
        ny = y_news_start + idx * (card_h + card_gap)
        # Fondo tarjeta blanco
        draw.rounded_rectangle([12, ny, 12 + card_w, ny + card_h], radius=10, fill=WHITE, outline=BORDER_CARD, width=1)

        # Pestaña de categoría
        cat_txt = noti.get("categoria", "VENEZUELA")
        dibujar_pestana_editorial(draw, 12, ny, 175, 30, cat_txt, f_tab)

        # Medio de comunicación a la derecha de la pestaña
        medio_txt = noti.get("medio", "")
        if medio_txt:
            draw.text((12 + card_w - 18, ny + 16), medio_txt, fill=(100, 116, 139, 255), font=f_news_medio, anchor="rm")

        # Foto redondeada grande (240x152) a la izquierda
        img_path = noti.get("imagen_local")
        box_img = [24, ny + 38, 264, ny + card_h - 10]
        pegar_imagen_redondeada_ed(canvas, img_path, box_img, radio=8)

        # Contenido textual amplio a la derecha (x: 280 a 1040 -> 760 px de ancho)
        tx_news = 282
        tw_news = card_w - 290 # ~766 px

        titular = noti.get("titular", "")
        t_lines = wrap_text(titular, f_news_title, tw_news)
        ty = ny + 40
        for line in t_lines[:2]: # Máximo 2 líneas de titular grande
            draw.text((tx_news, ty), line, fill=(15, 23, 42, 255), font=f_news_title, anchor="lt")
            ty += 28

        # Resumen en negrita itálica color negro
        resumen = noti.get("resumen", "")
        r_lines = wrap_text(resumen, f_news_body, tw_news)
        ty += 6
        for line in r_lines[:3]: # Máximo 3 líneas de resumen
            draw.text((tx_news, ty), line, fill=(0, 0, 0, 255), font=f_news_body, anchor="lt")
            ty += 22

    # ══════════════════════════════════════════════════════════════
    # 4. FRANJA INFERIOR: FRASE UNIVERSAL + EFEMÉRIDES (Y: 1378 a 1838, alto 460 px)
    # ══════════════════════════════════════════════════════════════
    y_bot = 1378
    h_bot = 460
    w_bot = (W - 36) // 2 # 522 px cada bloque

    # Bloque Izquierdo: LA FRASE UNIVERSAL
    grad_frase = crear_degradado_vertical(w_bot, h_bot, (255, 253, 247, 255), (254, 247, 234, 255))
    canvas.paste(grad_frase, (12, y_bot))
    draw.rounded_rectangle([12, y_bot, 12 + w_bot, y_bot + h_bot], radius=10, outline=BORDER_CARD, width=1)
    dibujar_pestana_editorial(draw, 12, y_bot, 240, 34, "LA FRASE UNIVERSAL", f_tab_lg)

    # Foto del viajero en buen tamaño (180x380 px)
    img_viajero = os.path.join(BASE_DIR, "assets", "general", "frase_viajero.jpg")
    pegar_imagen_redondeada_ed(canvas, img_viajero, [24, y_bot + 46, 184, y_bot + h_bot - 16], radio=8)

    # Frase célebre
    pensa = pensamiento if isinstance(pensamiento, dict) else {}
    f_txt = pensa.get("texto", "La vida es un viaje, no un destino.")
    f_aut = pensa.get("autor", "Anónimo")
    frase_q = f'"{f_txt}"'
    tx_frase = 200
    tw_frase = w_bot - 215

    frase_lines = wrap_text(frase_q, f_frase_text, tw_frase)
    total_fh = len(frase_lines[:6]) * 34 + 36
    ty_frase = y_bot + 46 + max((h_bot - 60 - total_fh) // 2, 0)
    for line in frase_lines[:6]:
        draw.text((tx_frase, ty_frase), line, fill=(15, 23, 42, 255), font=f_frase_text, anchor="lt")
        ty_frase += 34
    if f_aut and f_aut.lower() not in ("anónimo", "anonimo"):
        draw.text((tx_frase, ty_frase + 10), f"— {f_aut}", fill=NAVY_DEEP, font=f_frase_author, anchor="lt")

    # Bloque Derecho: EFEMÉRIDES DE VENEZUELA
    x_efem = 12 + w_bot + 12
    grad_efem = crear_degradado_vertical(w_bot, h_bot, (255, 253, 247, 255), (254, 247, 234, 255))
    canvas.paste(grad_efem, (x_efem, y_bot))
    draw.rounded_rectangle([x_efem, y_bot, x_efem + w_bot, y_bot + h_bot], radius=10, outline=BORDER_CARD, width=1)
    dibujar_pestana_editorial(draw, x_efem, y_bot, 260, 34, "EFEMÉRIDES DE VENEZUELA", f_tab_lg)

    # Formatear texto efeméride
    efem_raw = efemeride if isinstance(efemeride, str) else efemeride.get("texto", "")
    match_ano = re.search(r'\((\d{4})\)', efem_raw)
    ano_efem  = match_ano.group(1) if match_ano else ano_str
    explicacion = re.sub(r'\(\d{4}\)', '', efem_raw)
    if "|" in explicacion:
        partes = explicacion.split("|", 1)
        explicacion = partes[0].strip() + ". " + partes[1].strip()
    explicacion = re.sub(r'\s+', ' ', explicacion).strip()

    # Selección de imagen: Bolívar si lo menciona, de lo contrario Escudo Nacional
    efem_lower = explicacion.lower()
    box_efem = [x_efem + 16, y_bot + 46, x_efem + 186, y_bot + h_bot - 16]
    w_box_e = box_efem[2] - box_efem[0]
    h_box_e = box_efem[3] - box_efem[1]

    if any(k in efem_lower for k in ["bolívar", "bolivar", "libertador"]):
        img_bolivar = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
        pegar_imagen_redondeada_ed(canvas, img_bolivar, box_efem, radio=8)
    else:
        escudo_path = os.path.join(BASE_DIR, "assets", "general", "escudo_venezuela.png")
        if os.path.exists(escudo_path):
            try:
                im_esc = Image.open(escudo_path).convert("RGBA")
                im_esc.thumbnail((w_box_e - 6, h_box_e - 6), Image.Resampling.LANCZOS)
                px_esc = box_efem[0] + (w_box_e - im_esc.width) // 2
                py_esc = box_efem[1] + (h_box_e - im_esc.height) // 2
                canvas.paste(im_esc, (px_esc, py_esc), im_esc)
            except Exception as e_esc:
                print("Error pegando Escudo:", e_esc)

    # Texto de efemérides amplio
    fecha_efem_hdr = f"{dia_num} de {mes_nombre.lower()} de {ano_efem}"
    tx_efem_txt = x_efem + 198
    tw_efem = w_bot - 212

    draw.text((tx_efem_txt, y_bot + 52), fecha_efem_hdr, fill=(15, 23, 42, 255), font=f_efem_date, anchor="lt")
    efem_lines = wrap_text(explicacion, f_efem_body, tw_efem)
    ty_efem = y_bot + 92
    for line in efem_lines[:8]: # Hasta 8 líneas legibles
        draw.text((tx_efem_txt, ty_efem), line, fill=(15, 23, 42, 255), font=f_efem_body, anchor="lt")
        ty_efem += 26

    # ══════════════════════════════════════════════════════════════
    # 5. PIE EDITORIAL (Y: 1850 a 1920)
    # ══════════════════════════════════════════════════════════════
    y_foot = 1850
    draw.rectangle([0, y_foot, W, H], fill=NAVY_DEEP)
    draw.line([(0, y_foot), (W, y_foot)], fill=GOLD_BORDER, width=2)
    foot_text = "Fuentes: Medios Nacionales | Generado Automáticamente · © Ing. LF"
    bbox_ft = f_footer.getbbox(foot_text)
    ft_w = bbox_ft[2] - bbox_ft[0]
    cx_ft = W // 2
    draw.line([(60, y_foot + 35), (cx_ft - (ft_w // 2) - 20, y_foot + 35)], fill=GOLD_BORDER, width=2)
    draw.line([(cx_ft + (ft_w // 2) + 20, y_foot + 35), (W - 60, y_foot + 35)], fill=GOLD_BORDER, width=2)
    draw.text((cx_ft, y_foot + 35), foot_text, fill=(241, 245, 249, 255), font=f_footer, anchor="mm")

    # Guardar imagen optimizada
    canvas.save(output_path, "PNG", optimize=True)
    print(f"🎉 ¡Boletín Vertical 1080×1920 guardado exitosamente en: {output_path}!")
    return output_path

def crear_boletin_editorial_feed_1080x1350(datos_bcv, noticias_5, pensamiento, efemeride, output_path):
    """
    Maqueta el boletín en formato VERTICAL FEED 1080×1350 px (4:5).
    270 píxeles más alto que el cuadrado, con tipografías más amplias y proporciones balanceadas.
    """
    print("🎨 [BOLETÍN FEED 1080×1350] Maquetando versión 4:5...")

    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), BG_PAGE)
    draw = ImageDraw.Draw(canvas)

    f_header_title = cargar_fuente("georgiab.ttf",  54)
    f_header_sub   = cargar_fuente("georgiai.ttf",  22)
    f_date_day     = cargar_fuente("segoeui.ttf",   15)
    f_date_num     = cargar_fuente("segoeuib.ttf",  46)
    f_date_month   = cargar_fuente("segoeuib.ttf",  15)
    f_date_year    = cargar_fuente("segoeuib.ttf",  13)

    f_tab          = cargar_fuente("segoeuib.ttf",  15)
    f_tab_lg       = cargar_fuente("segoeuib.ttf",  16)
    f_rate_title   = cargar_fuente("segoeuib.ttf",  15)
    f_rate_val     = cargar_fuente("segoeuib.ttf",  26)

    # Noticias fila 1 (grandes)
    f_news_t1      = cargar_fuente("georgiab.ttf",  19)
    f_news_r1      = cargar_fuente("segoeuiz.ttf",  14) # Bold Italic más grande
    # Noticias fila 2
    f_news_t2      = cargar_fuente("georgiab.ttf",  16)
    f_news_r2      = cargar_fuente("segoeuiz.ttf",  13)

    # Frase & Efemérides
    f_frase_text   = cargar_fuente("georgiaz.ttf",  23)
    f_frase_author = cargar_fuente("segoeuib.ttf",  15)
    f_efem_date    = cargar_fuente("georgiab.ttf",  20)
    f_efem_body    = cargar_fuente("segoeui.ttf",   15)

    f_footer       = cargar_fuente("segoeuib.ttf",  14)

    ahora = datetime.now()
    dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    dia_nombre = dias_es[ahora.weekday()]
    dia_num    = str(ahora.day)
    mes_nombre = meses_es[ahora.month - 1]
    ano_str    = str(ahora.year)

    # 1. Cabecera (Y: 0 a 150)
    HH = 150
    header_grad = crear_degradado_vertical(W, HH, NAVY_HEADER_TOP, NAVY_HEADER_BOT)
    canvas.paste(header_grad, (0, 0))
    draw.line([(0, 1), (W, 1)], fill=GOLD_BORDER, width=2)
    draw.line([(0, HH - 2), (W, HH - 2)], fill=GOLD_BORDER, width=3)

    globe_path = os.path.join(BASE_DIR, "assets", "general", "globe.png")
    if os.path.exists(globe_path):
        try:
            gim = Image.open(globe_path).convert("RGBA")
            gim = gim.resize((150, 125), Image.Resampling.LANCZOS)
            canvas.paste(gim, (16, 12), gim)
        except Exception:
            pass

    cx_hdr = W // 2 - 15
    draw.text((cx_hdr, 50), "NOTICIAS DEL DÍA", fill=WHITE, font=f_header_title, anchor="mm")
    draw.text((cx_hdr, 108), "La actualidad en una sola mirada", fill=(241, 245, 249, 255), font=f_header_sub, anchor="mm")

    bx1, by1, bx2, by2 = W - 142, 14, W - 18, HH - 14
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=8, fill=WHITE, outline=BORDER_CARD, width=1)
    cx_b = (bx1 + bx2) // 2
    draw.text((cx_b, by1 + 18), dia_nombre, fill=(51, 65, 85, 255), font=f_date_day, anchor="mm")
    draw.text((cx_b, by1 + 54), dia_num, fill=NAVY_DEEP, font=f_date_num, anchor="mm")
    draw.text((cx_b, by1 + 90), mes_nombre, fill=(15, 23, 42, 255), font=f_date_month, anchor="mm")
    draw.text((cx_b, by1 + 109), ano_str, fill=(71, 85, 105, 255), font=f_date_year, anchor="mm")

    # 2. Cotizaciones (Y: 162 a 252)
    y_cot, h_cot = 162, 90
    draw.rectangle([0, y_cot, W, y_cot + h_cot], fill=WHITE, outline=BORDER_LIGHT, width=1)

    w_tab_cot, corte_cot = 185, 15
    pts_cot = [(0, y_cot), (w_tab_cot, y_cot), (w_tab_cot - corte_cot, y_cot + h_cot), (0, y_cot + h_cot)]
    draw.polygon(pts_cot, fill=NAVY_DEEP)
    draw.line([(w_tab_cot, y_cot), (w_tab_cot - corte_cot, y_cot + h_cot)], fill=GOLD_ACCENT, width=4)
    draw.text((18, y_cot + 28), "COTIZACIONES", fill=WHITE, font=f_tab_lg, anchor="lm")
    draw.text((18, y_cot + 58), "DEL DÍA", fill=WHITE, font=f_tab_lg, anchor="lm")

    icon_usd = os.path.join(BASE_DIR, "assets", "icons", "usd.png")
    icon_eur = os.path.join(BASE_DIR, "assets", "icons", "eur.png")
    icon_bin = os.path.join(BASE_DIR, "assets", "icons", "binance.png")

    usd_val = str(datos_bcv.get("usd", "888,89")) + " Bs"
    eur_val = str(datos_bcv.get("eur", "989,39")) + " Bs"
    bin_val = str(datos_bcv.get("binance", "1005,20")) + " Bs"

    div_blocks = [
        {"x": 225, "icon": icon_usd, "title": "DÓLAR BCV",   "val": usd_val},
        {"x": 510, "icon": icon_eur, "title": "EURO BCV",    "val": eur_val},
        {"x": 785, "icon": icon_bin, "title": "BINANCE P2P", "val": bin_val}
    ]

    for blk in div_blocks:
        xs = blk["x"]
        if os.path.exists(blk["icon"]):
            try:
                ico = Image.open(blk["icon"]).convert("RGBA")
                ico = ico.resize((46, 46), Image.Resampling.LANCZOS)
                canvas.paste(ico, (xs, y_cot + 22), ico)
            except Exception:
                pass
        tx = xs + 56
        draw.text((tx, y_cot + 32), blk["title"], fill=(15, 23, 42, 255), font=f_rate_title, anchor="lm")
        draw.text((tx, y_cot + 60), blk["val"],   fill=NAVY_DEEP, font=f_rate_val, anchor="lm")

    # 3. Sección de Noticias (Y: 265 a 935)
    # Fila 1: 2 noticias principales (Y: 265 a 575, Alto: 310 px) -> Mucho más altas y legibles!
    y_r1 = 265
    h_r1 = 310
    w_r1 = 522

    for col_idx in range(2):
        n = noticias_5[col_idx] if col_idx < len(noticias_5) else {}
        x0 = 12 + col_idx * (w_r1 + 12)
        draw.rounded_rectangle([x0, y_r1, x0 + w_r1, y_r1 + h_r1], radius=8, fill=WHITE, outline=BORDER_CARD, width=1)
        dibujar_pestana_editorial(draw, x0, y_r1, 160, 32, n.get("categoria", ""), f_tab)
        
        # Imagen grande
        img_n = n.get("imagen_local")
        pegar_imagen_redondeada_ed(canvas, img_n, [x0 + 12, y_r1 + 42, x0 + 215, y_r1 + h_r1 - 12], radio=6)

        # Texto a la derecha
        t_lines = wrap_text(n.get("titular", ""), f_news_t1, 285)
        ty = y_r1 + 46
        for line in t_lines[:3]:
            draw.text((x0 + 225, ty), line, fill=(15, 23, 42, 255), font=f_news_t1, anchor="lt")
            ty += 25
        r_lines = wrap_text(n.get("resumen", ""), f_news_r1, 285)
        ty += 8
        for line in r_lines[:4]:
            draw.text((x0 + 225, ty), line, fill=(0, 0, 0, 255), font=f_news_r1, anchor="lt")
            ty += 20

    # Fila 2: 3 noticias secundarias (Y: 588 a 938, Alto: 350 px)
    y_r2 = 588
    h_r2 = 350
    w_r2 = 344
    gap_r2 = 12

    for idx, noti in enumerate(noticias_5[2:5]):
        nx = 12 + idx * (w_r2 + gap_r2)
        draw.rounded_rectangle([nx, y_r2, nx + w_r2, y_r2 + h_r2], radius=8, fill=WHITE, outline=BORDER_CARD, width=1)
        dibujar_pestana_editorial(draw, nx, y_r2, 155, 30, noti.get("categoria", ""), f_tab)

        img_n2 = noti.get("imagen_local")
        pegar_imagen_redondeada_ed(canvas, img_n2, [nx + 10, y_r2 + 38, nx + 130, y_r2 + 195], radio=6)

        tx_pos = nx + 138
        tw_max = w_r2 - 146
        t_lines = wrap_text(noti.get("titular", ""), f_news_t2, tw_max)
        ty = y_r2 + 42
        for line in t_lines[:4]:
            draw.text((tx_pos, ty), line, fill=(15, 23, 42, 255), font=f_news_t2, anchor="lt")
            ty += 21

        # Resumen en bloque inferior amplio a todo lo ancho de la tarjeta
        r_lines = wrap_text(noti.get("resumen", ""), f_news_r2, w_r2 - 20)
        ty_r = y_r2 + 205
        for line in r_lines[:4]:
            draw.text((nx + 10, ty_r), line, fill=(0, 0, 0, 255), font=f_news_r2, anchor="lt")
            ty_r += 18

    # 4. Franja Inferior: Frase & Efemérides (Y: 950 a 1290, Alto: 340 px)
    y_bot = 950
    h_bot = 340
    w_bot = 522

    # Frase Universal
    grad_frase = crear_degradado_vertical(w_bot, h_bot, (255, 253, 247, 255), (254, 247, 234, 255))
    canvas.paste(grad_frase, (12, y_bot))
    draw.rounded_rectangle([12, y_bot, 12 + w_bot, y_bot + h_bot], radius=8, outline=BORDER_CARD, width=1)
    dibujar_pestana_editorial(draw, 12, y_bot, 220, 32, "LA FRASE UNIVERSAL", f_tab_lg)
    img_viajero = os.path.join(BASE_DIR, "assets", "general", "frase_viajero.jpg")
    pegar_imagen_redondeada_ed(canvas, img_viajero, [24, y_bot + 44, 180, y_bot + h_bot - 14], radio=6)

    pensa = pensamiento if isinstance(pensamiento, dict) else {}
    f_txt = pensa.get("texto", "La vida es un viaje, no un destino.")
    f_aut = pensa.get("autor", "Anónimo")
    frase_q = f'"{f_txt}"'
    frase_lines = wrap_text(frase_q, f_frase_text, 310)
    ty_f = y_bot + 52
    for line in frase_lines[:5]:
        draw.text((195, ty_f), line, fill=(15, 23, 42, 255), font=f_frase_text, anchor="lt")
        ty_f += 32
    if f_aut and f_aut.lower() not in ("anónimo", "anonimo"):
        draw.text((195, ty_f + 8), f"— {f_aut}", fill=NAVY_DEEP, font=f_frase_author, anchor="lt")

    # Efemérides
    x_efem = 12 + w_bot + 12
    grad_efem = crear_degradado_vertical(w_bot, h_bot, (255, 253, 247, 255), (254, 247, 234, 255))
    canvas.paste(grad_efem, (x_efem, y_bot))
    draw.rounded_rectangle([x_efem, y_bot, x_efem + w_bot, y_bot + h_bot], radius=8, outline=BORDER_CARD, width=1)
    dibujar_pestana_editorial(draw, x_efem, y_bot, 245, 32, "EFEMÉRIDES DE VENEZUELA", f_tab_lg)

    efem_raw = efemeride if isinstance(efemeride, str) else efemeride.get("texto", "")
    match_ano = re.search(r'\((\d{4})\)', efem_raw)
    ano_efem  = match_ano.group(1) if match_ano else ano_str
    explicacion = re.sub(r'\(\d{4}\)', '', efem_raw)
    if "|" in explicacion:
        partes = explicacion.split("|", 1)
        explicacion = partes[0].strip() + ". " + partes[1].strip()
    explicacion = re.sub(r'\s+', ' ', explicacion).strip()

    box_efem = [x_efem + 12, y_bot + 44, x_efem + 165, y_bot + h_bot - 14]
    w_box_e = box_efem[2] - box_efem[0]
    h_box_e = box_efem[3] - box_efem[1]

    if any(k in explicacion.lower() for k in ["bolívar", "bolivar", "libertador"]):
        img_bolivar = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
        pegar_imagen_redondeada_ed(canvas, img_bolivar, box_efem, radio=6)
    else:
        escudo_path = os.path.join(BASE_DIR, "assets", "general", "escudo_venezuela.png")
        if os.path.exists(escudo_path):
            try:
                im_esc = Image.open(escudo_path).convert("RGBA")
                im_esc.thumbnail((w_box_e - 6, h_box_e - 6), Image.Resampling.LANCZOS)
                px_esc = box_efem[0] + (w_box_e - im_esc.width) // 2
                py_esc = box_efem[1] + (h_box_e - im_esc.height) // 2
                canvas.paste(im_esc, (px_esc, py_esc), im_esc)
            except Exception as e_esc:
                print("Error pegando Escudo:", e_esc)

    fecha_efem_hdr = f"{dia_num} de {mes_nombre.lower()} de {ano_efem}"
    tx_efem_txt = x_efem + 178
    tw_efem = w_bot - 190
    draw.text((tx_efem_txt, y_bot + 48), fecha_efem_hdr, fill=(15, 23, 42, 255), font=f_efem_date, anchor="lt")
    efem_lines = wrap_text(explicacion, f_efem_body, tw_efem)
    ty_e = y_bot + 84
    for line in efem_lines[:6]:
        draw.text((tx_efem_txt, ty_e), line, fill=(15, 23, 42, 255), font=f_efem_body, anchor="lt")
        ty_e += 24

    # 5. Pie editorial (Y: 1300 a 1350)
    y_foot = 1300
    draw.rectangle([0, y_foot, W, H], fill=NAVY_DEEP)
    draw.line([(0, y_foot), (W, y_foot)], fill=GOLD_BORDER, width=2)
    foot_text = "Fuentes: Medios Nacionales | Generado Automáticamente · © Ing. LF"
    bbox_ft = f_footer.getbbox(foot_text)
    ft_w = bbox_ft[2] - bbox_ft[0]
    cx_ft = W // 2
    draw.line([(70, y_foot + 25), (cx_ft - (ft_w // 2) - 20, y_foot + 25)], fill=GOLD_BORDER, width=2)
    draw.line([(cx_ft + (ft_w // 2) + 20, y_foot + 25), (W - 70, y_foot + 25)], fill=GOLD_BORDER, width=2)
    draw.text((cx_ft, y_foot + 25), foot_text, fill=(241, 245, 249, 255), font=f_footer, anchor="mm")

    canvas.save(output_path, "PNG", optimize=True)
    print(f"🎉 ¡Boletín Feed 1080×1350 guardado en: {output_path}!")
    return output_path
