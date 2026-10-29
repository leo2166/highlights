import sys
sys.path.insert(0, 'C:\\Users\\Lucidio\\Proyectos\\highlights')
from generator import crear_boletin_grafico
from datetime import datetime

# Datos de prueba
ahora = datetime.now()
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
meses_ano = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
fecha_formateada = f"{dias_semana[ahora.weekday()]}, {ahora.day} de {meses_ano[ahora.month - 1]} de {ahora.year}"
hora_formateada = ahora.strftime("%I:%M %p")

tasas = {"usd": "520,91", "eur": "604,16", "binance": "773,10", "fecha": fecha_formateada}
noticia = {"titulo": "Asociaciones de Jubilados del Zulia analizan el impacto de los nuevos ajustes de indexación de bonos en el sector público nacional.", "link": "https://www.bancaynegocios.com/"}
db = {
    "pensamiento": {"texto": "El secreto del cambio es enfocar toda tu energía no en luchar contra lo viejo, sino en construir lo nuevo.", "autor": "Sócrates"},
    "efemeride_venezuela": "Hoy conmemoramos el Día Mundial de la Medicina Familiar en Venezuela, reconociendo el pilar fundamental de la salud pública."
}

result = crear_boletin_grafico(tasas, noticia, db)
print(f"\n✅ Boletín vertical generado: {result}")
print(f"\n📍 Ubicado en: Escritorio de Windows (OneDrive)")