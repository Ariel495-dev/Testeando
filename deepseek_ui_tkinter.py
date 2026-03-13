"""
Interfaz gráfica con Tkinter para DeepSeek + Contexto
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import threading
import requests
from dotenv import load_dotenv
import datetime
import re

# Importar tu generador de contexto
from contexto import GitIngestSinEmojis

load_dotenv()

class DeepSeekUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek - Asistente con Contexto")
        self.root.geometry("1200x700")

        # Variables
        self.api_key = os.getenv('DEEPSEEK_API_KEY', '')
        self.contexto_actual = ""
        self.archivos_seleccionados = []
        self.conversacion = []
        self.proyecto_actual = None
        self.max_tokens_limit = 130000  # Límite seguro para DeepSeek (131072 es el máximo)

        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz"""
        # Menú principal
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir proyecto", command=self.abrir_proyecto)
        file_menu.add_command(label="Generar contexto", command=self.generar_contexto)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.acerca_de)

        # Panel principal dividido
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel izquierdo - Contexto
        left_frame = ttk.Frame(main_panel)
        main_panel.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Contexto del Proyecto", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)

        # Botones para contexto
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Seleccionar carpeta", command=self.abrir_proyecto).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Generar contexto", command=self.generar_contexto).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Limpiar", command=self.limpiar_contexto).pack(side=tk.LEFT, padx=2)

        # Control de límite de contexto
        limit_frame = ttk.Frame(left_frame)
        limit_frame.pack(fill=tk.X, pady=5)
        ttk.Label(limit_frame, text="Límite contexto (tokens):").pack(side=tk.LEFT)
        self.context_limit_var = tk.StringVar(value="100000")
        ttk.Spinbox(limit_frame, from_=10000, to=130000, increment=10000,
                   textvariable=self.context_limit_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(limit_frame, text="(máx 131072)").pack(side=tk.LEFT)

        # Checkbox para truncar automáticamente
        self.truncate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_frame, text="Truncar contexto automáticamente",
                       variable=self.truncate_var).pack(anchor=tk.W, pady=2)

        # Árbol de archivos
        self.tree_frame = ttk.Frame(left_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(self.tree_frame, columns=('size',), show='tree')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_tree = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_tree.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll_tree.set)

        # Panel central - Chat
        center_frame = ttk.Frame(main_panel)
        main_panel.add(center_frame, weight=2)

        ttk.Label(center_frame, text="Chat con DeepSeek", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)

        # Área de chat
        self.chat_area = scrolledtext.ScrolledText(center_frame, wrap=tk.WORD, font=('Consolas', 10))
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=5)
        self.chat_area.config(state=tk.DISABLED)

        # Configurar tags para colores
        self.chat_area.tag_config('user', foreground='blue')
        self.chat_area.tag_config('bot', foreground='green')
        self.chat_area.tag_config('system', foreground='red')

        # Entrada de mensaje
        input_frame = ttk.Frame(center_frame)
        input_frame.pack(fill=tk.X, pady=5)

        self.message_input = tk.Text(input_frame, height=3, font=('Arial', 10))
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Bind Enter para enviar (Shift+Enter para nueva línea)
        self.message_input.bind('<Return>', self.enviar_mensaje_event)
        self.message_input.bind('<Shift-Return>', lambda e: None)

        btn_send = ttk.Button(input_frame, text="Enviar", command=self.enviar_mensaje)
        btn_send.pack(side=tk.RIGHT, padx=2)

        # Panel derecho - Configuración
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=1)

        ttk.Label(right_frame, text="Configuración", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)

        # API Key
        ttk.Label(right_frame, text="API Key:").pack(anchor=tk.W, pady=(10, 0))
        self.api_entry = ttk.Entry(right_frame, width=40, show="*")
        self.api_entry.pack(fill=tk.X, pady=5)
        self.api_entry.insert(0, self.api_key)

        # Modelo
        ttk.Label(right_frame, text="Modelo:").pack(anchor=tk.W, pady=(10, 0))
        self.model_combo = ttk.Combobox(right_frame, values=['deepseek-chat', 'deepseek-coder'], state='readonly')
        self.model_combo.pack(fill=tk.X, pady=5)
        self.model_combo.set('deepseek-chat')

        # Temperatura
        ttk.Label(right_frame, text="Temperatura:").pack(anchor=tk.W, pady=(10, 0))
        self.temp_scale = ttk.Scale(right_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL)
        self.temp_scale.set(0.3)
        self.temp_scale.pack(fill=tk.X, pady=5)

        # Max tokens (para la respuesta, no para el contexto)
        ttk.Label(right_frame, text="Max tokens respuesta:").pack(anchor=tk.W, pady=(10, 0))
        self.tokens_var = tk.StringVar(value="4000")
        ttk.Spinbox(right_frame, from_=100, to=8000, textvariable=self.tokens_var).pack(fill=tk.X, pady=5)

        # Sistema prompt
        ttk.Label(right_frame, text="System prompt:").pack(anchor=tk.W, pady=(10, 0))
        self.system_text = tk.Text(right_frame, height=5, font=('Arial', 9))
        self.system_text.pack(fill=tk.X, pady=5)
        self.system_text.insert('1.0', "Eres un asistente experto en programación. Si generas código, incluye el marcador GUARDAR: seguido de la ruta del archivo y el contenido completo para que pueda guardarse automáticamente.")

        # Botones de acción
        ttk.Button(right_frame, text="Guardar conversación", command=self.guardar_conversacion).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="Limpiar chat", command=self.limpiar_chat).pack(fill=tk.X, pady=2)

        # Barra de estado
        self.status_bar = ttk.Label(self.root, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def abrir_proyecto(self):
        """Abre un selector de carpeta"""
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.proyecto_actual = carpeta
            self.status_bar.config(text=f"Proyecto: {carpeta}")
            self.cargar_arbol_archivos(carpeta)

    def cargar_arbol_archivos(self, carpeta):
        """Carga el árbol de archivos"""
        self.tree.delete(*self.tree.get_children())

        # Extensiones de texto comunes
        text_exts = {'.py', '.js', '.html', '.css', '.json', '.md', '.txt',
                     '.yml', '.yaml', '.toml', '.ini', '.env', '.gitignore'}
        archivos_especiales = {'Dockerfile', 'Makefile', 'requirements.txt'}

        for root, dirs, files in os.walk(carpeta):
            # Excluir carpetas innecesarias
            dirs[:] = [d for d in dirs if d not in {'__pycache__', 'venv', 'env', 'node_modules', '.git', '.idea'}]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in text_exts or file in archivos_especiales:
                    ruta = os.path.join(root, file)
                    rel = os.path.relpath(ruta, carpeta)
                    try:
                        tamaño = os.path.getsize(ruta)
                        self.tree.insert('', 'end', text=rel, values=(f"{tamaño/1024:.1f} KB",))
                    except:
                        pass

    def generar_contexto(self):
        """Genera el contexto del proyecto"""
        if not self.proyecto_actual:
            messagebox.showwarning("Advertencia", "Primero selecciona una carpeta de proyecto")
            return

        try:
            self.status_bar.config(text="Generando contexto...")
            self.root.update()

            # Usar tu generador
            g = GitIngestSinEmojis(self.proyecto_actual)
            g.scan()
            g.save("temp_contexto.txt")

            with open("temp_contexto.txt", 'r', encoding='utf-8') as f:
                self.contexto_actual = f.read()

            # Mostrar tamaño del contexto
            chars = len(self.contexto_actual)
            tokens_estimados = chars // 4
            self.status_bar.config(text=f"Contexto generado: {chars/1024:.1f} KB (~{tokens_estimados:,} tokens)")

            # Advertir si es demasiado grande
            if tokens_estimados > self.max_tokens_limit:
                messagebox.showwarning("Contexto grande",
                    f"El contexto tiene ~{tokens_estimados:,} tokens estimados.\n"
                    f"El límite de DeepSeek es 131,072 tokens.\n"
                    f"Se truncará automáticamente al enviar.")
            else:
                messagebox.showinfo("Éxito", f"Contexto generado: {chars/1024:.1f} KB")

        except Exception as e:
            messagebox.showerror("Error", f"Error generando contexto: {e}")
            self.status_bar.config(text="Error generando contexto")

    def enviar_mensaje_event(self, event):
        """Maneja el evento Enter"""
        self.enviar_mensaje()
        return 'break'

    def enviar_mensaje(self):
        """Envía un mensaje a DeepSeek"""
        mensaje = self.message_input.get('1.0', tk.END).strip()
        if not mensaje:
            return

        # Mostrar mensaje en el chat
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"\nTú: {mensaje}\n", 'user')
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

        # Limpiar input
        self.message_input.delete('1.0', tk.END)

        # Enviar en hilo separado
        threading.Thread(target=self._enviar_a_api, args=(mensaje,), daemon=True).start()

    def _enviar_a_api(self, mensaje):
        """Envía a la API en segundo plano"""
        try:
            self.root.after(0, lambda: self.status_bar.config(text="Enviando..."))

            api_key = self.api_entry.get() or self.api_key
            if not api_key:
                raise ValueError("API Key no configurada")

            # Limitar contexto si es necesario
            contexto_para_enviar = self.contexto_actual
            if self.truncate_var.get() and contexto_para_enviar:
                # Calcular tokens estimados (aprox 4 caracteres por token)
                max_chars = int(self.context_limit_var.get()) * 4
                if len(contexto_para_enviar) > max_chars:
                    chars_original = len(contexto_para_enviar)
                    contexto_para_enviar = contexto_para_enviar[:max_chars] + f"\n\n[Contexto truncado: originalmente {chars_original} caracteres, ~{chars_original//4} tokens]"
                    print(f"Contexto truncado de {chars_original} a {max_chars} caracteres")

            # Preparar prompt con contexto
            if contexto_para_enviar:
                prompt = f"""Contexto del proyecto:
{contexto_para_enviar}

Pregunta: {mensaje}

Responde basándote en el contexto proporcionado. Si generas código, incluye el marcador GUARDAR: seguido de la ruta del archivo y el contenido completo."""
            else:
                prompt = mensaje

            # Llamar a la API
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_combo.get(),
                    "messages": [
                        {"role": "system", "content": self.system_text.get('1.0', tk.END).strip()},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": self.temp_scale.get(),
                    "max_tokens": int(self.tokens_var.get())
                },
                timeout=120
            )

            if response.status_code == 200:
                respuesta = response.json()['choices'][0]['message']['content']

                # Guardar en conversación
                self.conversacion.append({"role": "user", "content": mensaje})
                self.conversacion.append({"role": "assistant", "content": respuesta})

                # Procesar guardado automático
                archivos_guardados = self.procesar_guardado(respuesta)

                # Mostrar respuesta
                self.root.after(0, lambda: self._mostrar_respuesta(respuesta, archivos_guardados))
                self.root.after(0, lambda: self.status_bar.config(text="Listo"))
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                self.root.after(0, lambda: messagebox.showerror("Error API", error_msg))
                self.root.after(0, lambda: self.status_bar.config(text="Error en API"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self.status_bar.config(text="Error"))

    def procesar_guardado(self, respuesta):
        """Procesa la respuesta para ver si contiene instrucciones de guardado"""
        # Buscar patrones GUARDAR: [ruta]
        patron = r'GUARDAR:\s*([^\n]+)\n(.*?)(?=GUARDAR:|$)'
        matches = re.findall(patron, respuesta, re.DOTALL | re.IGNORECASE)

        archivos_guardados = []

        for ruta_rel, contenido in matches:
            ruta_rel = ruta_rel.strip()
            contenido = contenido.strip()

            # Determinar la ruta absoluta
            if self.proyecto_actual:
                ruta_abs = os.path.join(self.proyecto_actual, ruta_rel)
            else:
                ruta_abs = os.path.join(os.getcwd(), ruta_rel)

            try:
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(ruta_abs), exist_ok=True)

                # Guardar archivo
                with open(ruta_abs, 'w', encoding='utf-8') as f:
                    f.write(contenido)

                archivos_guardados.append(ruta_rel)
                print(f"Archivo guardado: {ruta_rel}")

                # Actualizar el árbol si el archivo está en el proyecto actual
                if self.proyecto_actual and ruta_abs.startswith(self.proyecto_actual):
                    self.root.after(0, lambda: self.actualizar_arbol_archivo(ruta_rel))

            except Exception as e:
                print(f"Error guardando {ruta_rel}: {e}")

        return archivos_guardados

    def actualizar_arbol_archivo(self, ruta_rel):
        """Actualiza el árbol para mostrar un archivo nuevo"""
        # Esta es una implementación simple - podrías mejorarla
        self.cargar_arbol_archivos(self.proyecto_actual)

    def _mostrar_respuesta(self, respuesta, archivos_guardados=None):
        """Muestra la respuesta en el chat"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"\nDeepSeek: {respuesta}\n", 'bot')

        # Si se guardaron archivos, mostrar mensaje
        if archivos_guardados:
            self.chat_area.insert(tk.END, f"\n[Archivos guardados automáticamente: {', '.join(archivos_guardados)}]\n", 'system')

        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def limpiar_contexto(self):
        """Limpia el contexto actual"""
        self.contexto_actual = ""
        self.tree.delete(*self.tree.get_children())
        self.proyecto_actual = None
        self.status_bar.config(text="Contexto limpiado")

    def limpiar_chat(self):
        """Limpia el área de chat"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete('1.0', tk.END)
        self.chat_area.config(state=tk.DISABLED)
        self.conversacion = []

    def guardar_conversacion(self):
        """Guarda la conversación en un archivo"""
        if not self.chat_area.get('1.0', tk.END).strip():
            messagebox.showwarning("Advertencia", "No hay conversación para guardar")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.chat_area.get('1.0', tk.END))
            self.status_bar.config(text=f"Conversación guardada en {filename}")

    def acerca_de(self):
        """Muestra información de la aplicación"""
        messagebox.showinfo(
            "Acerca de",
            "DeepSeek UI con Contexto\n\n"
            "Versión: 2.0\n"
            "Integración con DeepSeek API\n"
            "Generador de contexto para proyectos\n"
            "Guardado automático de archivos con marcador GUARDAR:"
        )

def main():
    root = tk.Tk()
    app = DeepSeekUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()