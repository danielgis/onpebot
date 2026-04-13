import requests
import json
import os

# Configuración de Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "last_state.txt"


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://resultados.onpe.gob.pe/", # A veces validan de dónde vienes
    "Origin": "https://resultados.onpe.gob.pe"
}

# URLs de ONPE
URL_RESUMEN = "https://resultadoelectoral.onpe.gob.pe/presentacion-backend/resumen-general/totales?idEleccion=10&tipoFiltro=eleccion"
URL_PARTICIPANTES = "https://resultadoelectoral.onpe.gob.pe/presentacion-backend/resumen-general/participantes?idEleccion=10&tipoFiltro=eleccion"

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def get_data():
    try:
        # 1. Consumir Resumen
        resumen = requests.get(URL_RESUMEN, headers=headers).json()
        # 2. Consumir Participantes
        participantes = requests.get(URL_PARTICIPANTES, headers=headers).json()
        
        if not resumen['success'] or not participantes['success']:
            return None
        
        return resumen['data'], participantes['data']
    except Exception as e:
        print(f"Error consumiendo API: {e}")
        return None

def main():
    data_resumen, data_part = get_data()
    if not data_resumen:
        return

    current_val = str(data_resumen['actasContabilizadas'])
    
    # Leer el valor anterior si existe
    last_val = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            last_val = f.read().strip()

    # Si el valor cambió (o es la primera vez que corre)
    if current_val != last_val:
        print(f"Cambio detectado: {last_val} -> {current_val}")
        
        # Armar el mensaje con el Top 3 de candidatos
        top_candidatos = sorted(data_part, key=lambda x: x['totalVotosValidos'], reverse=True)[:10]
        
        msg = f"📊 *Actualización ONPE*\n"
        msg += f"✅ Actas Contabilizadas: `{current_val}%` ({data_resumen['contabilizadas']} actas)\n"
        msg += f"👥 Participación: `{data_resumen['participacionCiudadana']}%` \n\n"
        msg += f"🏆 *Top 3 Candidatos:*\n"
        
        for i, c in enumerate(top_candidatos, 1):
            msg += f"{i}. {c['nombreCandidato']} ({c['nombreAgrupacionPolitica']}): *{c['porcentajeVotosValidos']}%*\n"

        # print(msg)
        send_telegram_msg(msg)
        
        # Guardar el nuevo valor
        with open(STATE_FILE, "w") as f:
            f.write(current_val)
    else:
        print("Sin cambios en las actas.")

if __name__ == "__main__":
    main()