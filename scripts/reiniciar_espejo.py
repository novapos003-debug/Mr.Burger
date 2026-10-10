"""Reinicia el espejo de la nube para reconstruirlo desde ESTA caja.

Cuándo usarlo: una sola vez, al instalar (o reinstalar) la caja del restaurante. Vacía los
datos de negocio de la nube; al terminar, el backend local detecta que el espejo es nuevo y
le envía la base completa. En uno o dos minutos la nube queda idéntica a la caja.

Uso (desde la carpeta del proyecto, con el sistema ya configurado):
    python scripts/reiniciar_espejo.py

Lee CLOUD_SYNC_URL y CLOUD_SYNC_TOKEN del archivo .env. Pide confirmación escrita.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FRASE = "REINICIAR ESPEJO"


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
    url = env.get("CLOUD_SYNC_URL", "").rstrip("/")
    token = env.get("CLOUD_SYNC_TOKEN", "")
    if not url or not token:
        print("Falta CLOUD_SYNC_URL o CLOUD_SYNC_TOKEN en el archivo .env.")
        print("Ejecuta primero configurar_sincronizacion_windows.bat")
        return 1

    print("=" * 62)
    print("  REINICIAR EL ESPEJO EN LA NUBE")
    print("=" * 62)
    print(f"  Nube: {url}")
    print()
    print("  Se BORRARÁN de la nube todos los datos de negocio (ventas,")
    print("  inventario, catálogo y usuarios). Los datos de ESTA caja no")
    print("  se tocan: se copiarán completos a la nube a continuación.")
    print()
    if input(f'  Para continuar escribe exactamente  {FRASE}  : ').strip() != FRASE:
        print("\n  Cancelado. No se cambió nada.")
        return 1

    peticion = urllib.request.Request(
        f"{url}/sync/reiniciar-espejo",
        data=json.dumps({"confirmar": FRASE}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Sync-Token": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=120) as resp:
            datos = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"\n  La nube rechazó la solicitud (HTTP {e.code}): {e.read().decode('utf-8', 'ignore')[:300]}")
        return 1
    except Exception as e:  # sin internet, nube dormida, etc.
        print(f"\n  No se pudo contactar la nube: {e}")
        return 1

    print(f"\n  Espejo reiniciado ({datos.get('tablas_vaciadas')} tablas).")
    print("  Si el sistema está abierto, empezará a copiar la base en segundos.")
    print("  Puedes ver el avance en el indicador de sincronización de la caja.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
