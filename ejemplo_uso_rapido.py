"""
Ejemplo rápido de uso del sistema RAG - Versión simplificada
"""

# Cambiamos la importación a la versión simplificada
import rag_chat
import os

def main():
    print("=" * 60)
    print("🚀 EJEMPLO RÁPIDO - Chat con contexto del proyecto")
    print("=" * 60)

    # Inicializar RAG con la carpeta actual
    print(f"\n📂 Carpeta actual: {os.getcwd()}")
    rag = rag_chat(os.getcwd())

    # Cargar archivos del proyecto
    print("\n📚 Cargando archivos del proyecto...")
    rag.cargar_archivos_proyecto(
        extensiones=['.py', '.html', '.css', '.txt', '.md', '.json'],
        max_caracteres=8000  # Límite de caracteres para el contexto
    )

    # Crear contexto
    rag.crear_contexto()

    # Pregunta 1: Sobre los archivos del proyecto
    print("\n" + "-" * 60)
    pregunta1 = "¿Qué archivos Python hay en el proyecto y qué hace cada uno?"
    print(f"📝 Pregunta 1: {pregunta1}")

    respuesta1 = rag.preguntar_con_contexto(pregunta1)
    print(f"\n🤖 Respuesta 1:\n{respuesta1}")

    # Pregunta 2: Generar código
    print("\n" + "-" * 60)
    pregunta2 = "Crea una función en Python que lea todos los archivos .txt de una carpeta"
    print(f"📝 Pregunta 2: {pregunta2}")

    respuesta2 = rag.preguntar_con_contexto(pregunta2)
    print(f"\n🤖 Respuesta 2:\n{respuesta2}")

    # Pregunta 3: Análisis del proyecto (opcional)
    print("\n" + "-" * 60)
    pregunta3 = "Haz un resumen de la estructura de este proyecto"
    print(f"📝 Pregunta 3: {pregunta3}")

    respuesta3 = rag.preguntar_con_contexto(pregunta3)
    print(f"\n🤖 Respuesta 3:\n{respuesta3}")

    print("\n" + "=" * 60)
    print("✅ Ejemplo completado")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Ejemplo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en el ejemplo: {e}")
        import traceback
        traceback.print_exc()