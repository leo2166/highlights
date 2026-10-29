from render_exact_chatgpt import renderizar_boletin_exacto_chatgpt
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
    """Genera la portada editorial 1080x1080 px identica a la maqueta ChatGPT."""
    noticias_5 = datos_db.get('titulares_medios', [])
    pensamiento = datos_db.get('pensamiento', {})
    efemeride = datos_db.get('efemeride_venezuela', '')
    out_local = os.path.join(BASE_DIR, 'boletin_highlights_cuadrado.png')
    renderizar_boletin_exacto_chatgpt(1080, 1080, datos_bcv, noticias_5, pensamiento, efemeride, out_local)
    if os.path.exists(ESCRITORIO):
        out_esc = os.path.join(ESCRITORIO, 'boletin_highlights_cuadrado.png')
        try:
            import shutil
            shutil.copyfile(out_local, out_esc)
        except Exception:
            pass
    return out_local



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
    """Genera el boletin vertical 1080x1920 px (9:16) identico a la maqueta ChatGPT."""
    return renderizar_boletin_exacto_chatgpt(1080, 1920, datos_bcv, noticias_5, pensamiento, efemeride, output_path)



def crear_boletin_editorial_feed_1080x1350(datos_bcv, noticias_5, pensamiento, efemeride, output_path):
    """Genera el boletin vertical feed 1080x1350 px (4:5) identico a la maqueta ChatGPT."""
    return renderizar_boletin_exacto_chatgpt(1080, 1350, datos_bcv, noticias_5, pensamiento, efemeride, output_path)

