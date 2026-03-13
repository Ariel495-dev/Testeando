"""
Programa básico para probar la API de DeepSeek
"""

import os
import requests
from dotenv import load_dotenv

# Cargar la API key desde el archivo .env
load_dotenv()


class DeepSeekSimple:
    def __init__(self):
        """Inicializa el cliente con la API key"""
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            print("❌ ERROR: No se encontró la API key")
            print("📝 Asegúrate de tener un archivo .env con: DEEPSEEK_API_KEY=tu-api-key")
            exit(1)

        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        print("✅ Cliente DeepSeek inicializado")

    def preguntar(self, pregunta, sistema="Eres un asistente útil y amable"):
        """
        Envía una pregunta a DeepSeek y devuelve la respuesta
        """
        # Preparar los mensajes
        mensajes = [
            {"role": "system", "content": sistema},
            {"role": "user", "content": pregunta}
        ]

        # Preparar la petición
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": mensajes,
            "temperature": 0.7,
            "max_tokens": 1000
        }

        print("\n⏳ Enviando pregunta a DeepSeek...")

        try:
            # Hacer la petición
            respuesta = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )

            # Verificar si hubo error
            if respuesta.status_code != 200:
                print(f"❌ Error {respuesta.status_code}")
                print(respuesta.text)
                return None

            # Procesar la respuesta
            resultado = respuesta.json()
            texto_respuesta = resultado['choices'][0]['message']['content']

            return texto_respuesta

        except requests.exceptions.ConnectionError:
            print("❌ Error de conexión. ¿Estás conectado a internet?")
            return None
        except requests.exceptions.Timeout:
            print("❌ Tiempo de espera agotado")
            return None
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return None


def main():
    """Función principal"""
    print("=" * 60)
    print("🤖 PRUEBA BÁSICA DE DEEPSEEK API")
    print("=" * 60)

    # Crear el cliente
    cliente = DeepSeekSimple()

    # Mostrar la API key (oculta parcialmente)
    api_key = cliente.api_key
    if api_key:
        print(f"🔑 API Key: {api_key[:5]}...{api_key[-4:] if len(api_key) > 10 else ''}")

    # Menú de opciones
    while True:
        print("\n" + "-" * 40)
        print("¿Qué quieres hacer?")
        print("1. Hacer una pregunta")
        print("2. Usar pregunta de ejemplo")
        print("3. Salir")
        print("-" * 40)

        opcion = input("Elige una opción (1-3): ").strip()

        if opcion == "1":
            # Pregunta personalizada
            print("\n📝 Escribe tu pregunta (o 'cancelar' para volver):")
            pregunta = input("> ").strip()

            if pregunta.lower() == 'cancelar':
                continue

            if not pregunta:
                print("❌ La pregunta no puede estar vacía")
                continue

            respuesta = cliente.preguntar(pregunta)

            if respuesta:
                print("\n" + "=" * 60)
                print("🤖 RESPUESTA DE DEEPSEEK:")
                print("=" * 60)
                print(respuesta)
                print("=" * 60)

        elif opcion == "2":
            # Preguntas de ejemplo
            ejemplos = [
                "¿Qué es Python y para qué sirve?",
                "Explica qué es una variable en programación",
                "Escribe una función en Python que calcule el factorial de un número",
                "¿Cuál es la diferencia entre una lista y una tupla en Python?"
            ]

            print("\n📝 Preguntas de ejemplo:")
            for i, ej in enumerate(ejemplos, 1):
                print(f"  {i}. {ej}")

            try:
                idx = int(input("\nElige un número (1-4): ")) - 1
                if 0 <= idx < len(ejemplos):
                    pregunta = ejemplos[idx]
                    print(f"\n📝 Pregunta seleccionada: {pregunta}")

                    respuesta = cliente.preguntar(pregunta)

                    if respuesta:
                        print("\n" + "=" * 60)
                        print("🤖 RESPUESTA DE DEEPSEEK:")
                        print("=" * 60)
                        print(respuesta)
                        print("=" * 60)
                else:
                    print("❌ Opción no válida")
            except ValueError:
                print("❌ Por favor, ingresa un número válido")

        elif opcion == "3":
            print("\n👋 ¡Hasta luego!")
            break

        else:
            print("❌ Opción no válida")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")