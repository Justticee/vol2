# bot_registro.py - Bot para registrar códigos en SRCEI
import os
import requests
import time
import sys
import threading
import json
import re
from flask import Flask

# ========== CONFIGURACIÓN ==========
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_BASE = "https://codigo.srcei.cl"
ULTIMO_ID = 0
# ===================================

if not TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN no configurado")
    sys.exit(1)

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "🤖 Bot Registro SRCEI funcionando!", 200

@app_flask.route('/health')
def health():
    return "OK", 200

def enviar_mensaje(chat_id, texto, parse_mode=None):
    """Envía mensaje de texto"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": texto}
    if parse_mode:
        data["parse_mode"] = parse_mode
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return False

def enviar_espera(chat_id, mensaje_id=None):
    """Envía indicador de escritura"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except:
        pass

def registrar_codigo(chat_id, run, nombres, apellido_paterno, apellido_materno, email, codigo):
    """Registra un código en la API"""
    url = f"{API_BASE}/api/proxyiris/registerCode/"
    
    payload = {
        "run": str(run),
        "nombres": nombres.upper(),
        "apellPri": apellido_paterno.upper(),
        "apellSec": apellido_materno.upper(),
        "email": email.lower(),
        "codigo": str(codigo)
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://consola.codigo.srcei.cl",
        "Referer": "https://consola.codigo.srcei.cl/"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return True, data
            except:
                return True, {"respuesta": response.text}
        else:
            return False, f"Error {response.status_code}: {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return False, "Tiempo de espera agotado"
    except Exception as e:
        return False, f"Error: {str(e)[:200]}"

def validar_run(run):
    """Valida que el RUN tenga formato correcto (12345678)"""
    return run.isdigit() and len(run) >= 7 and len(run) <= 8

def validar_email(email):
    """Valida formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_codigo(codigo):
    """Valida que el código sea numérico y tenga entre 4 y 10 dígitos"""
    return codigo.isdigit() and 4 <= len(codigo) <= 10

def iniciar_bot():
    """Loop principal del bot"""
    ultimo_id = 0
    
    # Estados de usuarios para registro paso a paso
    estados_usuarios = {}
    
    print("=" * 55)
    print("🤖 BOT REGISTRO SRCEI - MODO POLLING")
    print("=" * 55)
    print(f"✅ Token configurado")
    print(f"✅ API: {API_BASE}")
    print("📡 Bot corriendo... Esperando mensajes...")
    print("=" * 55)
    
    MENSAJE_BIENVENIDA = """
🤖 *BOT REGISTRO SRCEI* 🤖

¡Bienvenido! Este bot te permite registrar códigos en el sistema de SRCEI.

*📌 Comandos disponibles:*

📝 `/registrar` - Registrar un nuevo código (paso a paso)
🚀 `/registrar_directo RUN|NOMBRES|APELLIDO_P|APELLIDO_M|EMAIL|CODIGO` - Registro rápido
✅ `/validar_run RUN` - Validar formato de RUN
📊 `/estado` - Estado del sistema
❓ `/help` - Ver esta ayuda

*📝 Ejemplo de registro rápido:*
