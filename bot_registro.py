# bot_registro.py - Versión corregida
import os
import requests
import time
import sys
import threading
import json
import re
from flask import Flask

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_BASE = "https://codigo.srcei.cl"
ULTIMO_ID = 0

if not TOKEN:
    print("ERROR: TELEGRAM_TOKEN no configurado")
    sys.exit(1)

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot Registro SRCEI funcionando!", 200

@app_flask.route('/health')
def health():
    return "OK", 200

def enviar_mensaje(chat_id, texto, parse_mode=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": texto}
    if parse_mode:
        data["parse_mode"] = parse_mode
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

def enviar_espera(chat_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except:
        pass

def registrar_codigo(chat_id, run, nombres, apellido_paterno, apellido_materno, email, codigo):
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
                return True, response.json()
            except:
                return True, {"respuesta": response.text}
        else:
            return False, f"Error {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def validar_run(run):
    return run.isdigit() and len(run) in [7, 8]

def validar_email(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_codigo(codigo):
    return codigo.isdigit() and 4 <= len(codigo) <= 10

def iniciar_bot():
    ultimo_id = 0
    estados_usuarios = {}
    
    MENSAJE_BIENVENIDA = """
🤖 BOT REGISTRO SRCEI 🤖

Bienvenido! Este bot te permite registrar codigos en el sistema de SRCEI.

Comandos disponibles:

/registrar - Registrar un nuevo codigo (paso a paso)
/registrar_directo RUN|NOMBRES|APELLIDO_P|APELLIDO_M|EMAIL|CODIGO - Registro rapido
/validar_run RUN - Validar formato de RUN
/estado - Estado del sistema
/help - Ver esta ayuda

Ejemplo de registro rapido:
/registrar_directo 14174673|LUIS IVAN|SANCHEZ|ANTIL|pegojhony79@gmail.com|656565
"""
    
    print("BOT INICIADO - Modo Registro")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"offset": ultimo_id + 1, "timeout": 30}
            respuesta = requests.get(url, params=params, timeout=35)
            datos = respuesta.json()
            
            if datos.get("ok"):
                for mensaje in datos.get("result", []):
                    ultimo_id = mensaje["update_id"]
                    chat_id = mensaje["message"]["chat"]["id"]
                    texto = mensaje["message"].get("text", "")
                    
                    print(f"Mensaje: {texto}")
                    
                    if chat_id in estados_usuarios:
                        paso = estados_usuarios[chat_id]["paso"]
                        datos_reg = estados_usuarios[chat_id]["datos"]
                        
                        if paso == 1:
                            if validar_run(texto):
                                datos_reg["run"] = texto
                                estados_usuarios[chat_id]["paso"] = 2
                                enviar_mensaje(chat_id, "Paso 2/6: Ingresa los NOMBRES completos")
                            else:
                                enviar_mensaje(chat_id, "RUN invalido. Reingresa:")
                        
                        elif paso == 2:
                            if len(texto) >= 3:
                                datos_reg["nombres"] = texto.upper()
                                estados_usuarios[chat_id]["paso"] = 3
                                enviar_mensaje(chat_id, "Paso 3/6: Ingresa el APELLIDO PATERNO")
                            else:
                                enviar_mensaje(chat_id, "Nombres muy cortos. Reingresa:")
                        
                        elif paso == 3:
                            if len(texto) >= 2:
                                datos_reg["apellido_paterno"] = texto.upper()
                                estados_usuarios[chat_id]["paso"] = 4
                                enviar_mensaje(chat_id, "Paso 4/6: Ingresa el APELLIDO MATERNO")
                            else:
                                enviar_mensaje(chat_id, "Apellido muy corto. Reingresa:")
                        
                        elif paso == 4:
                            if len(texto) >= 2:
                                datos_reg["apellido_materno"] = texto.upper()
                                estados_usuarios[chat_id]["paso"] = 5
                                enviar_mensaje(chat_id, "Paso 5/6: Ingresa el CORREO ELECTRONICO")
                            else:
                                enviar_mensaje(chat_id, "Apellido muy corto. Reingresa:")
                        
                        elif paso == 5:
                            if validar_email(texto):
                                datos_reg["email"] = texto.lower()
                                estados_usuarios[chat_id]["paso"] = 6
                                enviar_mensaje(chat_id, "Paso 6/6: Ingresa el CODIGO")
                            else:
                                enviar_mensaje(chat_id, "Email invalido. Reingresa:")
                        
                        elif paso == 6:
                            if validar_codigo(texto):
                                datos_reg["codigo"] = texto
                                enviar_mensaje(chat_id, "Registrando codigo...")
                                
                                exito, resultado = registrar_codigo(
                                    chat_id, datos_reg["run"], datos_reg["nombres"],
                                    datos_reg["apellido_paterno"], datos_reg["apellido_materno"],
                                    datos_reg["email"], datos_reg["codigo"]
                                )
                                
                                if exito:
                                    msg = f"REGISTRO EXITOSO!\n\nRUN: {datos_reg['run']}\nNombres: {datos_reg['nombres']}\nEmail: {datos_reg['email']}\nCodigo: {datos_reg['codigo']}"
                                    enviar_mensaje(chat_id, msg)
                                else:
                                    enviar_mensaje(chat_id, f"Error: {resultado}")
                                
                                del estados_usuarios[chat_id]
                            else:
                                enviar_mensaje(chat_id, "Codigo invalido. Reingresa:")
                        
                        continue
                    
                    if texto == "/start" or texto == "/help":
                        enviar_mensaje(chat_id, MENSAJE_BIENVENIDA)
                    
                    elif texto == "/estado":
                        enviar_mensaje(chat_id, "Bot activo y funcionando correctamente!")
                    
                    elif texto == "/registrar":
                        estados_usuarios[chat_id] = {"paso": 1, "datos": {}}
                        enviar_mensaje(chat_id, "Paso 1/6: Ingresa el RUN (solo numeros, 7-8 digitos)")
                    
                    elif texto.startswith("/registrar_directo"):
                        partes = texto.replace("/registrar_directo", "").strip().split("|")
                        if len(partes) == 6:
                            run, nombres, ap_pat, ap_mat, email, codigo = partes
                            if validar_run(run) and validar_email(email) and validar_codigo(codigo):
                                enviar_mensaje(chat_id, "Registrando...")
                                exito, resultado = registrar_codigo(chat_id, run, nombres, ap_pat, ap_mat, email, codigo)
                                if exito:
                                    enviar_mensaje(chat_id, f"Registro exitoso!\nRUN: {run}")
                                else:
                                    enviar_mensaje(chat_id, f"Error: {resultado}")
                            else:
                                enviar_mensaje(chat_id, "Datos invalidos. Verifica RUN, email y codigo.")
                        else:
                            enviar_mensaje(chat_id, "Formato: /registrar_directo RUN|NOMBRES|AP_PAT|AP_MAT|EMAIL|CODIGO")
                    
                    elif texto.startswith("/validar_run"):
                        partes = texto.split()
                        if len(partes) == 2:
                            if validar_run(partes[1]):
                                enviar_mensaje(chat_id, f"RUN {partes[1]} es valido")
                            else:
                                enviar_mensaje(chat_id, f"RUN {partes[1]} es invalido")
                    
                    elif texto.lower() == "cancelar" and chat_id in estados_usuarios:
                        del estados_usuarios[chat_id]
                        enviar_mensaje(chat_id, "Registro cancelado")
                    
                    else:
                        enviar_mensaje(chat_id, "Comando no reconocido. Usa /help")
            
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=iniciar_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)
