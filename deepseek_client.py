"""
CLIENTE BÁSICO PARA DEEPSEEK
Este archivo te permite usar DeepSeek desde PyCharm
"""

import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class DeepSeekClient:
    """
    Cliente simple para conectar con DeepSeek API
    """

    def __init__(self):
        # Obtener API key del archivo .env
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("""
            ⚠️  NO SE ENCONTRÓ LA API KEY
            Crea un archivo .env con:
            DEEPSEEK_API_KEY=sk-tu-api-key-aqui
            """)

        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        print("✅ Cliente DeepSeek inicializado correctamente")

    def preguntar(self, pregunta, sistema="Eres un asistente útil"):
        """
        Envía una pregunta a DeepSeek y devuelve la respuesta

        Args:
            pregunta (str): Lo que quieres preguntar
            sistema (str): Personalidad del asistente

        Returns:
            str: La respuesta de DeepSeek
        """

        # Preparar los mensajes
        mensajes = [
            {"role": "system", "content": sistema},
            {"role": "user", "content": pregunta}
        ]

        # Configurar headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Configurar el cuerpo de la petición
        data = {
            "model": "deepseek-chat",
            "messages": mensajes,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            print(f"\n📤 Enviando pregunta: {pregunta[:50]}...")

            # Hacer la petición
            respuesta = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )

            # Verificar si hubo error
            if respuesta.status_code != 200:
                return f"❌ Error {respuesta.status_code}: {respuesta.text}"

            # Extraer la respuesta
            resultado = respuesta.json()
            texto = resultado['choices'][0]['message']['content']

            print(f"📥 Respuesta recibida ({len(texto)} caracteres)")
            return texto

        except requests.exceptions.ConnectionError:
            return "❌ Error de conexión. ¿Estás conectado a internet?"
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"

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
            # Obtener pregunta del usuario
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

            # Preparar mensajes con historial
            mensajes = [{"role": "system", "content": personalidad}]
            mensajes.extend(historial[-5:])  # Últimos 5 mensajes
            mensajes.append({"role": "user", "content": pregunta})

            # Llamar a la API
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

                    # Guardar en historial
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

        print("\n¿Qué quieres hacer?")
        print("1. Pregunta única")
        print("2. Chat interactivo")

        opcion = input("\nElige 1 o 2: ").strip()

        if opcion == "1":
            # Modo pregunta única
            pregunta = input("\n📝 Escribe tu pregunta: ")
            respuesta = cliente.preguntar(pregunta)
            print(f"\n🤖 Respuesta:\n{respuesta}")

        elif opcion == "2":
            # Modo chat
            cliente.chat_interactivo()

        else:
            print("❌ Opción no válida")

    except Exception as e:
        print(f"❌ Error: {e}")