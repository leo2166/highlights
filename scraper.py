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
    """
    if item and hasattr(item, 'find'):
        desc_el = item.find('description')
        if desc_el:
            raw_desc = BeautifulSoup(desc_el.text, 'html.parser').text.strip()
            clean_desc = re.sub(r'https?://\S+', '', raw_desc)
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            palabras = [p for p in clean_desc.split() if p]
            if len(palabras) >= 10:
                resumen = " ".join(palabras[:24])
                if not resumen.endswith(('.', '!', '?')):
                    resumen += "..."
                return resumen
                
    return "El acontecer nacional e internacional destaca importantes avances y análisis de interés colectivo."

def obtener_titulares_multiples(objetivo=5, minimo=4):
    """
    Obtiene 5 noticias reales del ámbito ECONÓMICO y SOCIAL con titular,
    resumen de 15-30 palabras, categoría e imagen contextual para la portada.
    """
    import warnings
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

    FUENTES_ECONOMICAS_SOCIALES = [
        {"medio": "El Nacional",      "url": "https://www.el-nacional.com/economia/feed/",         "es_eco": True},
        {"medio": "Finanzas Digital", "url": "https://www.finanzasdigital.com/feed/",              "es_eco": True},
        {"medio": "Noticia al Día",   "url": "https://noticiaaldia.com/feed/",                     "es_eco": False},
        {"medio": "Tal Cual",         "url": "https://talcualdigital.com/seccion/economia/feed/", "es_eco": True},
        {"medio": "Banca y Negocios", "url": "https://www.bancaynegocios.com/",                   "es_eco": True, "es_web": True},
        {"medio": "El Pitazo",        "url": "https://elpitazo.net/category/economia/feed/",       "es_eco": True},
        {"medio": "El Pitazo",        "url": "https://elpitazo.net/category/comunidad/feed/",      "es_eco": False},
        {"medio": "El Diario",        "url": "https://eldiario.com/seccion/economia/feed/",        "es_eco": True},
        {"medio": "BBC Mundo",        "url": "https://feeds.bbci.co.uk/mundo/temas/economia/rss.xml", "es_eco": True},
    ]

    print(f"📰 [TITULARES] Obteniendo noticias del ámbito ECONÓMICO y SOCIAL (Objetivo: {objetivo}, Mínimo: {minimo})...")
    titulares = []
    titulares_extra = []
    titulares_textos_vistos = set()

    def limpiar_titular(texto):
        if not texto:
            return ""
        texto_limpio = BeautifulSoup(texto, 'html.parser').text.strip()
        texto_limpio = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', texto_limpio).strip()
        texto_limpio = re.sub(r'[\U00010000-\U0010ffff]', '', texto_limpio)
        texto_limpio = re.sub(r'[\u2600-\u27BF\uFE00-\uFE0F]', '', texto_limpio)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
        texto_limpio = re.sub(r'\s*-\s*(BBC News Mundo|BBC Mundo|Finanzas Digital|Banca y Negocios|Infobae|TalCual|Runrunes|El Diario|Noticia al Día|La Verdad|El Nacional|La Patilla|El Pitazo)$', '', texto_limpio, flags=re.IGNORECASE).strip()
        texto_limpio = re.sub(r'^[\s\|\-\:\.]+', '', texto_limpio).strip()
        return texto_limpio

    # Consultar las fuentes especializadas
    for fuente in FUENTES_ECONOMICAS_SOCIALES:
        if len(titulares) >= objetivo:
            break
        nombre = fuente["medio"]
        url = fuente["url"]
        es_eco = fuente.get("es_eco", False)
        es_web = fuente.get("es_web", False)

        try:
            response = requests.get(url, headers=HEADERS, verify=False, timeout=7)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                if es_web:
                    items = soup.select('.post-title a, article h2 a, .entry-title a')
                else:
                    items = soup.find_all('item')

                primer_agregado = False
                for item in items[:8]:
                    if es_web:
                        raw_text = item.text.strip() if hasattr(item, 'text') else ""
                    else:
                        title_el = item.find('title')
                        raw_text = title_el.text.strip() if title_el else ""

                    titulo = limpiar_titular(raw_text)
                    if titulo and len(titulo) > 15 and titulo.lower() not in titulares_textos_vistos:
                        if es_titular_economico_o_social(titulo, es_eco):
                            titulares_textos_vistos.add(titulo.lower())
                            cat, img_local = asignar_categoria_y_asset(titulo, nombre)
                            resumen = extraer_resumen_item(item if not es_web else None, titulo)
                            item_data = {
                                "medio": nombre,
                                "titular": titulo,
                                "resumen": resumen,
                                "categoria": cat,
                                "imagen_local": img_local
                            }
                            if not primer_agregado:
                                titulares.append(item_data)
                                print(f"  ✅ [{nombre}] ({cat}): \"{titulo[:50]}...\"")
                                primer_agregado = True
                                break
                            else:
                                titulares_extra.append(item_data)
                if not primer_agregado:
                    print(f"  ℹ️ [{nombre}]: No se encontraron noticias económico-sociales en los primeros titulares.")
            else:
                print(f"  ⚠️ [{nombre}]: Código HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ [{nombre}]: Conexión no disponible o timeout ({str(e)[:35]}...)")

    # Si faltan titulares para llegar al objetivo, usar titulares secundarios válidos
    if len(titulares) < objetivo and titulares_extra:
        for extra in titulares_extra:
            titulares.append(extra)
            print(f"  ➕ [Extra] [{extra['medio']}]: \"{extra['titular'][:50]}...\"")
            if len(titulares) >= objetivo:
                break

    # Respaldo inteligente en Google News enfocado en Economía y Comunidad
    if len(titulares) < minimo:
        print("🔄 [RESPALDO] Consultando Google News Venezuela (Economía, Comercio y Comunidad)...")
        try:
            gn_url = "https://news.google.com/rss/search?q=venezuela+(economia+OR+comercio+OR+petroleo+OR+salud+OR+educacion+OR+comunidad)+-elecciones+-maduro+-machado+-politica+when:2d&hl=es-419&gl=VE&ceid=VE:es-419"
            gn_res = requests.get(gn_url, headers=HEADERS, verify=False, timeout=8)
            if gn_res.status_code == 200:
                gn_soup = BeautifulSoup(gn_res.content, 'html.parser')
                for g_item in gn_soup.find_all('item'):
                    g_title_el = g_item.find('title')
                    if g_title_el:
                        raw_t = limpiar_titular(g_title_el.text)
                        partes = raw_t.rsplit(' - ', 1)
                        if len(partes) == 2:
                            g_tit, g_med = partes[0].strip(), partes[1].strip()
                        else:
                            g_tit, g_med = raw_t, "Economía & Sociedad"

                        if g_tit and len(g_tit) > 15 and g_tit.lower() not in titulares_textos_vistos:
                            if es_titular_economico_o_social(g_tit, es_feed_economico=False):
                                titulares_textos_vistos.add(g_tit.lower())
                                cat, img_local = asignar_categoria_y_asset(g_tit, g_med)
                                resumen = extraer_resumen_item(g_item, g_tit)
                                titulares.append({
                                    "medio": g_med,
                                    "titular": g_tit,
                                    "resumen": resumen,
                                    "categoria": cat,
                                    "imagen_local": img_local
                                })
                                print(f"  ✅ [Google News Eco/Soc] {g_med}: \"{g_tit[:50]}...\"")
                                if len(titulares) >= objetivo:
                                    break
        except Exception as gn_err:
            print(f"  ⚠️ Error en respaldo Google News: {str(gn_err)}")

    resultado_final = titulares[:objetivo]
    
    # Asegurar que las 5 noticias tengan categorías distintas para máxima riqueza visual
    CATS_DEFAULT = ["VENEZUELA", "ECONOMÍA", "INTERNACIONALES", "MARACAIBO", "SALUD"]
    base_assets = os.path.join(config.BASE_DIR, "assets", "categories")
    cats_vistas = set()
    for idx, noti in enumerate(resultado_final):
        cat_actual = noti.get("categoria", "VENEZUELA")
        if cat_actual in cats_vistas:
            for alt_cat in CATS_DEFAULT:
                if alt_cat not in cats_vistas:
                    noti["categoria"] = alt_cat
                    noti["imagen_local"] = os.path.join(base_assets, f"{alt_cat.lower()}.jpg")
                    break
        cats_vistas.add(noti["categoria"])

    print(f"📰 [TITULARES] Total final: {len(resultado_final)} noticias completas listas para el boletín.")
    return resultado_final


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
