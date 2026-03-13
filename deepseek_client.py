"""
CLIENTE PARA DEEPSEEK - VERSIÓN COMPLETA
Adaptado para trabajar con la interfaz de modificación de archivos
"""

import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class DeepSeekClient:
    """
    Cliente para conectarse a la API de DeepSeek
    Permite modificar y generar código en diferentes lenguajes
    """

    def __init__(self):
        """Inicializa el cliente con la API key desde el archivo .env"""
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("""
            ⚠️  NO SE ENCONTRÓ LA API KEY
            Crea un archivo .env con:
            DEEPSEEK_API_KEY=sk-tu-api-key-aqui
            """)

        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        print("✅ Cliente DeepSeek inicializado correctamente")

    def modificar_codigo(self, codigo_original, instrucciones, lenguaje):
        """
        Envía código a DeepSeek para modificarlo según instrucciones

        Args:
            codigo_original (str): El código a modificar
            instrucciones (str): Qué cambios hacer
            lenguaje (str): El lenguaje de programación

        Returns:
            str: El código modificado
        """
        sistema = f"""Eres un experto programador en {lenguaje}. 
        Tu tarea es modificar el código según las instrucciones del usuario.
        Devuelve SOLO el código modificado, sin explicaciones adicionales.
        Mantén la misma estructura y estilo del código original cuando sea posible.
        Asegúrate de que el código modificado sea funcional y siga las mejores prácticas."""

        mensaje_usuario = f"""
LENGUAJE: {lenguaje}

INSTRUCCIONES DE MODIFICACIÓN:
{instrucciones}

CÓDIGO ORIGINAL A MODIFICAR:
```{lenguaje}
{codigo_original}
```

Por favor, modifica el código según las instrucciones y devuelve SOLO el código resultante.
"""

        mensajes = [
            {"role": "system", "content": sistema},
            {"role": "user", "content": mensaje_usuario}
        ]

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
            codigo_modificado = resultado['choices'][0]['message']['content']

            # Limpiar la respuesta
            codigo_modificado = self._limpiar_respuesta_codigo(codigo_modificado)

            return codigo_modificado

        except requests.exceptions.ConnectionError:
            return "❌ Error de conexión. ¿Estás conectado a internet?"
        except requests.exceptions.Timeout:
            return "❌ Tiempo de espera agotado. La API tardó demasiado en responder."
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"

    def generar_nuevo_codigo(self, descripcion, lenguaje):
        """
        Genera código nuevo desde cero basado en una descripción

        Args:
            descripcion (str): Qué debe hacer el código
            lenguaje (str): El lenguaje de programación

        Returns:
            str: El código generado
        """
        sistema = f"""Eres un experto programador en {lenguaje}.
        Genera código limpio, eficiente y bien comentado basado en la descripción del usuario.
        Devuelve SOLO el código, sin explicaciones adicionales."""

        mensaje_usuario = f"""
LENGUAJE: {lenguaje}

DESCRIPCIÓN:
{descripcion}

Genera el código completo y funcional para esta tarea.
"""

        mensajes = [
            {"role": "system", "content": sistema},
            {"role": "user", "content": mensaje_usuario}
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": mensajes,
            "temperature": 0.5,
            "max_tokens": 4000
        }

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
            codigo = resultado['choices'][0]['message']['content']

            return self._limpiar_respuesta_codigo(codigo)

        except requests.exceptions.ConnectionError:
            return "❌ Error de conexión. ¿Estás conectado a internet?"
        except requests.exceptions.Timeout:
            return "❌ Tiempo de espera agotado. La API tardó demasiado en responder."
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"

    def _limpiar_respuesta_codigo(self, respuesta):
        """
        Limpia la respuesta para extraer solo el código.
        Elimina bloques de markdown si existen.
        """
        lineas = respuesta.split('\n')
        lineas_limpias = []
        dentro_bloque_codigo = False

        for linea in lineas:
            if linea.strip().startswith('```'):
                dentro_bloque_codigo = not dentro_bloque_codigo
                continue
            if dentro_bloque_codigo:
                lineas_limpias.append(linea)

        # Si no había bloques de código, devolvemos la respuesta original
        if not lineas_limpias:
            return respuesta

        return '\n'.join(lineas_limpias)

    def preguntar(self, pregunta, sistema="Eres un asistente útil"):
        """
        Envía una pregunta a DeepSeek y devuelve la respuesta

        Args:
            pregunta (str): Lo que quieres preguntar
            sistema (str): Personalidad del asistente

        Returns:
            str: La respuesta de DeepSeek
        """
        mensajes = [
            {"role": "system", "content": sistema},
            {"role": "user", "content": pregunta}
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": mensajes,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            respuesta = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )

            if respuesta.status_code != 200:
                return f"❌ Error {respuesta.status_code}: {respuesta.text}"

            resultado = respuesta.json()
            return resultado['choices'][0]['message']['content']

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def chat_interactivo(self):
        """
        Modo chat interactivo (conversación continua)
        """
        print("\n" + "=" * 50)
        print("🤖 CHAT CON DEEPSEEK (modo interactivo)")
        print("=" * 50)
        print("Comandos especiales:")
        print("  /salir  - Terminar la conversación")
        print("  /sistema - Cambiar personalidad")
        print("=" * 50 + "\n")

        historial = []
        personalidad = "Eres un asistente útil y amable"

        while True:
            pregunta = input("\n👤 Tú: ").strip()

            if pregunta.lower() == '/salir':
                print("👋 ¡Hasta luego!")
                break

            if pregunta.lower() == '/sistema':
                personalidad = input("📝 Nueva personalidad: ").strip()
                print(f"✅ Personalidad actualizada: {personalidad}")
                continue

            if not pregunta:
                continue

            mensajes = [{"role": "system", "content": personalidad}]
            mensajes.extend(historial[-5:])
            mensajes.append({"role": "user", "content": pregunta})

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": mensajes,
                "temperature": 0.7
            }

            try:
                respuesta = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=30
                )

                if respuesta.status_code == 200:
                    resultado = respuesta.json()
                    texto_respuesta = resultado['choices'][0]['message']['content']

                    print(f"\n🤖 DeepSeek: {texto_respuesta}")

                    historial.append({"role": "user", "content": pregunta})
                    historial.append({"role": "assistant", "content": texto_respuesta})
                else:
                    print(f"❌ Error: {respuesta.status_code}")

            except Exception as e:
                print(f"❌ Error: {str(e)}")


