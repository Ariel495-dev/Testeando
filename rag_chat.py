"""
Sistema RAG simplificado - No requiere tiktoken
"""

import os
import requests
from dotenv import load_dotenv
import json
from pathlib import Path
import re

# Cargar API key
load_dotenv()

class RAGChatSimple:
    def __init__(self, project_path=None):
        """Inicializa el sistema RAG"""
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("No se encontró DEEPSEEK_API_KEY en .env")

        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.project_path = project_path or os.getcwd()
        self.project_files = {}
        self.project_context = ""
        self.conversacion = []

        print(f"✅ Cliente DeepSeek inicializado")
        print(f"📂 Ruta del proyecto: {self.project_path}")

    def contar_caracteres(self, texto):
        """Cuenta caracteres como aproximación de tokens"""
        return len(texto)

    def cargar_archivos_proyecto(self, extensiones=None, max_caracteres=10000):
        """
        Carga archivos del proyecto con límite de caracteres
        extensiones: lista de extensiones a incluir
        max_caracteres: límite total de caracteres para el contexto
        """
        if extensiones is None:
            extensiones = ['.py', '.html', '.css', '.js', '.txt', '.md', '.json']

        # Extensiones prioritarias (se cargarán primero)
        prioritarias = ['.py', '.js', '.html']  # Archivos de código principales

        print(f"\n📖 Leyendo archivos del proyecto...")

        # Primero, recopilar todos los archivos
        archivos_encontrados = []
        for root, dirs, files in os.walk(self.project_path):
            # Ignorar carpetas innecesarias
            dirs[:] = [d for d in dirs if not d.startswith('.') and
                      d not in ('__pycache__', 'node_modules', 'venv', 'env', '.git', '.venv')]

            for file in files:
                if any(file.endswith(ext) for ext in extensiones):
                    ruta_completa = os.path.join(root, file)
                    rel_path = os.path.relpath(ruta_completa, self.project_path)

                    # Determinar prioridad
                    prioridad = 0
                    if any(file.endswith(ext) for ext in prioritarias):
                        prioridad = 1

                    archivos_encontrados.append({
                        'ruta': ruta_completa,
                        'rel_path': rel_path,
                        'nombre': file,
                        'extension': os.path.splitext(file)[1],
                        'prioridad': prioridad
                    })

        # Ordenar por prioridad (primero los prioritarios)
        archivos_encontrados.sort(key=lambda x: -x['prioridad'])

        # Cargar archivos hasta alcanzar el límite
        caracteres_totales = 0
        archivos_cargados = 0

        for archivo in archivos_encontrados:
            try:
                with open(archivo['ruta'], 'r', encoding='utf-8') as f:
                    contenido = f.read()

                caracteres = len(contenido)

                # Si pasamos el límite con este archivo, lo saltamos
                if caracteres_totales + caracteres > max_caracteres and archivos_cargados > 0:
                    continue

                # Guardar el archivo
                self.project_files[archivo['rel_path']] = {
                    'ruta': archivo['ruta'],
                    'contenido': contenido,
                    'extension': archivo['extension'],
                    'caracteres': caracteres
                }

                caracteres_totales += caracteres
                archivos_cargados += 1
                print(f"  ✓ {archivo['rel_path']} ({caracteres} caracteres)")

            except Exception as e:
                print(f"  ✗ Error leyendo {archivo['nombre']}: {e}")

        print(f"\n✅ Total: {archivos_cargados} archivos cargados")
        print(f"📊 Total caracteres: {caracteres_totales:,}")
        return archivos_cargados

    def crear_contexto(self):
        """
        Crea un string con todos los archivos para el contexto
        """
        partes = []
        for rel_path, info in self.project_files.items():
            partes.append(f"\n--- ARCHIVO: {rel_path} ---\n{info['contenido']}")

        self.project_context = "\n".join(partes)
        return self.project_context

    def preguntar_con_contexto(self, pregunta):
        """
        Hace una pregunta usando el contexto del proyecto
        """
        # Sistema prompt con instrucciones específicas
        sistema = f"""Eres un asistente experto en programación con acceso al código fuente de un proyecto.
        
Tu tarea es responder preguntas sobre el proyecto usando el contexto proporcionado.
El contexto contiene los archivos del proyecto con sus rutas.

CONTEXTO DEL PROYECTO:
{self.project_context}

INSTRUCCIONES:
1. Usa el contexto para responder preguntas específicas sobre el código
2. Si te piden modificar código, muestra los cambios exactos
3. Si te piden guardar cambios, usa el formato: GUARDAR: ruta/del/archivo.py
   seguido del contenido exacto del archivo
4. Sé específico y preciso en tus respuestas
5. Si no encuentras información en el contexto, dilo honestamente
"""

        # Preparar mensajes
        mensajes = [{"role": "system", "content": sistema}]

        # Agregar historial (últimas 5 para no exceder límites)
        for msg in self.conversacion[-6:]:
            mensajes.append(msg)

        # Agregar nueva pregunta
        mensajes.append({"role": "user", "content": pregunta})

        # Hacer la petición
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": mensajes,
            "temperature": 0.3,
            "max_tokens": 4000
        }

        print("\n⏳ Consultando a DeepSeek con contexto del proyecto...")

        try:
            respuesta = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=60
            )

            if respuesta.status_code != 200:
                return f"❌ Error {respuesta.status_code}: {respuesta.text}"

            resultado = respuesta.json()
            texto_respuesta = resultado['choices'][0]['message']['content']

            # Guardar en conversación
            self.conversacion.append({"role": "user", "content": pregunta})
            self.conversacion.append({"role": "assistant", "content": texto_respuesta})

            # Procesar si hay instrucciones de guardado
            self.procesar_guardado(texto_respuesta)

            return texto_respuesta

        except Exception as e:
            return f"❌ Error: {e}"

    def procesar_guardado(self, respuesta):
        """
        Procesa la respuesta para ver si contiene instrucciones de guardado
        """
        # Buscar patrones GUARDAR: [ruta]
        patron = r'GUARDAR:\s*([^\n]+)\n(.*?)(?=GUARDAR:|$)'
        matches = re.findall(patron, respuesta, re.DOTALL | re.IGNORECASE)

        for ruta_rel, contenido in matches:
            ruta_rel = ruta_rel.strip()
            contenido = contenido.strip()

            # Convertir a ruta absoluta
            ruta_abs = os.path.join(self.project_path, ruta_rel)

            try:
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(ruta_abs), exist_ok=True)

                # Guardar archivo
                with open(ruta_abs, 'w', encoding='utf-8') as f:
                    f.write(contenido)

                print(f"\n💾 Archivo guardado: {ruta_rel}")

                # Actualizar el contexto
                if ruta_rel in self.project_files:
                    self.project_files[ruta_rel]['contenido'] = contenido
                else:
                    self.project_files[ruta_rel] = {
                        'ruta': ruta_abs,
                        'contenido': contenido,
                        'extension': os.path.splitext(ruta_rel)[1]
                    }

            except Exception as e:
                print(f"\n❌ Error guardando {ruta_rel}: {e}")

    def chat_interactivo(self):
        """
        Modo chat interactivo con contexto del proyecto
        """
        print("\n" + "=" * 70)
        print("🤖 CHAT RAG SIMPLE - Contexto del proyecto")
        print("=" * 70)
        print("\nComandos especiales:")
        print("  /guardar - Guardar la conversación actual")
        print("  /recargar - Recargar archivos del proyecto")
        print("  /archivos - Listar archivos cargados")
        print("  /contexto - Ver resumen del contexto")
        print("  /salir - Terminar la conversación")
        print("=" * 70 + "\n")

        while True:
            try:
                pregunta = input("\n👤 Tú: ").strip()

                if not pregunta:
                    continue

                # Comandos
                if pregunta.lower() == '/salir':
                    print("👋 ¡Hasta luego!")
                    break

                elif pregunta.lower() == '/guardar':
                    self.guardar_conversacion()
                    continue

                elif pregunta.lower() == '/recargar':
                    self.project_files = {}
                    self.cargar_archivos_proyecto()
                    self.crear_contexto()
                    continue

                elif pregunta.lower() == '/archivos':
                    print(f"\n📁 Archivos cargados ({len(self.project_files)}):")
                    for i, (ruta, info) in enumerate(self.project_files.items(), 1):
                        print(f"  {i}. {ruta} ({info['caracteres']} caracteres)")
                    continue

                elif pregunta.lower() == '/contexto':
                    print(f"\n📊 Resumen del contexto:")
                    total_chars = sum(info.get('caracteres', len(info['contenido']))
                                     for info in self.project_files.values())
                    print(f"  • Archivos: {len(self.project_files)}")
                    print(f"  • Caracteres totales: {total_chars:,}")
                    continue

                # Pregunta normal
                respuesta = self.preguntar_con_contexto(pregunta)

                print(f"\n🤖 DeepSeek:\n{respuesta}")

            except KeyboardInterrupt:
                print("\n\n👋 Interrumpido por el usuario")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    def guardar_conversacion(self):
        """Guarda la conversación actual en un archivo"""
        if not self.conversacion:
            print("❌ No hay conversación para guardar")
            return

        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = f"conversacion_{timestamp}.md"

        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(f"# Conversación con DeepSeek - {timestamp}\n\n")

            for i, msg in enumerate(self.conversacion):
                rol = "👤 Usuario" if msg['role'] == 'user' else "🤖 DeepSeek"
                f.write(f"## {rol}\n\n")
                f.write(f"{msg['content']}\n\n")
                if i < len(self.conversacion) - 1:
                    f.write("---\n\n")

        print(f"\n💾 Conversación guardada en: {archivo}")

def main():
    """Función principal"""
    import sys

    # Obtener ruta del proyecto
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = os.getcwd()

    # Crear el chat RAG simplificado
    rag = RAGChatSimple(project_path)

    # Cargar archivos del proyecto
    print("\n📚 Cargando archivos del proyecto...")
    rag.cargar_archivos_proyecto(max_caracteres=15000)  # Ajustable según necesidad

    # Crear contexto
    rag.crear_contexto()

    # Iniciar chat
    rag.chat_interactivo()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        input("\nPresiona Enter para salir...")