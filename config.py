import os

# --- RUTAS DE ARCHIVOS Y DIRECTORIOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Base de datos SQLite
DB_PATH = os.path.join(BASE_DIR, "highlights.db")

# --- DETECCIÓN INTELIGENTE DEL ESCRITORIO DE WINDOWS (Soporte para OneDrive) ---
def _obtener_ruta_escritorio():
    user_profile = os.environ.get("USERPROFILE", "")
    # 1. Intentar Escritorio tradicional (verificando que sea directorio)
    escritorio_std = os.path.join(user_profile, "Desktop")
    if os.path.isdir(escritorio_std):
        return escritorio_std
    # 2. Intentar Escritorio de OneDrive (verificando que sea directorio)
    escritorio_od = os.path.join(user_profile, "OneDrive", "Desktop")
    if os.path.isdir(escritorio_od):
        return escritorio_od
    # 3. Buscar subcarpetas bajo OneDrive por si cambia de idioma o nombre
    onedrive_dir = os.path.join(user_profile, "OneDrive")
    if os.path.isdir(onedrive_dir):
        try:
            for item in os.listdir(onedrive_dir):
                sub_path = os.path.join(onedrive_dir, item)
                if os.path.isdir(sub_path) and item.lower() == "desktop":
                    return sub_path
        except Exception:
            pass
    return escritorio_std

ESCRITORIO = _obtener_ruta_escritorio()
OUTPUT_IMAGE_NAME = "boletin_highlights.png"
OUTPUT_IMAGE_PATH = os.path.join(ESCRITORIO, OUTPUT_IMAGE_NAME)
# Ruta de respaldo en la propia carpeta del proyecto por si falla el acceso al escritorio
BACKUP_IMAGE_PATH = os.path.join(BASE_DIR, OUTPUT_IMAGE_NAME)


# --- TELEGRAM BOT CONFIGURATION ---
# Completa estos valores para automatizar el envío del boletín a Telegram
TELEGRAM_TOKEN = ""   # Ej: "1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ"
TELEGRAM_CHAT_ID = "" # Ej: "-1001234567890" o "123456789"


# --- CONFIGURACIÓN DEL CLIMA ---
CLIMA_CIUDAD = "Maracaibo"
CLIMA_LATITUD = 10.63
CLIMA_LONGITUD = -71.64



# --- CONSTANTES DE DISEÑO DEL FLYER (PILLOW) ---
# Dimensiones de la imagen móvil vertical (Formato óptimo para smartphones)
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

# Paleta de Colores (Minimalista Light Premium - Blanco y Azul Corporativo)
BG_GRADIENT_START = (255, 255, 255)    # Blanco puro
BG_GRADIENT_END = (255, 255, 255)      # Blanco puro
CARD_BG_COLOR = (255, 255, 255, 255)   # Blanco sólido para las tarjetas
CARD_BORDER_COLOR = (160, 160, 160, 255) # Gris medio suave para los bordes
TEXT_PRIMARY_COLOR = (0, 0, 0)         # Negro puro para los contenidos
TEXT_SECONDARY_COLOR = (30, 70, 150)   # Azul corporativo oscuro para subtítulos y headers
YELLOW_ACCENT_BG = (255, 255, 255)     # Blanco para el banner del Mundial
YELLOW_ACCENT_TEXT = (30, 70, 150)     # Azul corporativo oscuro en el banner del Mundial
HEADER_GOLD_COLOR = (30, 70, 150)      # Azul corporativo oscuro para el título "HIGHLIGHT"



# Rutas de Fuentes Estándar en Windows
FONT_DIR = "C:\\Windows\\Fonts"
FONT_TITLE = os.path.join(FONT_DIR, "trebucbd.ttf")  # Trebuchet MS Bold
FONT_BOLD = os.path.join(FONT_DIR, "arialbd.ttf")    # Arial Bold
FONT_REGULAR = os.path.join(FONT_DIR, "arial.ttf")    # Arial Regular

# Rutas de Fuentes Oswald, Anton y Cursiva (Google Fonts)
FONT_OSWALD_DIR = os.path.join(BASE_DIR, "fonts")
FONT_OSWALD_BOLD = os.path.join(FONT_OSWALD_DIR, "Oswald-Bold.ttf")
FONT_OSWALD_SEMIBOLD = os.path.join(FONT_OSWALD_DIR, "Oswald-SemiBold.ttf")
FONT_OSWALD_REGULAR = os.path.join(FONT_OSWALD_DIR, "Oswald-Regular.ttf")
FONT_ANTON = os.path.join(FONT_OSWALD_DIR, "Anton-Regular.ttf")
FONT_SCRIPT = os.path.join(FONT_OSWALD_DIR, "Caveat-Bold.ttf")
