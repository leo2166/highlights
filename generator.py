from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from config import (
    CANVAS_WIDTH, CANVAS_HEIGHT, BG_GRADIENT_START, BG_GRADIENT_END,
    CARD_BG_COLOR, CARD_BORDER_COLOR, TEXT_PRIMARY_COLOR, TEXT_SECONDARY_COLOR,
    YELLOW_ACCENT_BG, YELLOW_ACCENT_TEXT, HEADER_GOLD_COLOR, MUNDIAL_FECHA,
    FONT_TITLE, FONT_BOLD, FONT_REGULAR, OUTPUT_IMAGE_PATH, BACKUP_IMAGE_PATH
)

def crear_degradado_vertical(width, height, start_color, end_color):
    """Genera una imagen con un degradado vertical suave de color."""
    base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    
    for y in range(height):
        # Interpolación lineal de cada canal de color (R, G, B)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * (y / height))
        g = int(start_color[1] + (end_color[1] - start_color[1]) * (y / height))
        b = int(start_color[2] + (end_color[2] - start_color[2]) * (y / height))
        
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        
    return base

def wrap_text(text, font, max_width):
    """Divide un texto largo en múltiples líneas que se ajusten a un ancho máximo en píxeles."""
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        # Medir ancho de la línea de prueba usando getbbox (Pillow 10+)
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(' '.join(current_line))
        
    return lines

def calcular_dias_mundial():
    """Calcula los días restantes hasta la fecha de inicio del Mundial de Fútbol 2026."""
    try:
        target = datetime.strptime(MUNDIAL_FECHA, "%Y-%m-%d")
        now = datetime.now()
        # Forzar hora a inicio del día para cálculo limpio de días
        target = target.replace(hour=0, minute=0, second=0, microsecond=0)
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)
        dias = (target - now).days
        return max(0, dias)
    except Exception:
        # Fallback histórico
        return 937

def cargar_fuente(ruta_fuente, tamano):
    """Intenta cargar una fuente TrueType; si falla, carga la fuente por defecto del sistema."""
    try:
        if os.path.exists(ruta_fuente):
            return ImageFont.truetype(ruta_fuente, tamano)
        else:
            # Buscar fuentes alternativas en la carpeta del sistema por si cambian de nombre
            alternativas = ["arial.ttf", "tahoma.ttf", "segoeui.ttf"]
            for alt in alternativas:
                alt_path = os.path.join("C:\\Windows\\Fonts", alt)
                if os.path.exists(alt_path):
                    return ImageFont.truetype(alt_path, tamano)
            return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()

