"""
Configuración de proyectos autorizados
Agrega aquí las rutas de los proyectos que quieres permitir
"""

import os

# Lista de proyectos autorizados (rutas absolutas o relativas)
# Descomenta y edita las rutas según tu sistema:
PROYECTOS_AUTORIZADOS = [
    # Windows:
    # r"C:\Users\tu_usuario\Documents\Proyectos\mi_app_flask",
    # r"D:\Desarrollo\juego_godot",
    # r"C:\Users\tu_usuario\AndroidStudioProjects\MiApp",

    # Linux/Mac:
    # "/home/usuario/proyectos/mi_app",
    # "/home/usuario/AndroidStudioProjects/MiApp",

    # Ruta del proyecto actual (para pruebas)
    os.path.dirname(os.path.abspath(__file__)),
]

# Extensiones permitidas por lenguaje
EXTENSIONES_PERMITIDAS = {
    'Python':    ['.py'],
    'GD Script': ['.gd'],
    'Java':      ['.java'],
    'Kotlin':    ['.kt', '.kts'],
    'XML':       ['.xml'],
}


def ruta_autorizada(ruta):
    """Verifica si una ruta está dentro de algún proyecto autorizado"""
    ruta_abs = os.path.abspath(ruta)
    for proyecto in PROYECTOS_AUTORIZADOS:
        proyecto_abs = os.path.abspath(proyecto)
        if ruta_abs.startswith(proyecto_abs):
            return True
    return False


def obtener_lenguaje_por_extension(archivo):
    """Determina el lenguaje basado en la extensión del archivo"""
    _, ext = os.path.splitext(archivo)
    ext = ext.lower()

    for lenguaje, extensiones in EXTENSIONES_PERMITIDAS.items():
        if ext in extensiones:
            return lenguaje

    return None