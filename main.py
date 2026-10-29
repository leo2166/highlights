import os
import sys
import io

# Reconfigurar salida estándar para soportar emojis en consolas Windows (UTF-8)
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from datetime import datetime
import requests
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Asegurar importación de módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import random
import json
import re
import config
import scraper
import generator

def obtener_efemeride_wikipedia(dia, mes):
    """
    Obtiene una efeméride histórica para el día y mes provistos desde la API oficial de Wikipedia en español.
    """
    url = f"https://es.wikipedia.org/api/rest_v1/feed/onthisday/events/{mes:02d}/{dia:02d}"
    print(f"📅 [WIKIPEDIA] Buscando efeméride para el {dia}/{mes} en Wikipedia...")
    try:
        headers = {
            'User-Agent': 'HighlightsDailyBot/1.0 (lucidio@example.com) Python-Requests'
        }
        # Desactivamos advertencias y hacemos la consulta
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            if events:
                # Seleccionar un evento aleatorio de la lista para darle dinamismo
                evento = random.choice(events)
                texto = evento.get("text", "")
                ano = evento.get("year", "")
                
                # Formatear el texto de la efeméride
                if ano and texto:
                    if not texto.strip().startswith(str(ano)):
                        efemeride = f"En {ano}, {texto}"
                    else:
                        efemeride = texto
                else:
                    efemeride = texto or "Hoy se conmemoran diversos acontecimientos históricos."
                
                # Quitar corchetes o enlaces residuales si existen (ej: [1], [2])
                efemeride = re.sub(r'\[\d+\]', '', efemeride).strip()
                print(f"✅ [WIKIPEDIA] Efeméride obtenida con éxito.")
                return efemeride
            else:
                print("⚠️ [WIKIPEDIA] No se encontraron eventos en la respuesta de Wikipedia.")
        else:
            print(f"⚠️ [WIKIPEDIA] La API de Wikipedia respondió con código {response.status_code}")
    except Exception as e:
        print(f"❌ [WIKIPEDIA] Error al obtener efeméride de Wikipedia: {str(e)}")
        
    # Fallback si falla internet o la API
    print("ℹ️ [WIKIPEDIA] Utilizando efeméride de respaldo local.")
    fallbacks = [
        "Hoy es un día ideal para planificar el crecimiento de tus proyectos y alcanzar tus objetivos.",
        "Se conmemoran importantes hitos en la historia de la ciencia y la cultura que forjaron nuestro presente.",
        "Un día como hoy se recuerda el valor y la persistencia de quienes trabajaron por un mundo mejor.",
        "Se celebran diversas efemérides culturales y conmemoraciones nacionales de gran significado histórico."
    ]
    return random.choice(fallbacks)

def obtener_efemeride_venezuela(dia, mes):
    """
    Obtiene la efeméride histórica y cultural correspondiente al día y mes en Venezuela,
    consultando de forma instantánea y robusta la base de datos offline local.
    """
    fecha_clave = f"{mes:02d}-{dia:02d}"
    fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "efemerides_venezuela_fallback.json")
    
    print(f"🇻🇪 [EFEMÉRIDE VENEZUELA] Consultando base de datos offline para el {dia}/{mes} ({fecha_clave})...")
    try:
        if os.path.exists(fallback_path):
            with open(fallback_path, "r", encoding="utf-8") as f:
                db = json.load(f)
                efemerides_diarias = db.get("efemerides_diarias", {})
                if fecha_clave in efemerides_diarias:
                    print(f"✅ [EFEMÉRIDE VENEZUELA] Efeméride obtenida exitosamente desde la base de datos local.")
                    return efemerides_diarias[fecha_clave]
    except Exception as err:
        print(f"⚠️ [EFEMÉRIDE VENEZUELA] Error al leer base de datos local: {str(err)}")
        
    return "Un día como hoy se recuerda el valioso aporte de los próceres y ciudadanos que construyeron la historia de Venezuela."

