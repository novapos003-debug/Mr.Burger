import http.server
import socketserver
import os
import sys

PORT = 5173
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)

    def do_GET(self):
        # Resolver ruta en disco
        path = self.translate_path(self.path)
        # Si el archivo no existe o es un directorio, servir index.html (soporte SPA)
        if not os.path.exists(path) or os.path.isdir(path):
            index_path = os.path.join(DIST_DIR, "index.html")
            if os.path.exists(index_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(index_path, "rb") as f:
                    self.wfile.write(f.read())
                return
        return super().do_GET()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        # Silenciar logs para máximo rendimiento en PCs lentas
        pass

if __name__ == "__main__":
    if not os.path.exists(DIST_DIR):
        print(f"Error: No existe el directorio compilado: {DIST_DIR}")
        sys.exit(1)
    # Reutilizar puerto para evitar errores de socket ocupado al reiniciar
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), SPAHandler) as httpd:
        print(f"Frontend servido en http://0.0.0.0:{PORT} desde {DIST_DIR}")
        httpd.serve_forever()
