import os
import json
import requests
from bs4 import BeautifulSoup
import re
import urllib3
from datetime import datetime
import config

# Deshabilitar advertencias de certificados SSL inseguros por si acaso (muy común con portales locales y VPNs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def formatear_tasa(tasa_str):
    """
    Convierte una tasa en formato string (ej: "520,91420000" o "520.9142") a un float,
    la redondea a 2 decimales y la devuelve formateada con coma decimal (ej: "520,91").
    """
    if not tasa_str or tasa_str == "No disponible":
        return tasa_str
    try:
        # Normalizar: quitar espacios, cambiar coma por punto
        clean_str = tasa_str.strip().replace(",", ".")
        # Extraer solo el número por si tiene símbolos (ej: "Bs. 520.91")
        match = re.search(r'([0-9]+(?:\.[0-9]+)?)', clean_str)
        if match:
            valor = float(match.group(1))
            # Redondear y formatear a 2 decimales con coma
            return f"{valor:.2f}".replace(".", ",")
    except Exception:
        pass
    return tasa_str

def obtener_tasas_bcv():
    """
    Realiza web scraping a la página oficial del BCV para obtener tasas de USD y EUR.
    Retorna un diccionario con las tasas y la fecha valor oficial.
    """
    url = "https://www.bcv.org.ve/"
    resultado = {"usd": "No disponible", "eur": "No disponible", "fecha": "No disponible"}
    
    print("💵 Extrayendo tasas oficiales del BCV...")
    try:
        # Petición HTTP con verificación SSL desactivada para evitar bloqueos por certificados locales
        response = requests.get(url, headers=HEADERS, verify=False, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. Buscar valor del Dólar (USD)
            dolar_el = soup.select_one("#dolar strong, #dolar .centrado")
            if dolar_el:
                resultado["usd"] = dolar_el.text.strip().replace(".", ",")
            
            # 2. Buscar valor del Euro (EUR)
            euro_el = soup.select_one("#euro strong, #euro .centrado")
            if euro_el:
                resultado["eur"] = euro_el.text.strip().replace(".", ",")
                
            # 3. Buscar Fecha Valor Oficial
            fecha_el = soup.select_one(".pull-right.dinpro.center span.date-display-single")
            if not fecha_el:
                fecha_el = soup.select_one("span.date-display-single")
            if fecha_el:
                resultado["fecha"] = fecha_el.text.strip()
                
            # Fallback por expresiones regulares si cambian el diseño HTML
            if resultado["usd"] == "No disponible" or resultado["eur"] == "No disponible":
                text = soup.text
                dolar_match = re.search(r'D[oó]lar[^0-9]*([0-9]+[,\.][0-9]+)', text, re.IGNORECASE)
                euro_match = re.search(r'Euro[^0-9]*([0-9]+[,\.][0-9]+)', text, re.IGNORECASE)
                
                if dolar_match and resultado["usd"] == "No disponible":
                    resultado["usd"] = dolar_match.group(1).replace(".", ",")
                if euro_match and resultado["eur"] == "No disponible":
                    resultado["eur"] = euro_match.group(1).replace(".", ",")
            
            # 4. Formatear y redondear tasas a 2 decimales
            resultado["usd"] = formatear_tasa(resultado["usd"])
            resultado["eur"] = formatear_tasa(resultado["eur"])
            
            print(f"✅ Scraping BCV exitoso -> USD: {resultado['usd']} | EUR: {resultado['eur']} | Fecha Valor: {resultado['fecha']}")
            
        else:
            print(f"⚠️ El servidor del BCV respondió con código de estado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error de conexión o scraping con el BCV: {str(e)}")
        # Mantiene los valores de fallback "No disponible" sin romper el flujo
        
    return resultado

def obtener_noticia_economica():
    """
    Obtiene el titular y enlace de la noticia principal económica desde el feed RSS de Banca y Negocios.
    """
    url = "https://www.bancaynegocios.com/feed/"
    resultado = {
        "titulo": "No disponible",
        "link": "#"
    }
    
    print("📰 Obteniendo noticia destacada (Banca y Negocios RSS)...")
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=20)
        
        if response.status_code == 200:
            # Parsear el RSS usando BeautifulSoup con parser XML (o html.parser en su defecto)
            soup = BeautifulSoup(response.content, 'xml')
            
            # Buscar el primer elemento de noticia <item> en el RSS
            item = soup.find('item')
            if item:
                titulo_el = item.find('title')
                link_el = item.find('link')
                
                if titulo_el:
                    # Limpiar etiquetas HTML residuales
                    resultado["titulo"] = BeautifulSoup(titulo_el.text, 'html.parser').text.strip()
                if link_el:
                    resultado["link"] = link_el.text.strip()
                    
            print(f"✅ Noticia obtenida -> Título: \"{resultado['titulo'][:45]}...\"")
        else:
            print(f"⚠️ El servidor RSS respondió con código de estado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error de conexión o lectura del feed RSS: {str(e)}")
        # Intentamos usar un plan alternativo de scraping básico al index si el feed está caído
        try:
            print("🔄 Reintentando mediante scraping básico al portal...")
            alt_res = requests.get("https://www.bancaynegocios.com/", headers=HEADERS, verify=False, timeout=10)
            if alt_res.status_code == 200:
                alt_soup = BeautifulSoup(alt_res.content, 'html.parser')
                title_el = alt_soup.select_one(".post-title a")
                if title_el:
                    resultado["titulo"] = title_el.text.strip()
                    resultado["link"] = title_el.get("href", "#")
                    print(f"✅ Noticia obtenida vía scraping de respaldo -> Título: \"{resultado['titulo'][:45]}...\"")
        except Exception as alt_err:
            print(f"❌ Scraping de respaldo también falló: {str(alt_err)}")
            
    return resultado