# ============================================
# PROBAR EL CLIENTE
# ============================================
if __name__ == "__main__":
    try:
        # Crear el cliente
        cliente = DeepSeekClient()

        print("\n✅ Cliente funcionando correctamente")
        print(f"🔑 API Key configurada: {cliente.api_key[:5]}...{cliente.api_key[-4:] if len(cliente.api_key) > 10 else ''}")

        print("\n¿Qué quieres hacer?")
        print("1. Probar modificación de código")
        print("2. Probar generación de código")
        print("3. Chat interactivo")
        print("4. Pregunta simple")

        opcion = input("\nElige una opción (1-4): ").strip()

        if opcion == "1":
            lenguaje = input("Lenguaje (Python/GD Script/Java/Kotlin/XML): ").strip()
            codigo = input("Pega el código a modificar (o escribe 'ejemplo' para usar código de prueba): ").strip()

            if codigo.lower() == 'ejemplo':
                if lenguaje.lower() == 'python':
                    codigo = 'def saludar(nombre):\n    print("Hola " + nombre)'
                else:
                    codigo = '// Código de ejemplo'

            instrucciones = input("¿Qué cambios quieres hacer?: ").strip()

            print("\n⏳ Procesando...")
            resultado = cliente.modificar_codigo(codigo, instrucciones, lenguaje)
            print(f"\n📝 RESULTADO:\n{resultado}")

        elif opcion == "2":
            lenguaje = input("Lenguaje (Python/GD Script/Java/Kotlin/XML): ").strip()
            descripcion = input("Describe el código que necesitas: ").strip()

            print("\n⏳ Generando...")
            resultado = cliente.generar_nuevo_codigo(descripcion, lenguaje)
            print(f"\n📝 CÓDIGO GENERADO:\n{resultado}")

        elif opcion == "3":
            cliente.chat_interactivo()

        elif opcion == "4":
            pregunta = input("\n📝 Escribe tu pregunta: ")
            respuesta = cliente.preguntar(pregunta)
            print(f"\n🤖 Respuesta:\n{respuesta}")

        else:
            print("❌ Opción no válida")

    except Exception as e:
        print(f"❌ Error: {e}")