def obtener_pensamiento_dinamico():
    """
    Obtiene una frase célebre (pensamiento) en español. Intenta descargar la frase 
    desde una API pública confiable, y si falla, lee el archivo JSON local de respaldo.
    """
    url = "https://frasedeldia.azurewebsites.net/api/phrase"
    print("🧠 [PENSAMIENTO] Buscando pensamiento célebre en internet...")
    
    try:
        headers = {
            'User-Agent': 'HighlightsDailyBot/1.0 Python-Requests'
        }
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            texto = data.get("phrase", "").strip()
            autor = data.get("author", "Anónimo").strip()
            if texto:
                print("✅ [PENSAMIENTO] Frase obtenida con éxito desde la API de frases.")
                return {"texto": texto, "autor": autor}
    except Exception as e:
        print(f"⚠️ [PENSAMIENTO] No se pudo obtener la frase de internet ({str(e)}). Usando respaldo local...")

    # Fallback local desde quotes_fallback.json
    try:
        fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quotes_fallback.json")
        if os.path.exists(fallback_path):
            with open(fallback_path, "r", encoding="utf-8") as f:
                quotes = json.load(f)
                if quotes:
                    q = random.choice(quotes)
                    print("✅ [PENSAMIENTO] Frase obtenida con éxito desde el archivo de respaldo local.")
                    return q
    except Exception as err:
        print(f"❌ [PENSAMIENTO] Error al leer el archivo de respaldo local: {str(err)}")
        
    # Fallback absoluto final
    return {
        "texto": "La persistencia y el esfuerzo constante son el camino más seguro para lograr cualquier meta.",
        "autor": "Anónimo"
    }


def generar_texto_boletin(tasas, noticia, pensamiento, efemeride_universal, efemeride_venezuela, clima, fecha_formateada, html_format=False):
    """
    Formatea el boletín en texto plano o HTML para WhatsApp, Telegram o Consola.
    """
    ciudad = getattr(config, "CLIMA_CIUDAD", "Caracas")
    if clima and len(clima) >= 2:
        if html_format:
            clima_texto = f"""🌤️ <b>ESTADO DEL TIEMPO ({ciudad.upper()})</b>
• <b>Hoy:</b> {clima[0]['emoji']} {clima[0]['descripcion']} | {clima[0]['temp_max']} / {clima[0]['temp_min']}
• <b>Mañana:</b> {clima[1]['emoji']} {clima[1]['descripcion']} | {clima[1]['temp_max']} / {clima[1]['temp_min']}"""
        else:
            clima_texto = f"""🌤️ ESTADO DEL TIEMPO ({ciudad.upper()})
• Hoy: {clima[0]['emoji']} {clima[0]['descripcion']} | {clima[0]['temp_max']} / {clima[0]['temp_min']}
• Mañana: {clima[1]['emoji']} {clima[1]['descripcion']} | {clima[1]['temp_max']} / {clima[1]['temp_min']}"""
    else:
        clima_texto = f"🌤️ <b>ESTADO DEL TIEMPO ({ciudad.upper()})</b>\nInformación no disponible." if html_format else f"🌤️ ESTADO DEL TIEMPO ({ciudad.upper()})\nInformación no disponible."

    if html_format:
        return f"""✨ <b>HIGHLIGHTS DIARIO</b> ✨
📅 <b>Fecha:</b> {fecha_formateada}

🧠 <b>PENSAMIENTO UNIVERSAL</b>
"<i>{pensamiento['texto']}</i>"
— <b>{pensamiento['autor']}</b>

📅 <b>EFEMÉRIDES DEL DÍA</b>
• <b>Universal:</b> {efemeride_universal}
• <b>Venezuela:</b> {efemeride_venezuela}

🇻🇪 <b>NOTICIA DESTACADA</b>
<b>Titular:</b> {noticia['titulo']}
🔗 <b>Enlace:</b> {noticia['link']}

💵 <b>PARIDAD CAMBIARIA (Bs.)</b>
🇺🇸 <b>Dólar USD:</b> {tasas['usd']} Bs.
🇪🇺 <b>Euro EUR:</b> {tasas['eur']} Bs.
₿ <b>Binance USDT/VES:</b> {tasas.get('binance', 'No disponible')} Bs.
<i>BCV Tasa Oficial · Binance P2P (SELL) · Fecha Valor: {tasas['fecha']}</i>

{clima_texto}

---
<i>Generado automáticamente | ✍️ Ing. LF</i>"""
    else:
        return f"""✨ HIGHLIGHTS DIARIO ✨
📅 Fecha: {fecha_formateada}

🧠 PENSAMIENTO UNIVERSAL
"{pensamiento['texto']}"
— {pensamiento['autor']}

📅 EFEMÉRIDES DEL DÍA
• Universal: {efemeride_universal}
• Venezuela: {efemeride_venezuela}

🇻🇪 NOTICIA DESTACADA
Titular: {noticia['titulo']}
Enlace: {noticia['link']}

💵 PARIDAD CAMBIARIA (Bs.)
🇺🇸 Dólar USD: {tasas['usd']} Bs.
🇪🇺 Euro EUR: {tasas['eur']} Bs.
₿ Binance USDT/VES: {tasas.get('binance', 'No disponible')} Bs.
BCV Tasa Oficial · Binance P2P (SELL) · Fecha Valor: {tasas['fecha']}

{clima_texto}

---
Generado automáticamente | ✍️ Ing. LF"""

