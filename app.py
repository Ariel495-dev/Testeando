from flask import Flask, render_template, request, jsonify
import os
import shutil
from deepseek_client import DeepSeekClient
from config import PROYECTOS_AUTORIZADOS, EXTENSIONES_PERMITIDAS, ruta_autorizada, obtener_lenguaje_por_extension

app = Flask(__name__, template_folder='template')  # ← apunta a tu carpeta existente
deepseek = DeepSeekClient()

app.config['SECRET_KEY'] = 'cambia-esta-clave-secreta'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB


# ─────────────────────────────────────────────
#  PÁGINAS
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Página principal"""
    return render_template(
        'index.html',                               # ← nombre real de tu archivo
        proyectos=PROYECTOS_AUTORIZADOS,
        extensiones=list(EXTENSIONES_PERMITIDAS.keys())
    )


# ─────────────────────────────────────────────
#  API – ARCHIVOS
# ─────────────────────────────────────────────

@app.route('/api/listar-archivos', methods=['POST'])
def listar_archivos():
    """Lista los archivos de un directorio autorizado"""
    data = request.json or {}
    directorio = data.get('directorio', '')

    if not directorio or not os.path.exists(directorio):
        return jsonify({'error': 'Directorio no encontrado'}), 404

    if not ruta_autorizada(directorio):
        return jsonify({'error': 'Directorio no autorizado'}), 403

    try:
        archivos = []
        for root, dirs, files in os.walk(directorio):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules', '.git')]

            for file in files:
                ruta_completa = os.path.join(root, file)
                lenguaje = obtener_lenguaje_por_extension(file)

                if lenguaje:
                    archivos.append({
                        'nombre': file,
                        'ruta':   ruta_completa,
                        'lenguaje': lenguaje,
                        'tamano': os.path.getsize(ruta_completa)
                    })

        return jsonify({'archivos': archivos})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/leer-archivo', methods=['POST'])
def leer_archivo():
    """Lee el contenido de un archivo autorizado"""
    data = request.json or {}
    ruta = data.get('ruta', '')

    if not ruta or not os.path.exists(ruta):
        return jsonify({'error': 'Archivo no encontrado'}), 404

    if not ruta_autorizada(ruta):
        return jsonify({'error': 'Archivo no autorizado'}), 403

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()

        return jsonify({
            'contenido': contenido,
            'lenguaje': obtener_lenguaje_por_extension(ruta),
            'nombre': os.path.basename(ruta)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/guardar-archivo', methods=['POST'])
def guardar_archivo():
    """Guarda los cambios en un archivo (crea .backup antes)"""
    data = request.json or {}
    ruta = data.get('ruta', '')
    contenido = data.get('contenido', '')

    if not ruta:
        return jsonify({'error': 'Ruta no especificada'}), 400

    if not ruta_autorizada(ruta):
        return jsonify({'error': 'Archivo no autorizado'}), 403

    try:
        if os.path.exists(ruta):
            shutil.copy2(ruta, ruta + '.backup')

        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)

        return jsonify({'success': True, 'mensaje': 'Archivo guardado correctamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crear-archivo', methods=['POST'])
def crear_archivo():
    """Crea un nuevo archivo en el proyecto"""
    data = request.json or {}
    directorio = data.get('directorio', '')
    nombre     = data.get('nombre', '')
    contenido  = data.get('contenido', '')

    if not directorio or not nombre:
        return jsonify({'error': 'Directorio y nombre son requeridos'}), 400

    ruta_completa = os.path.join(directorio, nombre)

    if not ruta_autorizada(ruta_completa):
        return jsonify({'error': 'Ubicación no autorizada'}), 403

    if os.path.exists(ruta_completa):
        return jsonify({'error': 'El archivo ya existe'}), 400

    try:
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            f.write(contenido)

        return jsonify({
            'success': True,
            'ruta': ruta_completa,
            'mensaje': 'Archivo creado correctamente'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
#  API – IA
# ─────────────────────────────────────────────

@app.route('/api/modificar-archivo', methods=['POST'])
def modificar_archivo():
    """Modifica o genera código usando DeepSeek"""
    data = request.json or {}
    ruta          = data.get('ruta', '')
    instrucciones = data.get('instrucciones', '')
    accion        = data.get('accion', 'modificar')   # 'modificar' | 'generar'

    if not instrucciones:
        return jsonify({'error': 'Las instrucciones son requeridas'}), 400

    if accion == 'modificar':
        if not ruta or not os.path.exists(ruta):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        if not ruta_autorizada(ruta):
            return jsonify({'error': 'Archivo no autorizado'}), 403

    try:
        lenguaje = obtener_lenguaje_por_extension(ruta) or 'Python'

        if accion == 'generar':
            codigo_original  = ''
            codigo_resultado = deepseek.generar_nuevo_codigo(instrucciones, lenguaje)
        else:
            with open(ruta, 'r', encoding='utf-8') as f:
                codigo_original = f.read()
            codigo_resultado = deepseek.modificar_codigo(codigo_original, instrucciones, lenguaje)

        if codigo_resultado.startswith('❌'):
            return jsonify({'error': codigo_resultado}), 500

        return jsonify({
            'codigo_original':   codigo_original,
            'codigo_modificado': codigo_resultado,
            'lenguaje': lenguaje
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat directo con DeepSeek"""
    data = request.json or {}
    mensaje      = data.get('mensaje', '')
    historial    = data.get('historial', [])
    personalidad = data.get('personalidad', 'Eres un asistente útil y amable')

    if not mensaje:
        return jsonify({'error': 'El mensaje no puede estar vacío'}), 400

    try:
        mensajes = [{"role": "system", "content": personalidad}]
        mensajes.extend(historial[-10:])
        mensajes.append({"role": "user", "content": mensaje})

        import requests as req
        headers = {
            "Authorization": f"Bearer {deepseek.api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "deepseek-chat",
            "messages": mensajes,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        respuesta = req.post(deepseek.api_url, headers=headers, json=body, timeout=30)

        if respuesta.status_code != 200:
            return jsonify({'error': f'Error de API: {respuesta.status_code}'}), 500

        texto = respuesta.json()['choices'][0]['message']['content']
        return jsonify({'respuesta': texto})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)