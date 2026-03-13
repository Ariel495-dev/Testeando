"""
Configuración de proyectos autorizados
"""

import os

# Proyectos que aparecen en el desplegable por defecto
PROYECTOS_AUTORIZADOS = [
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
    """
    Acepta cualquier ruta que exista en el sistema de archivos.
    Los proyectos del desplegable siguen funcionando también.
    """
    ruta_abs = os.path.abspath(ruta)

    # Verificar que la ruta (o su carpeta padre) existe
    if os.path.exists(ruta_abs):
        return True
    if os.path.exists(os.path.dirname(ruta_abs)):
        return True

    # Compatibilidad con proyectos del desplegable
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