import os
import sys
import io

# Reconfigurar salida estándar para UTF-8 en consolas Windows
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════════════
# COLORES EDITORIALES
# ══════════════════════════════════════════════════════════════════════════════
NAVY_DEEP        = (6,   24,  58,  255)   # Azul marino oscuro
NAVY_HEADER_TOP  = (8,   32,  75,  255)   # Azul cabecera superior
NAVY_HEADER_BOT  = (4,   18,  46,  255)   # Azul cabecera inferior
NAVY_CARD_TAB    = (8,   28,  66,  255)   # Pestañas de categoría
NAVY_TEXT        = (8,   28,  66,  255)   # Azul cifras y títulos
GOLD_ACCENT      = (212, 175, 55,  255)   # Dorado institucional
GOLD_LIGHT       = (234, 198, 95,  255)   # Dorado claro brillante
GOLD_BORDER      = (225, 185, 75,  255)   # Líneas doradas
WHITE            = (255, 255, 255, 255)   # Blanco puro
BG_PAGE          = (255, 255, 255, 255)   # Fondo blanco del periódico
BG_CARD          = (255, 255, 255, 255)   # Fondo de tarjetas
BORDER_CARD      = (203, 213, 225, 255)   # Borde suave Slate 300
BORDER_LIGHT     = (226, 232, 240, 255)   # Borde tenue Slate 200
TEXT_TITLE       = (15,  23,  42,  255)   # Slate 900 titulares
TEXT_BODY        = (0,   0,   0,   255)   # Negro nítido para lectura clara de resúmenes
TEXT_MUTED       = (100, 116, 139, 255)   # Slate 500 auxiliares
WARM_BG_START    = (255, 253, 247, 255)   # Crema cálido Frase/Efeméride
WARM_BG_END      = (254, 247, 234, 255)   # Crema suave dorado

# Fuentes de Windows
FONT_DIR = r"C:\Windows\Fonts"

def cargar_fuente(nombre, tamano):
    """Carga fuente TrueType con fallbacks de Windows garantizados."""
    rutas = [
        os.path.join(FONT_DIR, nombre),
        os.path.join(BASE_DIR, "fonts", nombre),
        os.path.join(FONT_DIR, "arial.ttf")
    ]
    for r in rutas:
        if os.path.exists(r):
            try:
                return ImageFont.truetype(r, tamano)
            except Exception:
                pass
    return ImageFont.load_default()

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

def pegar_imagen_redondeada(canvas, img_path, box, radio=6):
    """Ajusta y recorta una imagen con esquinas redondeadas y la pega en el lienzo."""
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    if not os.path.exists(img_path):
        return
    try:
        im = Image.open(img_path).convert("RGBA")
        # Mantener proporción cubriendo el área (cover)
        im_ratio = im.width / im.height
        target_ratio = w / h
        if im_ratio > target_ratio:
            new_h = h
            new_w = int(h * im_ratio)
        else:
            new_w = w
            new_h = int(w / im_ratio)
        im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # Recortar al centro
        crop_x = (new_w - w) // 2
        crop_y = (new_h - h) // 2
        im = im.crop((crop_x, crop_y, crop_x + w, crop_y + h))
        
        # Máscara redondeada
        mask = Image.new("L", (w, h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, w, h], radius=radio, fill=255)
        
        canvas.paste(im, (x1, y1), mask)
    except Exception as e:
        print(f"Error pegando imagen {img_path}: {e}")

