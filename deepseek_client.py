"""
CLIENTE PARA DEEPSEEK - VERSIÓN MODIFICADA
Adaptado para trabajar con la interfaz de modificación de archivos
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class DeepSeekClient:
    def __init__(self):
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

        # Prompt específico para modificación de código
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