def obtener_tasa_binance():
    """
    Consulta la API P2P interna de Binance para obtener el precio promedio
    de USDT/VES (bolívares venezolanos) a partir de los 5 primeros anuncios
    de venta (SELL) de merchants verificados, que son los más competitivos.
    Retorna el precio formateado con 2 decimales y coma decimal (ej: "773,10").
    """
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "merchantCheck": True,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 10,
        "tradeType": "SELL"
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("₿ Consultando tasa Binance P2P (USDT/VES)...")
    try:
        response = requests.post(url, json=payload, headers=headers, verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            anuncios = data.get("data", [])
            if anuncios:
                # Tomar los primeros 5 anuncios (mejor precio) y promediar
                precios = [float(a["adv"]["price"]) for a in anuncios[:5]]
                promedio = sum(precios) / len(precios)
                resultado = f"{promedio:.2f}".replace(".", ",")
                print(f"✅ Binance P2P obtenido -> USDT/VES: {resultado} (promedio de {len(precios)} anuncios)")
                return resultado
            else:
                print("⚠️ Binance P2P: no se encontraron anuncios en la respuesta.")
        else:
            print(f"⚠️ Binance P2P respondió con código: {response.status_code}")
    except Exception as e:
        print(f"❌ Error consultando Binance P2P: {str(e)}")

    return "No disponible"

def obtener_clima():
    """
    Obtiene el estado del tiempo para hoy y mañana desde la API de Open-Meteo
    para la ubicación configurada (por defecto Caracas, Venezuela).
    Retorna una lista con diccionarios de datos del clima para hoy y mañana.
    """
    lat = getattr(config, "CLIMA_LATITUD", 10.4806)
    lon = getattr(config, "CLIMA_LONGITUD", -66.9036)
    ciudad = getattr(config, "CLIMA_CIUDAD", "Caracas")
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto"
    
    print(f"🌤️ [CLIMA] Obteniendo estado del tiempo para {ciudad} (Open-Meteo)...")
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            
            # Mapeo de códigos de clima WMO a descripciones y emojis
            wmo_codes = {
                0: ("Despejado", "☀️"),
                1: ("Parcialmente Despejado", "🌤️"),
                2: ("Parcialmente Nublado", "⛅"),
                3: ("Nublado", "☁️"),
                45: ("Neblina", "🌫️"),
                48: ("Neblina Escarchada", "🌫️"),
                51: ("Llovizna Ligera", "🌦️"),
                53: ("Llovizna Moderada", "🌦️"),
                55: ("Llovizna Densa", "🌧️"),
                56: ("Llovizna Helada Ligera", "🌧️"),
                57: ("Llovizna Helada Densa", "🌧️"),
                61: ("Lluvia Ligera", "🌧️"),
                63: ("Lluvia Moderada", "🌧️"),
                65: ("Lluvia Fuerte", "🌧️"),
                66: ("Lluvia Helada Ligera", "🌧️"),
                67: ("Lluvia Helada Fuerte", "🌧️"),
                71: ("Nieve Ligera", "❄️"),
                73: ("Nieve Moderada", "❄️"),
                75: ("Nieve Fuerte", "❄️"),
                77: ("Granizo Fino", "❄️"),
                80: ("Chubascos Ligeros", "🌦️"),
                81: ("Chubascos Moderados", "🌧️"),
                82: ("Chubascos Violentos", "⛈️"),
                85: ("Chubascos Nieve Ligeros", "❄️"),
                86: ("Chubascos Nieve Fuertes", "❄️"),
                95: ("Tormenta Eléctrica", "⛈️"),
                96: ("Tormenta con Granizo Leve", "⛈️"),
                99: ("Tormenta con Granizo Fuerte", "⛈️")
            }
            
            clima_dias = []
            # Obtener hoy y mañana (índices 0 y 1)
            for i in range(2):
                fecha_raw = daily["time"][i]
                max_temp = daily["temperature_2m_max"][i]
                min_temp = daily["temperature_2m_min"][i]
                code = daily["weather_code"][i]
                
                desc, emoji = wmo_codes.get(code, ("Desconocido", "🌡️"))
                
                fecha_obj = datetime.strptime(fecha_raw, "%Y-%m-%d")
                dias_nombre = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                dia_str = "Hoy" if i == 0 else "Mañana"
                
                clima_dias.append({
                    "dia": dia_str,
                    "nombre_dia": dias_nombre[fecha_obj.weekday()],
                    "fecha": fecha_obj.strftime("%d/%m"),
                    "temp_max": f"{max_temp:.1f}°C".replace(".", ","),
                    "temp_min": f"{min_temp:.1f}°C".replace(".", ","),
                    "descripcion": desc,
                    "emoji": emoji
                })
                
            print(f"✅ [CLIMA] Estado del tiempo obtenido con éxito para {ciudad}.")
            return clima_dias
        else:
            print(f"⚠️ [CLIMA] La API de clima respondió con código {response.status_code}")
    except Exception as e:
        print(f"❌ [CLIMA] Error al conectar o procesar el clima: {str(e)}")
        
    return []


# ── FILTROS TEMÁTICOS: ECONÓMICO Y SOCIAL (EVITAR POLÍTICA / ELECCIONES) ──────
PALABRAS_EXCLUIR_POLITICA = [
    'maduro', 'machado', 'chavismo', 'chavista', 'oposici', 'cne', 
    'eleccion', 'electoral', 'candidat', 'partido', 'asamblea nacional', 
    'inhabilitad', 'preso politico', 'presos politicos', 'represion', 
    'diputad', 'regimen', 'golpe de estado', 'tsj', 'fiscal general',
    'delcy', 'cabello', 'padrino lopez', 'edmundo gonzalez', 'comando con vzla',
    'politica', 'politico', 'lula', 'bolsonaro', 'presidencia', 'voto',
    'votacion', 'militante', 'manifestacion politica', 'protesta politica',
    'pandilla', 'narcotrafic', 'sicari', 'crimen', 'guerra', 'bombardeo',
    'ataque armado', 'homicidio', 'delincuencia armada'
]

PALABRAS_TEMAS_ECO_SOC = [
    'econom', 'dolar', 'bolivar', 'tasa', 'banco', 'bancari', 'comercio', 
    'comercial', 'empresa', 'empresari', 'negocio', 'produccion', 'petrole', 
    'gas', 'industria', 'consumo', 'salario', 'sueldo', 'bono', 'pension', 
    'jubilad', 'import', 'export', 'inflacion', 'costo', 'precio', 'transporte', 
    'vuelo', 'aeropuerto', 'via', 'vialidad', 'puente', 'obra', 'comunidad', 
    'vecin', 'salud', 'hospital', 'medic', 'farmacia', 'alimento', 'comida', 
    'educacion', 'colegio', 'universidad', 'escuela', 'estudiant', 'tecnolog', 
    'internet', 'luz', 'electrico', 'agua', 'parque', 'cultura', 'teatro', 
    'turismo', 'zulia', 'maracaibo', 'trabajad', 'empleo'
]

def es_titular_economico_o_social(titular, es_feed_economico=False):
    """
    Verifica que el titular pertenezca al ámbito económico, social, empresarial o comunitario,
    excluyendo rigurosamente la diatriba y temas partidistas o electorales.
    """
    if not titular or len(titular) < 12:
        return False
    t_low = titular.lower()
    
    # 1. Descartar si contiene palabras estrictamente políticas o partidistas
    for ex in PALABRAS_EXCLUIR_POLITICA:
        if re.search(r'\b' + re.escape(ex), t_low):
            return False
            
    # 2. Si proviene de un feed 100% económico verificado, pasa directamente
    if es_feed_economico:
        return True
        
    # 3. Si proviene de un portal general, debe coincidir con temas económicos/sociales
    return any(term in t_low for term in PALABRAS_TEMAS_ECO_SOC)


def asignar_categoria_y_asset(titular, medio=""):
    """
    Asigna una categoría y una imagen local según el texto del titular.
    Categorías: VENEZUELA, ECONOMÍA, INTERNACIONALES, MARACAIBO, SALUD.
    """
    t_low = (titular + " " + medio).lower()
    base_assets = os.path.join(config.BASE_DIR, "assets", "categories")
    
    if any(k in t_low for k in ['zulia', 'maracaibo', 'san francisco', 'cabimas', 'lago', 'puente']):
        return "MARACAIBO", os.path.join(base_assets, "maracaibo.jpg")
    if any(k in t_low for k in ['salud', 'medic', 'médic', 'hospital', 'enfermedad', 'farmac', 'virus', 'oms', 'vida saludable']):
        return "SALUD", os.path.join(base_assets, "salud.jpg")
    if any(k in t_low for k in ['internacional', 'onu', 'eeuu', 'estados unidos', 'europa', 'mundo', 'global', 'biden', 'trump', 'paz']):
        return "INTERNACIONALES", os.path.join(base_assets, "internacionales.jpg")
    if any(k in t_low for k in ['econom', 'finanz', 'dolar', 'dólar', 'bcv', 'banco', 'bancari', 'comercio', 'petroleo', 'petróleo', 'bolsa', 'wall street', 'inflac', 'precio', 'tasa']):
        return "ECONOMÍA", os.path.join(base_assets, "economia.jpg")
        
    return "VENEZUELA", os.path.join(base_assets, "venezuela.jpg")

def extraer_resumen_item(item, titular=""):
    """
    Extrae un resumen de 15 a 30 palabras desde el tag description o el contenido del item RSS.
    Retorna None si no logra extraer un resumen válido.
    """
    if item and hasattr(item, 'find'):
        desc_el = item.find('description')
        if desc_el:
            raw_desc = BeautifulSoup(desc_el.text, 'html.parser').text.strip()
            # Limpiar URLs
            clean_desc = re.sub(r'https?://\S+', '', raw_desc)
            # Limpiar prefijos de dominios web tipo "www,finanzasdigital.com"
            clean_desc = re.sub(r'www[\.,][a-zA-Z0-9\.\-_]+\s*', '', clean_desc)
            # Limpiar firmas de autor tipo "Por: ... Caracas.-"
            clean_desc = re.sub(r'^Por:\s*[^.\n\-]+(?:[\.\-]\s*|,\s*)?', '', clean_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+(?:\(EFE\)|Caracas\.-|Maracaibo\.-)\s*', '', clean_desc)
            # Limpiar guiones y espacios iniciales residuales
            clean_desc = re.sub(r'^[\s\-\u2013\u2014:,]+', '', clean_desc)
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            palabras = [p for p in clean_desc.split() if p]
            if len(palabras) >= 8:
                resumen = " ".join(palabras[:45])
                if not resumen.endswith(('.', '!', '?')):
                    resumen += "..."
                return resumen

    return None


def extraer_resumen_desde_url(url_articulo, timeout=6):
    """
    Obtiene el resumen real de un artículo accediendo a su página web.
    Intenta primero og:description, luego meta description,
    y finalmente el primer párrafo largo del cuerpo del artículo.
    """
    try:
        resp = requests.get(url_articulo, headers=HEADERS, verify=False, timeout=timeout)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, 'html.parser')

        for tag in [soup.find('meta', property='og:description'),
                    soup.find('meta', attrs={'name': 'description'})]:
            if tag and tag.get('content', '').strip():
                texto = tag['content'].strip()
                texto = re.sub(r'https?://\S+', '', texto)
                texto = re.sub(r'^[\s\-\u2013\u2014:,]+', '', texto)
                texto = re.sub(r'\s+', ' ', texto).strip()
                palabras = texto.split()
                if len(palabras) >= 8:
                    resumen = " ".join(palabras[:45])
                    if not resumen.endswith(('.', '!', '?')):
                        resumen += "..."
                    return resumen

        # Primer párrafo largo del artículo
        body = soup.select_one('.entry-content, .post-content, article .content, .article-body')
        if body:
            for p in body.find_all('p'):
                txt = p.text.strip()
                if len(txt) > 50:
                    txt = re.sub(r'https?://\S+', '', txt)
                    txt = re.sub(r'\s+', ' ', txt).strip()
                    palabras = txt.split()
                    resumen = " ".join(palabras[:45])
                    if not resumen.endswith(('.', '!', '?')):
                        resumen += "..."
                    return resumen
    except Exception:
        pass
    return None

def obtener_titulares_multiples(objetivo=5, minimo=4):
    """
    Obtiene exactamente 5 noticias categorizadas y coherentes:
    1. VENEZUELA (Nacional / Desarrollo)
    2. ECONOMÍA (Bancos / Mercados / Finanzas)
    3. MARACAIBO (Zulia / Regional)
    4. INTERNACIONALES (Finanzas / Geopolítica / Comercio global)
    5. SALUD (Medicina / Bienestar / Hospitales)

    Garantiza que el titular, el resumen, la categoría y la imagen correspondan
    estrictamente al mismo tema.
    """
    import warnings
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

    base_assets = os.path.join(config.BASE_DIR, "assets", "categories")

    def limpiar_titular(texto):
        if not texto:
            return ""
        texto_limpio = BeautifulSoup(texto, 'html.parser').text.strip()
        texto_limpio = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', texto_limpio).strip()
        texto_limpio = re.sub(r'[\U00010000-\U0010ffff]', '', texto_limpio)
        texto_limpio = re.sub(r'[\u2600-\u27BF\uFE00-\uFE0F]', '', texto_limpio)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
        texto_limpio = re.sub(r'\s*-\s*(DW|BBC News Mundo|BBC Mundo|Finanzas Digital|Banca y Negocios|Infobae|TalCual|Runrunes|El Diario|Noticia al Día|La Verdad|El Nacional|La Patilla|El Pitazo)$', '', texto_limpio, flags=re.IGNORECASE).strip()
        texto_limpio = re.sub(r'^[\s\|\-\:\.]+', '', texto_limpio).strip()
        return texto_limpio

    def extraer_desc_limpia(item):
        if not item:
            return ""
        d_el = item.find('description')
        if not d_el:
            return ""
        raw = BeautifulSoup(d_el.text, 'html.parser').text.strip()
        clean = re.sub(r'https?://\S+', '', raw)
        clean = re.sub(r'www[\.,][a-zA-Z0-9\.\-_]+\s*', '', clean)
        clean = re.sub(r'^Por:\s*[^.\n\-]+(?:[\.\-]\s*|,\s*)?', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+(?:\(EFE\)|Caracas\.-|Maracaibo\.-)\s*', '', clean)
        clean = re.sub(r'^[\s\-\u2013\u2014:,]+', '', clean)
        words = clean.strip().split()
        if len(words) >= 6:
            res = ' '.join(words[:45])
            if not res.endswith(('.', '!', '?')):
                res += '...'
            return res
        return ""

    titulares_por_categoria = {}
    titulares_vistos = set()

    print("📰 [TITULARES] Obteniendo noticias especializadas por categoría temática...")

    # ─────────────────────────────────────────────────────────────
    # 1. SALUD
    # ─────────────────────────────────────────────────────────────
    print("  🩺 Buscando noticia de SALUD...")
    try:
        r = requests.get('https://elpitazo.net/category/salud/feed/', headers=HEADERS, verify=False, timeout=7)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'html.parser')
            for it in s.find_all('item')[:5]:
                t = limpiar_titular(it.find('title').text)
                desc = extraer_desc_limpia(it)
                if t and desc and t.lower() not in titulares_vistos:
                    titulares_vistos.add(t.lower())
                    titulares_por_categoria["SALUD"] = {
                        "medio": "El Pitazo Salud",
                        "categoria": "SALUD",
                        "titular": t,
                        "resumen": desc,
                        "imagen_local": os.path.join(base_assets, "salud.jpg")
                    }
                    print(f"  ✅ [SALUD]: {t[:50]}...")
                    break
    except Exception as e:
        print(f"  ⚠️ Error en feed de salud: {e}")

    # Respaldo Google News Salud si no se encontró
    if "SALUD" not in titulares_por_categoria:
        try:
            gn_url = 'https://news.google.com/rss/search?q=venezuela+(salud+OR+medicina+OR+hospital+OR+oncologico+OR+farmacia)+when:3d&hl=es-419&gl=VE&ceid=VE:es-419'
            r = requests.get(gn_url, headers=HEADERS, verify=False, timeout=7)
            if r.status_code == 200:
                s = BeautifulSoup(r.content, 'html.parser')
                it = s.find('item')
                if it:
                    parts = limpiar_titular(it.find('title').text).rsplit(' - ', 1)
                    t = parts[0].strip()
                    med = parts[1].strip() if len(parts) > 1 else "Salud"
                    desc = extraer_desc_limpia(it) or t
                    titulares_por_categoria["SALUD"] = {
                        "medio": med,
                        "categoria": "SALUD",
                        "titular": t,
                        "resumen": desc,
                        "imagen_local": os.path.join(base_assets, "salud.jpg")
                    }
                    print(f"  ✅ [SALUD (Respaldo)]: {t[:50]}...")
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────
    # 2. INTERNACIONALES
    # ─────────────────────────────────────────────────────────────
    print("  🌐 Buscando noticia de INTERNACIONALES...")
    try:
        r = requests.get('https://rss.dw.com/xml/rss-sp-eco', headers=HEADERS, verify=False, timeout=7)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'html.parser')
            for it in s.find_all('item')[:6]:
                t = limpiar_titular(it.find('title').text)
                desc = extraer_desc_limpia(it)
                if t and desc and not any(k in t.lower() for k in ['muert', 'guerra', 'homicid', 'atentado', 'choque']):
                    if t.lower() not in titulares_vistos:
                        titulares_vistos.add(t.lower())
                        titulares_por_categoria["INTERNACIONALES"] = {
                            "medio": "DW Español",
                            "categoria": "INTERNACIONALES",
                            "titular": t,
                            "resumen": desc,
                            "imagen_local": os.path.join(base_assets, "internacionales.jpg")
                        }
                        print(f"  ✅ [INTERNACIONALES]: {t[:50]}...")
                        break
    except Exception as e:
        print(f"  ⚠️ Error en feed internacional DW: {e}")

    # Respaldo BBC Mundo o Google News Internacional
    if "INTERNACIONALES" not in titulares_por_categoria:
        try:
            r = requests.get('https://feeds.bbci.co.uk/mundo/temas/internacional/rss.xml', headers=HEADERS, timeout=7)
            if r.status_code == 200:
                s = BeautifulSoup(r.content, 'html.parser')
                for it in s.find_all('item')[:6]:
                    t = limpiar_titular(it.find('title').text)
                    desc = extraer_desc_limpia(it)
                    if t and desc and not any(k in t.lower() for k in ['muert', 'guerra', 'choque', 'asesin']):
                        titulares_por_categoria["INTERNACIONALES"] = {
                            "medio": "BBC Mundo",
                            "categoria": "INTERNACIONALES",
                            "titular": t,
                            "resumen": desc,
                            "imagen_local": os.path.join(base_assets, "internacionales.jpg")
                        }
                        print(f"  ✅ [INTERNACIONALES (BBC)]: {t[:50]}...")
                        break
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────
    # 3. MARACAIBO / ZULIA
    # ─────────────────────────────────────────────────────────────
    print("  🌉 Buscando noticia de MARACAIBO / ZULIA...")
    try:
        r = requests.get('https://noticiaaldia.com/feed/', headers=HEADERS, verify=False, timeout=7)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'html.parser')
            for it in s.find_all('item')[:12]:
                t = limpiar_titular(it.find('title').text)
                desc = extraer_desc_limpia(it)
                if any(k in (t + " " + desc).lower() for k in ['zulia', 'maracaibo', 'san francisco', 'cabimas', 'lago', 'puente']):
                    if t.lower() not in titulares_vistos:
                        titulares_vistos.add(t.lower())
                        titulares_por_categoria["MARACAIBO"] = {
                            "medio": "Noticia al Día",
                            "categoria": "MARACAIBO",
                            "titular": t,
                            "resumen": desc or "Información destacada del acontecer regional en el Zulia.",
                            "imagen_local": os.path.join(base_assets, "maracaibo.jpg")
                        }
                        print(f"  ✅ [MARACAIBO]: {t[:50]}...")
                        break
    except Exception as e:
        print(f"  ⚠️ Error en feed Maracaibo: {e}")

    # ─────────────────────────────────────────────────────────────
    # 4. ECONOMÍA
    # ─────────────────────────────────────────────────────────────
    print("  📈 Buscando noticia de ECONOMÍA...")
    try:
        r = requests.get('https://www.finanzasdigital.com/feed/', headers=HEADERS, verify=False, timeout=7)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'html.parser')
            for it in s.find_all('item')[:6]:
                t = limpiar_titular(it.find('title').text)
                desc = extraer_desc_limpia(it)
                if t and desc and t.lower() not in titulares_vistos:
                    if es_titular_economico_o_social(t, es_feed_economico=True):
                        titulares_vistos.add(t.lower())
                        titulares_por_categoria["ECONOMÍA"] = {
                            "medio": "Finanzas Digital",
                            "categoria": "ECONOMÍA",
                            "titular": t,
                            "resumen": desc,
                            "imagen_local": os.path.join(base_assets, "economia.jpg")
                        }
                        print(f"  ✅ [ECONOMÍA]: {t[:50]}...")
                        break
    except Exception as e:
        print(f"  ⚠️ Error en feed Economía: {e}")

    # ─────────────────────────────────────────────────────────────
    # 5. VENEZUELA (Nacional)
    # ─────────────────────────────────────────────────────────────
    print("  🇻🇪 Buscando noticia de VENEZUELA...")
    try:
        r = requests.get('https://www.el-nacional.com/economia/feed/', headers=HEADERS, verify=False, timeout=7)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'html.parser')
            for it in s.find_all('item')[:6]:
                t = limpiar_titular(it.find('title').text)
                desc = extraer_desc_limpia(it)
                if t and desc and t.lower() not in titulares_vistos:
                    if es_titular_economico_o_social(t, es_feed_economico=True):
                        titulares_vistos.add(t.lower())
                        titulares_por_categoria["VENEZUELA"] = {
                            "medio": "El Nacional",
                            "categoria": "VENEZUELA",
                            "titular": t,
                            "resumen": desc,
                            "imagen_local": os.path.join(base_assets, "venezuela.jpg")
                        }
                        print(f"  ✅ [VENEZUELA]: {t[:50]}...")
                        break
    except Exception as e:
        print(f"  ⚠️ Error en feed Venezuela: {e}")

    # Si alguna faltó, completar con respaldo de Banca y Negocios o El Pitazo
    ORDEN_DESEADO = ["VENEZUELA", "ECONOMÍA", "MARACAIBO", "INTERNACIONALES", "SALUD"]
    resultado_final = []
    for cat in ORDEN_DESEADO:
        if cat in titulares_por_categoria:
            resultado_final.append(titulares_por_categoria[cat])

    # Si por alguna razón falta alguna categoría, buscar en Banca y Negocios
    if len(resultado_final) < objetivo:
        print("  🔄 Completando noticias faltantes con Banca y Negocios...")
        try:
            r = requests.get('https://www.bancaynegocios.com/', headers=HEADERS, verify=False, timeout=7)
            if r.status_code == 200:
                s = BeautifulSoup(r.content, 'html.parser')
                items = s.select('.post-title a, article h2 a, .entry-title a')
                for it in items[:8]:
                    t = limpiar_titular(it.text)
                    link = it.get('href', '')
                    if t and t.lower() not in titulares_vistos:
                        titulares_vistos.add(t.lower())
                        res = extraer_resumen_desde_url(link) if link else t
                        cat, img = asignar_categoria_y_asset(t, "Banca y Negocios")
                        resultado_final.append({
                            "medio": "Banca y Negocios",
                            "categoria": cat,
                            "titular": t,
                            "resumen": res or t,
                            "imagen_local": img
                        })
                        if len(resultado_final) >= objetivo:
                            break
        except Exception:
            pass

    print(f"📰 [TITULARES] Total final: {len(resultado_final)} noticias completas y temáticamente coherentes.")
    return resultado_final[:objetivo]


if __name__ == "__main__":

    # Test rápido de extracción
    tasas = obtener_tasas_bcv()
    noticia = obtener_noticia_economica()
    tasa_binance = obtener_tasa_binance()
    titulares = obtener_titulares_multiples()
    print("\n--- RESULTADOS DEL TEST ---")
    print(f"Dólar USD: {tasas['usd']}")
    print(f"Euro EUR: {tasas['eur']}")
    print(f"Binance USDT/VES: {tasa_binance}")
    print(f"Noticia: {noticia['titulo']} ({noticia['link']})")
    print(f"Titulares: {len(titulares)} medios procesados")
