"""Comprueba que el token de sincronización guardado en .env sea el que acepta la nube.
Solo consulta; no envía ni modifica datos. La usa scripts/preparar_sistema.bat.

Códigos de salida:
    0  el token es válido
    2  no hay token, o la nube lo rechaza (hay que pegar el correcto)
    3  no se pudo comprobar (sin internet o la nube no respondió); se intentará sola más tarde
"""
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NUBE_POR_DEFECTO = "https://mrburger-api.onrender.com"


def leer_env() -> dict[str, str]:
    valores: dict[str, str] = {}
    ruta = RAIZ / ".env"
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                clave, valor = linea.split("=", 1)
                valores[clave.strip()] = valor.strip()
    return valores


def main() -> int:
    env = leer_env()
    token = env.get("CLOUD_SYNC_TOKEN", "")
    url = (env.get("CLOUD_SYNC_URL") or NUBE_POR_DEFECTO).rstrip("/")
    if not token:
        print("    [FALTA] Este computador aun no tiene el token de la nube.")
        return 2

    # La nube gratuita se duerme: la primera respuesta puede tardar cerca de un minuto
    print("    Consultando la nube (puede tardar hasta un minuto)...")
    peticion = urllib.request.Request(
        f"{url}/sync/cambios?despues_de=2000000000&limite=1", headers={"X-Sync-Token": token}
    )
    try:
        with urllib.request.urlopen(peticion, timeout=90):
            print("    [OK] Token de sincronizacion valido.")
            return 0
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            print("    [FALTA] La nube rechaza el token guardado (es el viejo o esta mal copiado).")
            return 2
        print(f"    [AVISO] La nube respondio con un error ({e.code}). Se reintentara sola.")
        return 3
    except Exception:
        print("    [AVISO] No se pudo contactar la nube (sin internet?). La caja funciona igual")
        print("            y sincronizara sola cuando vuelva la conexion.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