def enviar_a_telegram(image_path, texto_html):
    """
    Envía la imagen del boletín y el resumen de texto a un canal o chat de Telegram.
    """
    token = config.TELEGRAM_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        print("\n📢 [TELEGRAM] Envío omitido: Configura TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en config.py para automatizar el envío.")
        return False

    print("\n📤 [TELEGRAM] Enviando boletín (imagen + caption) a Telegram...")
    try:
        url_photo = f"https://api.telegram.org/bot{token}/sendPhoto"
        
        # El límite de caracteres en el pie de foto de Telegram es 1024 caracteres.
        # Si el texto es más largo, lo recortamos y mandamos un mensaje de texto separado.
        caption_text = texto_html
        enviar_mensaje_separado = False
        
        if len(texto_html) > 1020:
            caption_text = texto_html[:1000] + "...\n\n(Texto continuado abajo)"
            enviar_mensaje_separado = True

        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': chat_id,
                'caption': caption_text,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url_photo, files=files, data=data, verify=False, timeout=30)
            
            if response.status_code == 200:
                print("✅ [TELEGRAM] Imagen enviada exitosamente con su descripción.")
                
                if enviar_mensaje_separado:
                    url_message = f"https://api.telegram.org/bot{token}/sendMessage"
                    data_msg = {
                        'chat_id': chat_id,
                        'text': texto_html,
                        'parse_mode': 'HTML'
                    }
                    requests.post(url_message, data=data_msg, verify=False, timeout=20)
                    print("✅ [TELEGRAM] Mensaje de texto completo enviado de forma complementaria.")
                return True
            else:
                print(f"⚠️ [TELEGRAM] Error al enviar foto (Código {response.status_code}): {response.text}")
                
                # Reintento enviando solo texto
                print("🔄 Intentando enviar solo texto como alternativa...")
                url_message = f"https://api.telegram.org/bot{token}/sendMessage"
                data_msg = {
                    'chat_id': chat_id,
                    'text': texto_html,
                    'parse_mode': 'HTML'
                }
                response_msg = requests.post(url_message, data=data_msg, verify=False, timeout=20)
                if response_msg.status_code == 200:
                    print("✅ [TELEGRAM] Mensaje de texto alternativo enviado con éxito.")
                    return True
                else:
                    print(f"❌ [TELEGRAM] Falló reintento de solo texto: {response_msg.text}")
                    
    except Exception as e:
        print(f"❌ [TELEGRAM] Excepción inesperada en el envío: {str(e)}")
        
    return False

