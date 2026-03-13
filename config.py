### 2. Archivo de configuración (`config.py`):
"""
Configuración de proyectos autorizados
Agrega aquí las rutas de los proyectos que quieres permitir
"""

import os

# Lista de proyectos autorizados (rutas absolutas o relativas)
PROYECTOS_AUTORIZADOS = [
    # Ejemplos (cámbialos por tus rutas reales):
    # r"C:\Users\tu_usuario\Documents\Proyectos\mi_app_flask",
    # r"D:\Desarrollo\juego_godot",
    # r"/home/usuario/AndroidStudioProjects/MiApp",

    # Ruta del proyecto actual (para pruebas)
    os.path.dirname(os.path.abspath(__file__)),
]

# Extensiones permitidas por lenguaje
EXTENSIONES_PERMITIDAS = {
    'Python': ['.py'],
    'GD Script': ['.gd'],
    'Java': ['.java'],
    'Kotlin': ['.kt', '.kts'],
    'XML': ['.xml'],
}


# Función para verificar si una ruta está autorizada
def ruta_autorizada(ruta):
    """Verifica si una ruta está dentro de algún proyecto autorizado"""
    ruta_abs = os.path.abspath(ruta)
    for proyecto in PROYECTOS_AUTORIZADOS:
        proyecto_abs = os.path.abspath(proyecto)
        if ruta_abs.startswith(proyecto_abs):
            return True
    return False


# Función para obtener lenguaje por extensión
def obtener_lenguaje_por_extension(archivo):
    """Determina el lenguaje basado en la extensión del archivo"""
    _, ext = os.path.splitext(archivo)
    ext = ext.lower()

    for lenguaje, extensiones in EXTENSIONES_PERMITIDAS.items():
        if ext in extensiones:
            return lenguaje

    return None