def crear_boletin_grafico(datos_bcv, datos_noticia, datos_db):
    """
    Maqueta y dibuja el Flyer de Highlights usando Pillow (PIL)
    con ondas corporativas azules y estilo de tarjetas premium con sombras flotantes
    y lo guarda como una imagen PNG.
    """
    print("🎨 Iniciando maquetación gráfica del Flyer con Pillow...")
    
    # 1. Crear el Lienzo Base con Fondo Blanco Puro
    img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 2. Rellenar fondo con degradado vertical sutil (blanco a gris azulado claro)
    start_color = (250, 252, 255)
    end_color = (238, 243, 250)
    for y in range(CANVAS_HEIGHT):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * (y / CANVAS_HEIGHT))
        g = int(start_color[1] + (end_color[1] - start_color[1]) * (y / CANVAS_HEIGHT))
        b = int(start_color[2] + (end_color[2] - start_color[2]) * (y / CANVAS_HEIGHT))
        draw.line([(0, y), (CANVAS_WIDTH, y)], fill=(r, g, b, 255))
    
    # 3. Cargar Fuentes
    font_title_large = cargar_fuente(FONT_TITLE, 26)
    font_sub = cargar_fuente(FONT_BOLD, 16)
    font_buenos_dias = cargar_fuente(FONT_BOLD, 21)
    font_header_data = cargar_fuente(FONT_BOLD, 12)
    font_card_title = cargar_fuente(FONT_BOLD, 14)
    font_text = cargar_fuente(FONT_REGULAR, 16)      
    font_card_title_1_4 = cargar_fuente(FONT_BOLD, 15) 
    font_text_1_4 = cargar_fuente(FONT_REGULAR, 14)
    font_days = cargar_fuente(FONT_TITLE, 36)
    font_footer = cargar_fuente(FONT_REGULAR, 10)

    # Helper para calcular curvas Bézier
    def calcular_bezier(p0, p1, p2, p3, steps=40):
        points = []
        for i in range(steps + 1):
            t = i / steps
            x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
            points.append((x, y))
        return points

    # --- ONDAS CORPORATIVAS EN EL ENCABEZADO ---
    scale = 4
    header_w = CANVAS_WIDTH * scale
    header_h = 100 * scale
    header_temp = Image.new("RGBA", (header_w, header_h), (0, 0, 0, 0))
    header_draw = ImageDraw.Draw(header_temp)

    # Onda 1: Azul Brillante (Cyan) de fondo en alta resolución (escalada a 100px de alto, desplazada proporcionalmente)
    p0_c = (0 * scale, 70 * scale)
    p1_c = (194 * scale, 27 * scale)
    p2_c = (405 * scale, 100 * scale)
    p3_c = (600 * scale, 57 * scale)
    puntos_cyan = calcular_bezier(p0_c, p1_c, p2_c, p3_c)
    puntos_cyan = [(0, 0)] + puntos_cyan + [(header_w, 0)]
    header_draw.polygon(puntos_cyan, fill=(0, 150, 224, 255))
    
    # Onda 2: Azul Marino (Navy) superpuesta en alta resolución
    p0_n = (0 * scale, 50 * scale)
    p1_n = (194 * scale, 90 * scale)
    p2_n = (405 * scale, 30 * scale)
    p3_n = (600 * scale, 70 * scale)
    puntos_navy = calcular_bezier(p0_n, p1_n, p2_n, p3_n)
    puntos_navy = [(0, 0)] + puntos_navy + [(header_w, 0)]
    header_draw.polygon(puntos_navy, fill=(15, 55, 135, 255))

    # Redimensionar el encabezado a su tamaño original usando filtro LANCZOS
    header_smooth = header_temp.resize((CANVAS_WIDTH, 100), Image.Resampling.LANCZOS)
    img.paste(header_smooth, (0, 0), header_smooth)

    # Helper para dibujar Tarjetas con Sombra Proyectada (efecto premium 3D sutil)
    def draw_card_with_shadow(rect, radius, fill_color, outline_color):
        shadow_rect = [rect[0] + 3, rect[1] + 4, rect[2] + 3, rect[3] + 4]
        draw.rounded_rectangle(shadow_rect, radius=radius, fill=(0, 0, 0, 12))
        draw.rounded_rectangle(rect, radius=radius, fill=fill_color, outline=outline_color, width=1)

    # --- A. ENCABEZADO "HIGHLIGHT" ---
    # Fecha y Hora del Boletín
    ahora = datetime.now()
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses_ano = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    fecha_formateada = f"{dias_semana[ahora.weekday()]} {ahora.day} de {meses_ano[ahora.month - 1]} de {ahora.year}"
    hora_formateada = ahora.strftime("%I:%M %p")

    # Título Highlights en blanco sobre ondas, alineado a la izquierda
    draw.text((35, 16), "HIGHLIGHT", fill=(255, 255, 255, 255), font=font_title_large, anchor="lt")
    
    # Cargar y redimensionar el icono del sol
    sun_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sun_icon.png")
    sun_size = 33
    sun_icon = None
    if os.path.exists(sun_path):
        try:
            sun_img = Image.open(sun_path).convert("RGBA")
            datas = sun_img.getdata()
            newData = []
            for item in datas:
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)
            sun_img.putdata(newData)
            sun_icon = sun_img.resize((sun_size, sun_size), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"⚠️ No se pudo procesar el icono del sol: {str(e)}")

    # Saludo "¡Buenos Días!" en blanco a la derecha sobre las ondas
    saludo_texto = "¡Buenos Días!"
    text_bbox = font_buenos_dias.getbbox(saludo_texto)
    text_width = text_bbox[2] - text_bbox[0]
    spacing = 8
    
    y_center_saludo = 32  # Alineado verticalmente con HIGHLIGHT
    
    if sun_icon:
        total_width = sun_size + spacing + text_width
        start_x = CANVAS_WIDTH - 35 - total_width
        sun_y = y_center_saludo - sun_size // 2
        img.paste(sun_icon, (start_x, sun_y), sun_icon)
        text_x = start_x + sun_size + spacing
        draw.text((text_x, y_center_saludo), saludo_texto, fill=(255, 255, 255, 255), font=font_buenos_dias, anchor="lm")
    else:
        draw.text((CANVAS_WIDTH - 35, y_center_saludo), saludo_texto, fill=(255, 255, 255, 255), font=font_buenos_dias, anchor="rm")

    # --- FILA DE FECHA Y HORA (EN LA ZONA BLANCA DEBAJO DE LAS ONDAS) ---
    y_date_time = 108
    y_center_icons = 115
    color_dark = (30, 30, 30, 255) # Gris carbón oscuro ultra-legible
    
    # 1. Dibujar Icono del Calendario (Vectorial)
    cx_cal = 35
    cy_cal = y_center_icons - 6
    # Rectángulo base del calendario
    draw.rectangle([cx_cal, cy_cal, cx_cal + 14, cy_cal + 13], outline=color_dark, width=1)
    # Línea horizontal interna
    draw.line([(cx_cal, cy_cal + 4), (cx_cal + 14, cy_cal + 4)], fill=color_dark, width=1)
    # Dos pequeñas anillas superiores
    draw.line([(cx_cal + 3, cy_cal - 2), (cx_cal + 3, cy_cal)], fill=color_dark, width=1)
    draw.line([(cx_cal + 11, cy_cal - 2), (cx_cal + 11, cy_cal)], fill=color_dark, width=1)
    
    # Dibujar texto de la Fecha
    draw.text((56, y_date_time), f"{fecha_formateada}", fill=color_dark, font=font_header_data, anchor="lt")
    
    # 2. Obtener y medir texto de la Hora
    hora_text = f"{hora_formateada}"
    hora_bbox = font_header_data.getbbox(hora_text)
    hora_w = hora_bbox[2] - hora_bbox[0]
    
    # Dibujar Icono del Reloj (Vectorial) a la izquierda del texto de la hora
    cx_clock = CANVAS_WIDTH - 35 - hora_w - 14
    cy_clock = y_center_icons
    r_clock = 6
    # Círculo del reloj
    draw.ellipse([cx_clock - r_clock, cy_clock - r_clock, cx_clock + r_clock, cy_clock + r_clock], outline=color_dark, width=1)
    # Manecillas (una vertical hacia arriba y otra horizontal/diagonal)
    draw.line([(cx_clock, cy_clock), (cx_clock, cy_clock - 3)], fill=color_dark, width=1)
    draw.line([(cx_clock, cy_clock), (cx_clock + 3, cy_clock + 1)], fill=color_dark, width=1)
    
    # Dibujar texto de la Hora
    draw.text((CANVAS_WIDTH - 35, y_date_time), hora_text, fill=color_dark, font=font_header_data, anchor="ra")
        
    # --- B. TARJETA 1: PENSAMIENTO UNIVERSAL ---
    y_start = 135
    card_height = 85
    draw_card_with_shadow([30, y_start, CANVAS_WIDTH - 30, y_start + card_height], 10, CARD_BG_COLOR, CARD_BORDER_COLOR)
    # Título interno
    draw.text((45, y_start + 10), "□ PENSAMIENTO UNIVERSAL", fill=TEXT_SECONDARY_COLOR, font=font_card_title_1_4)
    # Línea separadora de título interna
    draw.line([(45, y_start + 26), (CANVAS_WIDTH - 45, y_start + 26)], fill=(220, 225, 235, 255), width=1)
    # Contenido
    pensamiento = datos_db["pensamiento"]
    texto_p = f"\"{pensamiento['texto']}\" — {pensamiento['autor']}."
    wrapped_p = wrap_text(texto_p, font_text_1_4, 510)
    
    line_y = y_start + 32
    for line in wrapped_p[:3]: # Soporte hasta 3 líneas
        draw.text((45, line_y), line, fill=TEXT_PRIMARY_COLOR, font=font_text_1_4)
        line_y += 16

    # --- C. TARJETA 2: EFEMÉRIDES UNIVERSAL ---
    y_start = 230
    card_height = 90
    draw_card_with_shadow([30, y_start, CANVAS_WIDTH - 30, y_start + card_height], 10, CARD_BG_COLOR, CARD_BORDER_COLOR)
    # Título interno
    draw.text((45, y_start + 10), "□ EFEMÉRIDES UNIVERSAL", fill=TEXT_SECONDARY_COLOR, font=font_card_title_1_4)
    # Línea separadora
    draw.line([(45, y_start + 26), (CANVAS_WIDTH - 45, y_start + 26)], fill=(220, 225, 235, 255), width=1)
    # Contenido
    efemeride_u = datos_db["efemeride_universal"]
    wrapped_e = wrap_text(efemeride_u, font_text_1_4, 510)
    
    line_y = y_start + 32
    for line in wrapped_e[:3]: # Soporte hasta 3 líneas para evitar cortes
        draw.text((45, line_y), line, fill=TEXT_PRIMARY_COLOR, font=font_text_1_4)
        line_y += 16

    # --- D. TARJETA 3: EFEMÉRIDES VENEZUELA ---
    y_start = 330
    card_height = 90
    draw_card_with_shadow([30, y_start, CANVAS_WIDTH - 30, y_start + card_height], 10, CARD_BG_COLOR, CARD_BORDER_COLOR)
    # Título interno
    draw.text((45, y_start + 10), "□ EFEMÉRIDES VENEZUELA", fill=TEXT_SECONDARY_COLOR, font=font_card_title_1_4)
    # Línea separadora
    draw.line([(45, y_start + 26), (CANVAS_WIDTH - 45, y_start + 26)], fill=(220, 225, 235, 255), width=1)
    # Contenido
    efemeride_v = datos_db["efemeride_venezuela"]
    wrapped_ev = wrap_text(efemeride_v, font_text_1_4, 510)
    
    line_y = y_start + 32
    for line in wrapped_ev[:3]: # Soporte hasta 3 líneas
        draw.text((45, line_y), line, fill=TEXT_PRIMARY_COLOR, font=font_text_1_4)
        line_y += 16

    # --- E. TARJETA 4: NOTICIA DESTACADA ---
    y_start = 430
    card_height = 85
    draw_card_with_shadow([30, y_start, CANVAS_WIDTH - 30, y_start + card_height], 10, CARD_BG_COLOR, CARD_BORDER_COLOR)
    # Título interno
    draw.text((45, y_start + 10), "□ NOTICIA DESTACADA", fill=TEXT_SECONDARY_COLOR, font=font_card_title_1_4)
    # Línea separadora
    draw.line([(45, y_start + 26), (CANVAS_WIDTH - 45, y_start + 26)], fill=(220, 225, 235, 255), width=1)
    # Contenido
    noticia_titulo = datos_noticia["titulo"]
    wrapped_n = wrap_text(noticia_titulo, font_text_1_4, 510)
    
    line_y = y_start + 32
    for line in wrapped_n[:3]: # Soporte hasta 3 líneas
        draw.text((45, line_y), line, fill=TEXT_PRIMARY_COLOR, font=font_text_1_4)
        line_y += 16

    # --- E2. TARJETA UNIFICADA: PARIDAD CAMBIARIA (3 COLUMNAS: DÓLAR · EURO · BINANCE) ---
    y_start = 525
    card_height = 90
    card_left = 30
    card_right = CANVAS_WIDTH - 30
    card_inner_w = card_right - card_left  # 540px

    # Tarjeta contenedora única
    draw_card_with_shadow([card_left, y_start, card_right, y_start + card_height], 10, CARD_BG_COLOR, CARD_BORDER_COLOR)

    # Título centrado de la tarjeta
    draw.text((CANVAS_WIDTH // 2, y_start + 10), "PARIDAD CAMBIARIA (Bs.)", fill=TEXT_SECONDARY_COLOR, font=font_card_title, anchor="mm")
    # Línea separadora de título
    draw.line([(card_left + 15, y_start + 22), (card_right - 15, y_start + 22)], fill=(220, 225, 235, 255), width=1)

    # Definir las 3 sub-columnas de igual ancho
    col_w = card_inner_w // 3  # 180px aprox cada una
    col_centers = [
        card_left + col_w // 2,               # Centro col Dólar
        card_left + col_w + col_w // 2,       # Centro col Euro
        card_left + col_w * 2 + col_w // 2,   # Centro col Binance
    ]
    labels = ["Dólar ($)", "Euro (€)", "Binance (₿)"]
    values = [
        datos_bcv.get("usd", "N/D"),
        datos_bcv.get("eur", "N/D"),
        datos_bcv.get("binance", "N/D"),
    ]
    font_col_label = cargar_fuente(FONT_BOLD, 11)
    font_col_value = cargar_fuente(FONT_BOLD, 18)

    for i, (cx, label, val) in enumerate(zip(col_centers, labels, values)):
        # Línea divisora vertical entre columnas (no al final)
        if i > 0:
            div_x = card_left + col_w * i
            draw.line([(div_x, y_start + 26), (div_x, y_start + card_height - 8)], fill=(210, 215, 225, 255), width=1)
        # Etiqueta pequeña
        draw.text((cx, y_start + 34), label, fill=TEXT_SECONDARY_COLOR, font=font_col_label, anchor="mm")
        # Valor en negrita
        draw.text((cx, y_start + 62), val, fill=TEXT_PRIMARY_COLOR, font=font_col_value, anchor="mm")

    # Fuente debajo de la tarjeta
    draw.text((CANVAS_WIDTH // 2, y_start + card_height + 10),
              "FUENTE BCV, TASA OFICIAL  ·  BINANCE P2P (USDT/VES)",
              fill=(120, 120, 120), font=font_footer, anchor="mm")



    # --- G. TARJETA 6: CUENTA REGRESIVA MUNDIAL FÚTBOL 2026 ---
    y_start = 645
    card_height = 110
    # Doble marco gris redondeado
    draw_card_with_shadow([30, y_start, CANVAS_WIDTH - 30, y_start + card_height], 12, CARD_BG_COLOR, (80, 80, 80, 255))
    draw.rounded_rectangle([34, y_start + 4, CANVAS_WIDTH - 34, y_start + card_height - 4], radius=10, fill=None, outline=(200, 200, 200, 255), width=1)
    
    # Título del Mundial
    draw.text((CANVAS_WIDTH // 2, y_start + 18), "□ CUENTA REGRESIVA MUNDIAL FÚTBOL 2026", fill=TEXT_SECONDARY_COLOR, font=font_card_title, anchor="mm")
    
    # Días restantes
    dias_restantes = calcular_dias_mundial()
    texto_dias = f"{dias_restantes} DÍAS"
    
    # Sombra proyectada clásica (Drop Shadow)
    draw.text((CANVAS_WIDTH // 2 + 2, y_start + 55 + 2), texto_dias, fill=(0, 0, 0, 35), font=font_days, anchor="mm")
    
    # Texto verde brillante principal
    draw.text((CANVAS_WIDTH // 2, y_start + 55), texto_dias, fill=(46, 204, 113, 255), font=font_days, anchor="mm")
    
    # Subtítulo del Mundial
    draw.text((CANVAS_WIDTH // 2, y_start + 88), "Para el pitazo inicial en Norteamérica", fill=TEXT_SECONDARY_COLOR, font=font_sub, anchor="mm")

    # --- H. PIE DE PÁGINA (FIRMA) ---
    draw.text((CANVAS_WIDTH // 2, CANVAS_HEIGHT - 18), "Generado Automáticamente | © Ing. LF", fill=TEXT_SECONDARY_COLOR, font=font_footer, anchor="mm")

    # 4. Guardar la Imagen
    try:
        # Guardar en la ruta principal (Escritorio)
        img.save(OUTPUT_IMAGE_PATH, "PNG")
        print(f"🎉 ¡Flyer guardado exitosamente en el Escritorio!: {OUTPUT_IMAGE_PATH}")
        return OUTPUT_IMAGE_PATH
    except Exception as e:
        print(f"⚠️ No se pudo guardar directamente en el Escritorio: {str(e)}")
        img.save(BACKUP_IMAGE_PATH, "PNG")
        print(f"📁 Flyer guardado como respaldo en el proyecto: {BACKUP_IMAGE_PATH}")
        return BACKUP_IMAGE_PATH

def crear_boletin_grafico_cuadrado(datos_bcv, datos_noticia, datos_db):
    """
    Maqueta y dibuja la versión cuadrada premium (Versión 2) en formato 1080x1080
    con el rediseño basado en líneas divisorias, fuentes más grandes y colores actualizados.
    """
    print("🎨 Iniciando maquetación de la Versión Cuadrada Rediseñada (1080x1080) con Pillow...")
    
    width = 1080
    height = 1080
    
    # Colores del Rediseño
    COLOR_NAVY = (15, 55, 135, 255)
    COLOR_CYAN = (0, 150, 224, 255)
    COLOR_TEXT_NAVY = (30, 70, 150, 255)
    COLOR_TEXT_BLACK = (0, 0, 0, 255)
    COLOR_LINE = (0, 0, 0, 60) # Líneas sutiles
    COLOR_MUNDIAL_BG = (255, 200, 200, 255) # Rojo muy claro / Rosado
    COLOR_MUNDIAL_TEXT = (220, 20, 60, 255) # Rojo intenso
    COLOR_DIVISA_LABEL = (220, 20, 60, 255) # Rojo para etiquetas de divisas
    
    # 1. Crear lienzo base
    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 2. Rellenar fondo con degradado vertical sutil (blanco a gris azulado claro)
    start_color = (250, 252, 255)
    end_color = (238, 243, 250)
    for y in range(height):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * (y / height))
        g = int(start_color[1] + (end_color[1] - start_color[1]) * (y / height))
        b = int(start_color[2] + (end_color[2] - start_color[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        
    # 3. Dibuja Ondas Corporativas Azules en el Encabezado
    def calcular_bezier(p0, p1, p2, p3, steps=40):
        points = []
        for i in range(steps + 1):
            t = i / steps
            x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
            points.append((x, y))
        return points

    scale = 4
    header_w = width * scale
    header_h = 300 * scale
    header_temp = Image.new("RGBA", (header_w, header_h), (0, 0, 0, 0))
    header_draw = ImageDraw.Draw(header_temp)

    p0_c = (0 * scale, 180 * scale)
    p1_c = (350 * scale, 50 * scale)
    p2_c = (730 * scale, 270 * scale)
    p3_c = (1080 * scale, 140 * scale)
    puntos_cyan = calcular_bezier(p0_c, p1_c, p2_c, p3_c)
    puntos_cyan = [(0, 0)] + puntos_cyan + [(header_w, 0)]
    header_draw.polygon(puntos_cyan, fill=COLOR_CYAN)
    
    p0_n = (0 * scale, 130 * scale)
    p1_n = (350 * scale, 250 * scale)
    p2_n = (730 * scale, 70 * scale)
    p3_n = (1080 * scale, 190 * scale)
    puntos_navy = calcular_bezier(p0_n, p1_n, p2_n, p3_n)
    puntos_navy = [(0, 0)] + puntos_navy + [(header_w, 0)]
    header_draw.polygon(puntos_navy, fill=COLOR_NAVY)

    header_smooth = header_temp.resize((width, 300), Image.Resampling.LANCZOS)
    img.paste(header_smooth, (0, 0), header_smooth)

    # 4. Cargar Fuentes (Arial optimizada)
    font_header_title = cargar_fuente(FONT_TITLE, 42)
    font_header_date = cargar_fuente(FONT_BOLD, 22)
    font_card_title = cargar_fuente(FONT_BOLD, 26) # Más grande
    font_text = cargar_fuente(FONT_REGULAR, 24)     # Más grande
    font_results = cargar_fuente(FONT_BOLD, 26)     # Fuente para resultados: Rojo, Negrita, 26px
    font_days = cargar_fuente(FONT_TITLE, 54)
    font_footer = cargar_fuente(FONT_REGULAR, 14)
    font_rate_val = cargar_fuente(FONT_BOLD, 26)
    font_sub_bold = cargar_fuente(FONT_BOLD, 22)
    font_buenos_dias_cuadrado = cargar_fuente(FONT_BOLD, 60)

    # 5. Dibujar Textos del Encabezado
    draw.text((60, 50), "HIGHLIGHTS DIARIO", fill=(255, 255, 255, 255), font=font_header_title)
    
    ahora = datetime.now()
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses_ano = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha_formateada = f"{dias_semana[ahora.weekday()]}, {ahora.day} de {meses_ano[ahora.month - 1]} de {ahora.year}"
    hora_formateada = ahora.strftime("%I:%M %p")
    
    # Fecha en su propia línea
    draw.text((60, 95), f"📅  {fecha_formateada}", fill=(255, 255, 255, 255), font=font_header_date)
    # Hora en línea separada debajo para evitar solapamiento con el icono del sol
    font_header_hora = cargar_fuente(FONT_BOLD, 20)
    draw.text((60, 128), f"🕒  {hora_formateada}", fill=(255, 255, 255, 210), font=font_header_hora)

    # 6. Saludo "¡Buenos Días!" con Sol
    sun_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sun_icon.png")
    sun_size = 130
    sun_icon = None
    if os.path.exists(sun_path):
        try:
            sun_img = Image.open(sun_path).convert("RGBA")
            datas = sun_img.getdata()
            newData = []
            for item in datas:
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)
            sun_img.putdata(newData)
            sun_icon = sun_img.resize((sun_size, sun_size), Image.Resampling.LANCZOS)
        except Exception:
            pass

    saludo_texto = "¡Buenos Días!"
    text_bbox = font_buenos_dias_cuadrado.getbbox(saludo_texto)
    text_width = text_bbox[2] - text_bbox[0]
    spacing = 20
    
    right_margin = 60
    if sun_icon:
        total_width = sun_size + spacing + text_width
        start_x = width - right_margin - total_width
        sun_y = 90 - sun_size // 2
        img.paste(sun_icon, (start_x, sun_y), sun_icon)
        text_x = start_x + sun_size + spacing
        draw.text((text_x, 90), saludo_texto, fill=(255, 255, 255, 255), font=font_buenos_dias_cuadrado, anchor="lm")
    else:
        text_x = width - right_margin - text_width
        draw.text((text_x, 90), saludo_texto, fill=(255, 255, 255, 255), font=font_buenos_dias_cuadrado, anchor="lm")

    # 7. Definición de la Rejilla de Contenido
    x_mid = width // 2
    y_row1_end = 504
    y_row2_end = 770
    x_margin = 60
    content_width = (width // 2) - x_margin - 20

    # Dibujar Líneas Divisorias
    # Línea Vertical Central
    draw.line([(x_mid, 210), (x_mid, 1040)], fill=COLOR_LINE, width=2)
    # Línea Horizontal 1
    draw.line([(x_margin, y_row1_end), (width - x_margin, y_row1_end)], fill=COLOR_LINE, width=2)
    # Línea Horizontal 2
    draw.line([(x_margin, y_row2_end), (width - x_margin, y_row2_end)], fill=COLOR_LINE, width=2)

    # --- FILA 1, COL IZQ: PENSAMIENTO UNIVERSAL ---
    draw.text((x_margin, 220), "PENSAMIENTO UNIVERSAL", fill=COLOR_TEXT_NAVY, font=font_card_title)
    pensamiento = datos_db["pensamiento"]
    texto_p = f"\"{pensamiento['texto']}\" — {pensamiento['autor']}."
    wrapped_p = wrap_text(texto_p, font_text, content_width)
    line_y = 260
    for line in wrapped_p[:7]:
        draw.text((x_margin, line_y), line, fill=COLOR_TEXT_BLACK, font=font_text)
        line_y += 32

    # --- FILA 1, COL DER: EFEMÉRIDES UNIVERSAL ---
    x_right = x_mid + 20
    draw.text((x_right, 220), "EFEMÉRIDES UNIVERSAL", fill=COLOR_TEXT_NAVY, font=font_card_title)
    efemeride_u = datos_db["efemeride_universal"]
    wrapped_eu = wrap_text(efemeride_u, font_text, content_width)
    line_y = 260
    for line in wrapped_eu[:7]:
        draw.text((x_right, line_y), line, fill=COLOR_TEXT_BLACK, font=font_text)
        line_y += 32

    # --- FILA 2, COL IZQ: NOTICIA DESTACADA ---
    draw.text((x_margin, y_row1_end + 20), "NOTICIA DESTACADA", fill=COLOR_TEXT_NAVY, font=font_card_title)
    noticia_titulo = datos_noticia["titulo"]
    wrapped_n = wrap_text(noticia_titulo, font_text, content_width)
    line_y = y_row1_end + 60
    for line in wrapped_n[:6]:
        draw.text((x_margin, line_y), line, fill=COLOR_TEXT_BLACK, font=font_text)
        line_y += 32

    # --- FILA 2, COL DER: EFEMÉRIDES VENEZUELA ---
    draw.text((x_right, y_row1_end + 20), "EFEMÉRIDES VENEZUELA", fill=COLOR_TEXT_NAVY, font=font_card_title)
    efemeride_v = datos_db["efemeride_venezuela"]
    wrapped_ev = wrap_text(efemeride_v, font_text, content_width)
    line_y = y_row1_end + 60
    for line in wrapped_ev[:6]:
        draw.text((x_right, line_y), line, fill=COLOR_TEXT_BLACK, font=font_text)
        line_y += 32

    # --- FILA 3, COL IZQ: RESULTADOS DEL MUNDIAL ---
    # Centro de la columna izquierda (entre x_margin y x_mid)
    x_left_center = (x_margin + x_mid) // 2
    # Título
    draw.text((x_left_center, y_row2_end + 20), "RESULTADOS DEL MUNDIAL", fill=COLOR_TEXT_NAVY, font=font_card_title, anchor="mt")
    
    # Obtener resultados desde datos_db
    resultados = datos_db.get("resultados_mundial", [])
    
    if resultados:
        # Dibujar los primeros 5 resultados para evitar desbordamiento
        # Alineamos el primer resultado con los VALORES de las divisas (y_row2_end + 100)
        line_y = y_row2_end + 100
        for res in resultados[:5]:
            # Texto en Rojo, Negrita y 26px para máximo impacto y congruencia
            draw.text((x_left_center, line_y), res, fill=COLOR_MUNDIAL_TEXT, font=font_results, anchor="mm")
            line_y += 32
    else:
        # Mensaje si no hay partidos
        draw.text((x_left_center, y_row2_end + 110), "No hay partidos hoy", fill=COLOR_TEXT_NAVY, font=font_sub_bold, anchor="mm")

    # --- FILA 3, COL DER: INDICADORES DE DIVISAS (3 columnas horizontales) ---
    draw.text((x_right, y_row2_end + 20), "INDICADORES DE DIVISAS (BCV)", fill=COLOR_TEXT_NAVY, font=font_card_title)

    divisas = [
        {"label": "DÓLAR",      "val": datos_bcv.get('usd', 'N/D'), "unit": "Bs. / USD"},
        {"label": "EURO",       "val": datos_bcv.get('eur', 'N/D'), "unit": "Bs. / EUR"},
        {"label": "BINANCE (₿)","val": datos_bcv.get('binance', 'N/D'), "unit": "Bs. / USDT"},
    ]

    # Sección derecha: desde x_right hasta width-x_margin = 460px → 3 cols de ~153px c/u
    right_sec_w = (width - x_margin) - x_right   # 460 px
    col_w_div   = right_sec_w // 3               # ~153 px
    div_y_lbl   = y_row2_end + 68   # y etiqueta roja
    div_y_val   = y_row2_end + 100  # y valor grande
    div_y_unit  = y_row2_end + 136  # y unidad gris pequeña

    for i, div in enumerate(divisas):
        col_x = x_right + i * col_w_div
        # Etiqueta en Rojo (bold)
        draw.text((col_x, div_y_lbl),  div["label"], fill=COLOR_DIVISA_LABEL, font=font_sub_bold)
        # Valor en Negro (grande y bold)
        draw.text((col_x, div_y_val),  div["val"],   fill=COLOR_TEXT_BLACK,   font=font_rate_val)
        # Unidad en Gris (pequeño)
        draw.text((col_x, div_y_unit), div["unit"],  fill=(100, 100, 100, 255), font=font_footer)

    # Fuente y fecha centradas en la sección derecha (mismo azul que los títulos)
    right_center_x = x_right + right_sec_w // 2
    draw.text((right_center_x, y_row2_end + 195), "Fuente: Banco Central de Venezuela (BCV) · Binance P2P", fill=COLOR_TEXT_NAVY, font=font_footer, anchor="mm")
    draw.text((right_center_x, y_row2_end + 215), f"Fecha Valor: {datos_bcv['fecha']}", fill=COLOR_TEXT_NAVY, font=font_footer, anchor="mm")

    # 8. Pie de Página (bajado 3 espacios ~30px)
    draw.text((width // 2, height - 10), "Generado Automáticamente | © Ing. LF", fill=(50, 50, 50, 255), font=font_footer, anchor="mm")

    # 9. Guardar la Imagen Cuadrada
    from config import ESCRITORIO, BASE_DIR
    output_name_sq = "boletin_highlights_cuadrado.png"
    output_path_sq = os.path.join(ESCRITORIO, output_name_sq)
    backup_path_sq = os.path.join(BASE_DIR, output_name_sq)
    
    # Siempre guardar copia de respaldo en el proyecto
    img.save(backup_path_sq, "PNG")
    print(f"📁 Copia de respaldo cuadrada guardada en el proyecto: {backup_path_sq}")
    
    try:
        img.save(output_path_sq, "PNG")
        print(f"🎉 ¡Folleto Cuadrado guardado exitosamente en el Escritorio!: {output_path_sq}")
        return output_path_sq
    except Exception as e:
        print(f"⚠️ No se pudo guardar la copia cuadrada en el Escritorio: {str(e)}")
        return backup_path_sq

if __name__ == "__main__":
    # Test rápido de generación
    test_bcv = {"usd": "520,91", "eur": "604,16", "fecha": "Miércoles, 20 Mayo 2026"}
    test_noticia = {"titulo": "Asociaciones de Jubilados del Zulia analizan el impacto de los nuevos ajustes de indexación de bonos en el sector público nacional.", "link": "https://www.bancaynegocios.com/"}
    test_db = {
        "pensamiento": {"texto": "El secreto del cambio es enfocar toda tu energía no en luchar contra lo viejo, sino en construir lo nuevo.", "autor": "Sócrates"},
        "efemeride_universal": "Hoy conmemoramos el Día Mundial de la Medicina Familiar, reconociendo el pilar fundamental de la salud pública.",
        "efemeride_venezuela": "Hoy conmemoramos el Día Mundial de la Medicina Familiar en Venezuela, reconociendo el pilar fundamental de la salud pública."
    }
    crear_boletin_grafico_cuadrado(test_bcv, test_noticia, test_db)

