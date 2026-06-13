import requests
from bs4 import BeautifulSoup
import re
import urllib3

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

def obtener_resultados_mundial():
    """
    Obtiene los resultados de los partidos del Mundial desde la API de la webapp del usuario.
    Prioriza los resultados de 'yesterday' y luego los de 'today' que ya tengan marcador.
    """
    url = "https://copa26lf.vercel.app/api/matches"
    print("⚽ [MUNDIAL 2026] Extrayendo resultados desde copa26lf.vercel.app...")
    
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            resultados_finales = []
            
            # Solo resultados de AYER (partidos finalizados)
            yesterday = data.get("yesterday", [])
            for match in yesterday:
                home = match.get("homeTeam", "???")
                away = match.get("awayTeam", "???")
                h_score = match.get("homeScore", "0")
                a_score = match.get("awayScore", "0")
                resultados_finales.append(f"{home} {h_score} - {a_score} {away}")
            
            if resultados_finales:
                print(f"✅ [MUNDIAL 2026] Se encontraron {len(resultados_finales)} resultados.")
                # Retornar máximo 5 resultados más recientes
                return resultados_finales[:5]
            else:
                print("ℹ️ [MUNDIAL 2026] No se encontraron marcadores disponibles en la API.")
                return []
        else:
            print(f"⚠️ [MUNDIAL 2026] La API respondió con código {response.status_code}")
    except Exception as e:
        print(f"❌ [MUNDIAL 2026] Error al conectar con la webapp: {str(e)}")
        
    return []


if __name__ == "__main__":

    # Test rápido de extracción
    tasas = obtener_tasas_bcv()
    noticia = obtener_noticia_economica()
    tasa_binance = obtener_tasa_binance()
    print("\n--- RESULTADOS DEL TEST ---")
    print(f"Dólar USD: {tasas['usd']}")
    print(f"Euro EUR: {tasas['eur']}")
    print(f"Binance USDT/VES: {tasa_binance}")
    print(f"Noticia: {noticia['titulo']} ({noticia['link']})")
