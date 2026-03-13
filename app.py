from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from deepseek_client import DeepSeekClient
from config import PROYECTOS_AUTORIZADOS, EXTENSIONES_PERMITIDAS, ruta_autorizada, obtener_lenguaje_por_extension

app = Flask(__name__)
deepseek = DeepSeekClient()

# Configuración
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html',
                           proyectos=PROYECTOS_AUTORIZADOS,
                           extensiones=EXTENSIONES_PERMITIDAS)


@app.route('/api/listar-archivos', methods=['POST'])
def listar_archivos():
    """Lista los archivos de un directorio autorizado"""
    data = request.json
    directorio = data.get('directorio', '')

    if not directorio or not os.path.exists(directorio):
        return jsonify({'error': 'Directorio no encontrado'}), 404

    if not ruta_autorizada(directorio):
        return jsonify({'error': 'Directorio no autorizado'}), 403

    try:
        archivos = []
        for root, dirs, files in os.walk(directorio):
            # Evitar carpetas ocultas y de sistema
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                ruta_completa = os.path.join(root, file)
                lenguaje = obtener_lenguaje_por_extension(file)

                if lenguaje:  # Solo mostrar archivos con extensiones permitidas
                    archivos.append({
                        'nombre': file,
                        'ruta': ruta_completa,
                        'lenguaje': lenguaje,
                        'tamano': os.path.getsize(ruta_completa)
                    })

        return jsonify({'archivos': archivos})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/leer-archivo', methods=['POST'])
def leer_archivo():
    """Lee el contenido de un archivo autorizado"""
    data = request.json
    ruta = data.get('ruta', '')

    if not ruta or not os.path.exists(ruta):
        return jsonify({'error': 'Archivo no encontrado'}), 404

    if not ruta_autorizada(ruta):
        return jsonify({'error': 'Archivo no autorizado'}), 403

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()

        lenguaje = obtener_lenguaje_por_extension(ruta)

        return jsonify({
            'contenido': contenido,
            'lenguaje': lenguaje,
            'nombre': os.path.basename(ruta)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/modificar-archivo', methods=['POST'])
def modificar_archivo():
    """Modifica un archivo usando DeepSeek"""
    data = request.json
    ruta = data.get('ruta', '')
    instrucciones = data.get('instrucciones', '')
    accion = data.get('accion', 'modificar')  # 'modificar' o 'generar'

    if not ruta or not os.path.exists(ruta):
        return jsonify({'error': 'Archivo no encontrado'}), 404

    if not ruta_autorizada(ruta):
        return jsonify({'error': 'Archivo no autorizado'}), 403

    try:
        # Leer el archivo original
        with open(ruta, 'r', encoding='utf-8') as f:
            codigo_original = f.read()

        lenguaje = obtener_lenguaje_por_extension(ruta)

        if accion == 'generar':
            # Generar código nuevo
            codigo_modificado = deepseek.generar_nuevo_codigo(instrucciones, lenguaje)
        else:
            # Modificar código existente
            codigo_modificado = deepseek.modificar_codigo(codigo_original, instrucciones, lenguaje)

        # Verificar si hubo error
        if codigo_modificado.startswith('❌'):
            return jsonify({'error': codigo_modificado}), 500

        return jsonify({
            'codigo_original': codigo_original,
            'codigo_modificado': codigo_modificado,
            'lenguaje': lenguaje
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/guardar-archivo', methods=['POST'])
def guardar_archivo():
    """Guarda los cambios en un archivo"""
    data = request.json
    ruta = data.get('ruta', '')
    contenido = data.get('contenido', '')

    if not ruta:
        return jsonify({'error': 'Ruta no especificada'}), 400

    if not ruta_autorizada(ruta):
        return jsonify({'error': 'Archivo no autorizado'}), 403

    try:
        # Crear backup antes de guardar
        if os.path.exists(ruta):
            backup_ruta = ruta + '.backup'
            import shutil
            shutil.copy2(ruta, backup_ruta)

        # Guardar el archivo
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)

        return jsonify({'success': True, 'mensaje': 'Archivo guardado correctamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crear-archivo', methods=['POST'])
def crear_archivo():
    """Crea un nuevo archivo en el proyecto"""
    data = request.json
    directorio = data.get('directorio', '')
    nombre = data.get('nombre', '')
    contenido = data.get('contenido', '')

    if not directorio or not nombre:
        return jsonify({'error': 'Directorio y nombre requeridos'}), 400

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


if __name__ == '__main__':
    app.run(debug=True, port=5000)