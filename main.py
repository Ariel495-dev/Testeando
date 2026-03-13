"""
Punto de entrada principal.
Ejecuta: python main.py
"""

from app import app

if __name__ == '__main__':
    print("🚀 Iniciando Modificador de Código con DeepSeek...")
    print("📡 Abre tu navegador en: http://localhost:5000")
    app.run(debug=True, port=5000)