def main():
    print("=" * 60)
    print("🚀 PROCESO DE GENERACIÓN DE BOLETÍN 'HIGHLIGHTS' DIARIO 🚀")
    print("=" * 60)

    # Obtener fecha actual
    ahora = datetime.now()
    dia = ahora.day
    mes = ahora.month
    fecha_iso = ahora.strftime("%Y%m%d")

    # Nombre del día de la semana y mes
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses_ano = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha_formateada = f"{dias_semana[ahora.weekday()]}, {dia} de {meses_ano[mes - 1]} de {ahora.year}"

    # 1. Obtener pensamiento y efemérides de forma dinámica desde APIs
    print(f"\n🔍 Obteniendo datos dinámicos para el {dia}/{mes} ({fecha_formateada})...")
    pensamiento = obtener_pensamiento_dinamico()
    efemeride_universal = obtener_efemeride_wikipedia(dia, mes)
    efemeride_venezuela = obtener_efemeride_venezuela(dia, mes)
    print(f"✅ Pensamiento: \"{pensamiento['texto']}\" — {pensamiento['autor']}")
    print(f"✅ Efeméride Universal: {efemeride_universal}")
    print(f"✅ Efeméride Venezuela: {efemeride_venezuela}")

    # 2. Obtener Estado del Tiempo (Open-Meteo)
    print("")
    clima = scraper.obtener_clima()

    # 3. Web Scraping BCV
    print("")
    tasas = scraper.obtener_tasas_bcv()

    # 3b. Tasa Binance P2P (USDT/VES)
    print("")
    tasas["binance"] = scraper.obtener_tasa_binance()

    # 4. RSS Noticia Económica
    print("")
    noticia = scraper.obtener_noticia_economica()

    # 5. Obtener titulares de múltiples medios
    print("")
    titulares_medios = scraper.obtener_titulares_multiples()

    # 6. Generar Imagen con Pillow (Flyer)
    print("")
    datos_db = {
        "pensamiento": pensamiento,
        "efemeride_universal": efemeride_universal,
        "efemeride_venezuela": efemeride_venezuela,
        "clima": clima,
        "titulares_medios": titulares_medios
    }
    image_path = generator.crear_boletin_grafico(tasas, noticia, datos_db)
    
    # Generar Versión 2 (Formato Cuadrado Premium)
    image_path_sq = generator.crear_boletin_grafico_cuadrado(tasas, noticia, datos_db)

    # Generar Versión 3 (Formato Vertical 1200×1500 — Instagram Feed / LinkedIn)
    image_path_1200 = generator.crear_boletin_1200x1500(tasas, noticia, datos_db)


    # 7. Generar textos del boletín
    texto_consola = generar_texto_boletin(tasas, noticia, pensamiento, efemeride_universal, efemeride_venezuela, clima, fecha_formateada, html_format=False)
    texto_telegram = generar_texto_boletin(tasas, noticia, pensamiento, efemeride_universal, efemeride_venezuela, clima, fecha_formateada, html_format=True)

    # Imprimir en consola la versión en texto plano para que el usuario pueda copiarla fácilmente
    print("\n" + "=" * 50)
    print("📝 COPIA EL SIGUIENTE TEXTO PARA COMPARTIR EN REDES/WHATSAPP:")
    print("=" * 50)
    print(texto_consola)
    print("=" * 50 + "\n")

    # 8. Envío Automatizado a Telegram (si está configurado)
    enviar_a_telegram(image_path, texto_telegram)

    print("\n🎉 ¡Proceso completado exitosamente! El boletín gráfico se encuentra listo.")
    print("=" * 60)

if __name__ == "__main__":
    main()