def dibujar_pestana_editorial(draw, x, y, ancho, alto, texto, font, corte=16):
    """Dibuja pestaña azul marino con corte sesgado y filete dorado."""
    puntos = [(x, y), (x + ancho, y), (x + ancho - corte, y + alto), (x, y + alto)]
    draw.polygon(puntos, fill=NAVY_CARD_TAB)
    draw.line([(x + ancho, y), (x + ancho - corte, y + alto)], fill=GOLD_ACCENT, width=3)
    draw.text((x + 10, y + alto // 2), texto, fill=WHITE, font=font, anchor="lm")

def crear_portada_editorial(datos_bcv, noticias_5, pensamiento, efemeride, output_path):
    """Genera la portada editorial 'NOTICIAS DEL DÍA' exactamente en 1080x1080 px."""
    W, H = 1080, 1080
    canvas = Image.new("RGBA", (W, H), BG_PAGE)
    draw = ImageDraw.Draw(canvas)
    
    # ── FUENTES EDITORIALES ──
    f_header_title = cargar_fuente("georgiab.ttf", 52)      # Título principal Serif
    f_header_sub   = cargar_fuente("georgiai.ttf", 22)      # Subtítulo cursiva
    f_date_day     = cargar_fuente("segoeui.ttf", 15)       # Día semana
    f_date_num     = cargar_fuente("segoeuib.ttf", 46)      # Número grande
    f_date_month   = cargar_fuente("segoeuib.ttf", 15)      # Mes
    f_date_year    = cargar_fuente("segoeuib.ttf", 13)      # Año
    
    f_tab          = cargar_fuente("segoeuib.ttf", 14)      # Pestañas de categoría
    f_tab_lg       = cargar_fuente("segoeuib.ttf", 15)      # Pestañas grandes
    f_cot_tag      = cargar_fuente("segoeuib.ttf", 15)      # "COTIZACIONES DEL DÍA"
    
    f_rate_title   = cargar_fuente("segoeuib.ttf", 14)      # "DÓLAR BCV"
    f_rate_val     = cargar_fuente("segoeuib.ttf", 25)      # "888,89 Bs"
    
    # Fila 1 Noticias
    f_news_t1      = cargar_fuente("georgiab.ttf", 18)      # Titular fila 1
    f_news_r1      = cargar_fuente("segoeuiz.ttf", 13)      # Resumen fila 1 en negrita itálica
    
    # Fila 2 Noticias
    f_news_t2      = cargar_fuente("georgiab.ttf", 15)      # Titular fila 2
    f_news_r2      = cargar_fuente("segoeuiz.ttf", 12)      # Resumen fila 2 en negrita itálica
    
    # Frase & Efemérides
    f_frase_text   = cargar_fuente("georgiaz.ttf", 22)      # Frase negrita cursiva
    f_frase_author = cargar_fuente("segoeuib.ttf", 14)      # Autor
    f_efem_date    = cargar_fuente("georgiab.ttf", 19)      # Fecha efeméride
    f_efem_body    = cargar_fuente("segoeui.ttf", 14)       # Explicación efeméride
    
    f_footer       = cargar_fuente("segoeuib.ttf", 13)      # Pie editorial
    
    # ══════════════════════════════════════════════════════════════════════════
    # 1. CABECERA (Y: 0 a 145)
    # ══════════════════════════════════════════════════════════════════════════
    HH = 145
    header_grad = crear_degradado_vertical(W, HH, NAVY_HEADER_TOP, NAVY_HEADER_BOT)
    canvas.paste(header_grad, (0, 0))
    # Filetes dorados arriba y abajo
    draw.line([(0, 1), (W, 1)], fill=GOLD_BORDER, width=2)
    draw.line([(0, HH - 2), (W, HH - 2)], fill=GOLD_BORDER, width=3)
    
    # Globo terráqueo a la izquierda
    globe_path = os.path.join(BASE_DIR, "assets", "general", "globe.png")
    if os.path.exists(globe_path):
        globe_im = Image.open(globe_path).convert("RGBA")
        # Redimensionar manteniendo proporción a aprox 145x120
        globe_im = globe_im.resize((150, 125), Image.Resampling.LANCZOS)
        canvas.paste(globe_im, (12, 10), globe_im if globe_im.mode == "RGBA" else None)
    
    # Título y Subtítulo centrados entre X=170 y X=910
    cx_header = (170 + 910) // 2
    draw.text((cx_header, 48), "NOTICIAS DEL DÍA", fill=WHITE, font=f_header_title, anchor="mm")
    draw.text((cx_header, 104), "La actualidad en una sola mirada", fill=(241, 245, 249, 255), font=f_header_sub, anchor="mm")
    
    # Tarjeta de Fecha a la derecha (X: 915 a 1055, Y: 12 a 132)
    bx1, by1, bx2, by2 = 915, 12, 1055, 132
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=12, fill=WHITE)
    
    ahora = datetime.now()
    dias_s = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses_s = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    dia_nombre = dias_s[ahora.weekday()]
    dia_num    = str(ahora.day)
    mes_nombre = meses_s[ahora.month - 1]
    ano_str    = str(ahora.year)
    
    cx_badge = (bx1 + bx2) // 2
    draw.text((cx_badge, by1 + 18), dia_nombre, fill=(51, 65, 85, 255), font=f_date_day, anchor="mm")
    draw.text((cx_badge, by1 + 54), dia_num, fill=NAVY_DEEP, font=f_date_num, anchor="mm")
    draw.text((cx_badge, by1 + 90), mes_nombre, fill=(15, 23, 42, 255), font=f_date_month, anchor="mm")
    draw.text((cx_badge, by1 + 109), ano_str, fill=(71, 85, 105, 255), font=f_date_year, anchor="mm")
    
    # ══════════════════════════════════════════════════════════════════════════
    # 2. FRANJA DE COTIZACIONES (Y: 154 a 232)
    # ══════════════════════════════════════════════════════════════════════════
    y_cot = 154
    h_cot = 78
    draw.rectangle([0, y_cot, W, y_cot + h_cot], fill=WHITE, outline=BORDER_LIGHT, width=1)
    
    # Pestaña "COTIZACIONES DEL DÍA"
    w_tab_cot = 205
    corte_cot = 22
    puntos_cot = [(10, y_cot + 6), (10 + w_tab_cot, y_cot + 6), (10 + w_tab_cot - corte_cot, y_cot + h_cot - 6), (10, y_cot + h_cot - 6)]
    draw.polygon(puntos_cot, fill=NAVY_CARD_TAB)
    draw.line([(10 + w_tab_cot, y_cot + 6), (10 + w_tab_cot - corte_cot, y_cot + h_cot - 6)], fill=GOLD_ACCENT, width=4)
    draw.text((22, y_cot + 24), "COTIZACIONES", fill=WHITE, font=f_cot_tag, anchor="lm")
    draw.text((22, y_cot + 48), "DEL DÍA", fill=WHITE, font=f_cot_tag, anchor="lm")
    
    # 3 Indicadores de divisas
    # Dólar BCV
    usd_val = datos_bcv.get("usd", "No disp.") + " Bs"
    eur_val = datos_bcv.get("eur", "No disp.") + " Bs"
    bin_val = datos_bcv.get("binance", "No disp.") + " Bs"
    
    icon_usd = os.path.join(BASE_DIR, "assets", "icons", "usd.png")
    icon_eur = os.path.join(BASE_DIR, "assets", "icons", "eur.png")
    icon_bin = os.path.join(BASE_DIR, "assets", "icons", "binance.png")
    
    # Coordenadas de los 3 bloques
    div_blocks = [
        {"x": 235, "icon": icon_usd, "title": "DÓLAR BCV",   "val": usd_val},
        {"x": 510, "icon": icon_eur, "title": "EURO BCV",    "val": eur_val},
        {"x": 775, "icon": icon_bin, "title": "BINANCE P2P", "val": bin_val}
    ]
    
    for blk in div_blocks:
        x_start = blk["x"]
        if os.path.exists(blk["icon"]):
            ico = Image.open(blk["icon"]).convert("RGBA")
            ico = ico.resize((44, 44), Image.Resampling.LANCZOS)
            canvas.paste(ico, (x_start, y_cot + 16), ico)
        
        # Textos
        tx = x_start + 54
        draw.text((tx, y_cot + 25), blk["title"], fill=(15, 23, 42, 255), font=f_rate_title, anchor="lm")
        draw.text((tx, y_cot + 52), blk["val"],   fill=NAVY_DEEP, font=f_rate_val, anchor="lm")
    
    # ══════════════════════════════════════════════════════════════════════════
    # 3. SECCIÓN DE NOTICIAS (5 noticias en 2 filas)
    # ══════════════════════════════════════════════════════════════════════════
    # Fila 1: 2 noticias (Y: 244 a 484, Alto: 240)
    y_r1 = 244
    h_r1 = 240
    w_r1 = 522
    
    # Noticia 1 (Izquierda)
    n1 = noticias_5[0] if len(noticias_5) > 0 else {}
    n2 = noticias_5[1] if len(noticias_5) > 1 else {}
    n3 = noticias_5[2] if len(noticias_5) > 2 else {}
    n4 = noticias_5[3] if len(noticias_5) > 3 else {}
    n5 = noticias_5[4] if len(noticias_5) > 4 else {}
    
    # Recuadro N1
    draw.rounded_rectangle([12, y_r1, 12 + w_r1, y_r1 + h_r1], radius=8, fill=WHITE, outline=BORDER_CARD, width=1)
    dibujar_pestana_editorial(draw, 12, y_r1, 155, 30, n1.get("categoria", "VENEZUELA"), f_tab)
    # Imagen N1
    pegar_imagen_redondeada(canvas, n1.get("imagen_local", os.path.join(BASE_DIR, "assets", "categories", "venezuela.jpg")),
                            [22, y_r1 + 38, 218, y_r1 + h_r1 - 10], radio=6)
    # Textos N1
    t1_lines = wrap_text(n1.get("titular", "Gobierno impulsa nuevas estrategias económicas"), f_news_t1, 290)
    ty = y_r1 + 44
    for line in t1_lines[:3]:
        draw.text((230, ty), line, fill=TEXT_TITLE, font=f_news_t1, anchor="lt")
        ty += 23
    r1_lines = wrap_text(n1.get("resumen", "El Ejecutivo nacional reafirmó su compromiso con el bienestar del pueblo venezolano."), f_news_r1, 290)
    ty += 6
    for line in r1_lines[:3]:
        draw.text((230, ty), line, fill=TEXT_BODY, font=f_news_r1, anchor="lt")
        ty += 18
        
    # Recuadro N2 (Derecha)
    x2_start = 12 + w_r1 + 12
    draw.rounded_rectangle([x2_start, y_r1, x2_start + w_r1, y_r1 + h_r1], radius=8, fill=WHITE, outline=BORDER_CARD, width=1)
    dibujar_pestana_editorial(draw, x2_start, y_r1, 155, 30, n2.get("categoria", "ECONOMÍA"), f_tab)
    # Imagen N2
    pegar_imagen_redondeada(canvas, n2.get("imagen_local", os.path.join(BASE_DIR, "assets", "categories", "economia.jpg")),
                            [x2_start + 10, y_r1 + 38, x2_start + 206, y_r1 + h_r1 - 10], radio=6)
    # Textos N2
    t2_lines = wrap_text(n2.get("titular", "Economía muestra signos de recuperación"), f_news_t1, 290)
    ty = y_r1 + 44
    for line in t2_lines[:3]:
        draw.text((x2_start + 218, ty), line, fill=TEXT_TITLE, font=f_news_t1, anchor="lt")
        ty += 23
    r2_lines = wrap_text(n2.get("resumen", "Analistas destacan el repunte en sectores clave durante el tercer trimestre."), f_news_r1, 290)
    ty += 6
    for line in r2_lines[:3]:
        draw.text((x2_start + 218, ty), line, fill=TEXT_BODY, font=f_news_r1, anchor="lt")
        ty += 18

    # Fila 2: 3 noticias (Y: 494 a 745, Alto: 251)
    y_r2 = 494
    h_r2 = 251
    w_r2 = 344
    gap_r2 = 12
    
    noticias_fila2 = [
        (n3, "INTERNACIONALES", os.path.join(BASE_DIR, "assets", "categories", "internacionales.jpg")),
        (n4, "MARACAIBO",       os.path.join(BASE_DIR, "assets", "categories", "maracaibo.jpg")),
        (n5, "SALUD",            os.path.join(BASE_DIR, "assets", "categories", "salud.jpg"))
    ]
    
    for idx, (noticia_item, cat_default, img_default) in enumerate(noticias_fila2):
        nx = 12 + idx * (w_r2 + gap_r2)
        draw.rounded_rectangle([nx, y_r2, nx + w_r2, y_r2 + h_r2], radius=8, fill=WHITE, outline=BORDER_CARD, width=1)
        cat_nombre = noticia_item.get("categoria", cat_default)
        dibujar_pestana_editorial(draw, nx, y_r2, 148, 28, cat_nombre, f_tab)
        
        # Imagen
        img_use = noticia_item.get("imagen_local") or img_default
        pegar_imagen_redondeada(canvas, img_use, [nx + 8, y_r2 + 36, nx + 128, y_r2 + h_r2 - 8], radio=6)
        
        # Textos
        tx_pos = nx + 136
        tw_max = w_r2 - 144
        
        t_lines = wrap_text(noticia_item.get("titular", "Noticia de actualidad nacional"), f_news_t2, tw_max)
        ty = y_r2 + 40
        for line in t_lines[:3]:
            draw.text((tx_pos, ty), line, fill=TEXT_TITLE, font=f_news_t2, anchor="lt")
            ty += 20
        r_lines = wrap_text(noticia_item.get("resumen", "Información detallada sobre los acontecimientos más recientes."), f_news_r2, tw_max)
        ty += 6
        for line in r_lines[:3]:
            draw.text((tx_pos, ty), line, fill=TEXT_BODY, font=f_news_r2, anchor="lt")
            ty += 16
            
    # ══════════════════════════════════════════════════════════════════════════
    # 4. SECCIÓN INFERIOR: FRASE Y EFEMÉRIDES (Y: 757 a 1025)
    # ══════════════════════════════════════════════════════════════════════════
    y_bot = 757
    h_bot = 268
    w_bot = 522
    
    # Bloque Izquierdo: LA FRASE UNIVERSAL (X: 12 a 534)
    grad_frase = crear_degradado_vertical(w_bot, h_bot, WARM_BG_START, WARM_BG_END)
    canvas.paste(grad_frase, (12, y_bot))
    draw.rounded_rectangle([12, y_bot, 12 + w_bot, y_bot + h_bot], radius=8, outline=BORDER_CARD, width=1)
    dibujar_pestana_editorial(draw, 12, y_bot, 220, 32, "LA FRASE UNIVERSAL", f_tab_lg)
    
    # Imagen del viajero
    img_viajero = os.path.join(BASE_DIR, "assets", "general", "frase_viajero.jpg")
    pegar_imagen_redondeada(canvas, img_viajero, [24, y_bot + 42, 175, y_bot + h_bot - 12], radio=6)
    
    # Texto Frase entrecomillada
    f_texto = pensamiento.get("texto", "La vida es un viaje, no un destino")
    f_autor = pensamiento.get("autor", "Anónimo")
    frase_formateada = f'“{f_texto}”'
    frase_lines = wrap_text(frase_formateada, f_frase_text, 310)
    
    # Centrar verticalmente en el espacio disponible
    total_text_h = len(frase_lines[:4]) * 28 + 24
    start_ty = y_bot + 42 + (h_bot - 54 - total_text_h) // 2
    ty = start_ty
    for line in frase_lines[:4]:
        draw.text((188, ty), line, fill=TEXT_TITLE, font=f_frase_text, anchor="lt")
        ty += 28
    if f_autor and f_autor.lower() != "anónimo":
        draw.text((188, ty + 6), f"— {f_autor}", fill=NAVY_DEEP, font=f_frase_author, anchor="lt")
        
    # Bloque Derecho: EFEMÉRIDES DE VENEZUELA (X: 546 a 1068)
    x_efem = 12 + w_bot + 12
    grad_efem = crear_degradado_vertical(w_bot, h_bot, WARM_BG_START, WARM_BG_END)
    canvas.paste(grad_efem, (x_efem, y_bot))
    draw.rounded_rectangle([x_efem, y_bot, x_efem + w_bot, y_bot + h_bot], radius=8, outline=BORDER_CARD, width=1)
    dibujar_pestana_editorial(draw, x_efem, y_bot, 240, 32, "EFEMÉRIDES DE VENEZUELA", f_tab_lg)
    
    # Formateo inteligente de la efeméride
    efem_texto_raw = efemeride if isinstance(efemeride, str) else efemeride.get("texto", "")
    
    # Extraer año si existe (ej. "(1821)" o "1821")
    match_ano = re.search(r'\((\d{4})\)', efem_texto_raw)
    ano_efem = match_ano.group(1) if match_ano else str(ahora.year)
    
    # Limpiar año entre paréntesis de la explicación
    explicacion = re.sub(r'\(\d{4}\)', '', efem_texto_raw)
    if "|" in explicacion:
        partes = explicacion.split("|", 1)
        explicacion = partes[0].strip() + ". " + partes[1].strip()
    explicacion = re.sub(r'\s+', ' ', explicacion).strip()

    # Selección de imagen: Bolívar si lo menciona, de lo contrario Escudo Nacional de Venezuela
    efem_lower = explicacion.lower()
    box_efem = [x_efem + 12, y_bot + 42, x_efem + 155, y_bot + h_bot - 12]
    w_box_e = box_efem[2] - box_efem[0]
    h_box_e = box_efem[3] - box_efem[1]

    if any(k in efem_lower for k in ["bolívar", "bolivar", "libertador"]):
        img_efem = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
        pegar_imagen_redondeada(canvas, img_efem, box_efem, radio=6)
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
                img_efem = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
                pegar_imagen_redondeada(canvas, img_efem, box_efem, radio=6)
        else:
            img_efem = os.path.join(BASE_DIR, "assets", "general", "efemeride_bolivar.jpg")
            pegar_imagen_redondeada(canvas, img_efem, box_efem, radio=6)
    
    # Titular de fecha
    fecha_efem_header = f"{dia_num} de {mes_nombre.lower()} de {ano_efem}"
    
    tx_efem = x_efem + 168
    tw_efem = w_bot - 180
    
    draw.text((tx_efem, y_bot + 46), fecha_efem_header, fill=TEXT_TITLE, font=f_efem_date, anchor="lt")
    
    efem_lines = wrap_text(explicacion, f_efem_body, tw_efem)
    ty = y_bot + 78
    for line in efem_lines[:4]:
        draw.text((tx_efem, ty), line, fill=TEXT_BODY, font=f_efem_body, anchor="lt")
        ty += 22
        
    # ══════════════════════════════════════════════════════════════════════════
    # 5. PIE EDITORIAL (Y: 1038 a 1080)
    # ══════════════════════════════════════════════════════════════════════════
    y_foot = 1038
    h_foot = 42
    draw.rectangle([0, y_foot, W, H], fill=NAVY_DEEP)
    draw.line([(0, y_foot), (W, y_foot)], fill=GOLD_BORDER, width=2)
    
    # Líneas doradas y texto central
    foot_text = "Fuentes: Medios Nacionales | Generado Automáticamente · © Ing. LF"
    bbox_ft = f_footer.getbbox(foot_text)
    ft_w = bbox_ft[2] - bbox_ft[0]
    
    cx_ft = W // 2
    lx1 = 80
    lx2 = cx_ft - (ft_w // 2) - 20
    rx1 = cx_ft + (ft_w // 2) + 20
    rx2 = W - 80
    
    draw.line([(lx1, y_foot + h_foot // 2), (lx2, y_foot + h_foot // 2)], fill=GOLD_BORDER, width=2)
    draw.line([(rx1, y_foot + h_foot // 2), (rx2, y_foot + h_foot // 2)], fill=GOLD_BORDER, width=2)
    draw.text((cx_ft, y_foot + h_foot // 2), foot_text, fill=(241, 245, 249, 255), font=f_footer, anchor="mm")
    
    # ══════════════════════════════════════════════════════════════════════════
    # GUARDAR IMAGEN FINAL
    # ══════════════════════════════════════════════════════════════════════════
    canvas.save(output_path, "PNG", optimize=True)
    print(f"✅ Portada editorial 'NOTICIAS DEL DÍA' guardada exitosamente en:\n   {output_path}")
    return output_path

if __name__ == "__main__":
    datos_bcv = {"usd": "888,89", "eur": "989,39", "binance": "1.008,20"}
    noticias = [
        {
            "categoria": "VENEZUELA",
            "titular": "Gobierno impulsa nuevas estrategias económicas",
            "resumen": "El Ejecutivo nacional reafirmó su compromiso con el bienestar del pueblo venezolano.",
            "imagen_local": os.path.join(BASE_DIR, "assets", "categories", "venezuela.jpg")
        },
        {
            "categoria": "ECONOMÍA",
            "titular": "Economía muestra signos de recuperación",
            "resumen": "Analistas destacan el repunte en sectores clave durante el tercer trimestre.",
            "imagen_local": os.path.join(BASE_DIR, "assets", "categories", "economia.jpg")
        },
        {
            "categoria": "INTERNACIONALES",
            "titular": "ONU pide mayor diálogo para la paz",
            "resumen": "El organismo llamó a reducir las tensiones globales.",
            "imagen_local": os.path.join(BASE_DIR, "assets", "categories", "internacionales.jpg")
        },
        {
            "categoria": "MARACAIBO",
            "titular": "Maracaibo avanza con obras clave",
            "resumen": "Autoridades destacan proyectos para mejorar la ciudad.",
            "imagen_local": os.path.join(BASE_DIR, "assets", "categories", "maracaibo.jpg")
        },
        {
            "categoria": "SALUD",
            "titular": "Clave el cuidado para una vida más saludable",
            "resumen": "Especialistas recomiendan hábitos saludables y control médico periódico.",
            "imagen_local": os.path.join(BASE_DIR, "assets", "categories", "salud.jpg")
        }
    ]
    pensamiento = {
        "texto": "La vida es un viaje, no un destino",
        "autor": "Anónimo"
    }
    efemeride = "Simón Bolívar entra triunfalmente en Caracas, consolidando la independencia de Venezuela (1821)."
    
    out = os.path.join(BASE_DIR, "test_portada.png")
    crear_portada_editorial(datos_bcv, noticias, pensamiento, efemeride, out)
