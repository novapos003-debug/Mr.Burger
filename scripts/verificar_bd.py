"""Comprueba la base de datos local sin modificar nada. La usa scripts/preparar_sistema.bat.

Códigos de salida:
    0  la base existe y tiene las tablas del sistema
    2  PostgreSQL responde, pero la base "restaurante" todavía no está creada
    3  no se pudo comprobar (PostgreSQL apagado, falta un componente, otro error)

Solo el código 2 permite crear la base: ante la duda no se toca una base que puede tener datos.
"""
import sys

DSN = dict(host="127.0.0.1", port=5432, dbname="restaurante", user="restaurante", password="restaurante_dev", connect_timeout=5)


def main() -> int:
    try:
        import psycopg2
    except ImportError:
        print("    [ERROR] Falta el componente psycopg2 (no se pudo instalar). Revisa el internet.")
        return 3

    try:
        conn = psycopg2.connect(**DSN)
    except Exception as e:
        texto = str(e).lower()
        # PostgreSQL contesta, pero falta la base o su usuario: instalación nueva
        if "does not exist" in texto or "no existe" in texto or "password authentication failed" in texto or "autentific" in texto:
            print('    [FALTA] PostgreSQL esta encendido, pero no existe la base "restaurante".')
            return 2
        print("    [ERROR] PostgreSQL no responde en este computador (puerto 5432).")
        print(f"            Detalle: {str(e).strip().splitlines()[0][:150]}")
        return 3

    try:
        conn.set_session(readonly=True, autocommit=True)
        cur = conn.cursor()
        cur.execute("select to_regclass('public.producto') is not null")
        if not cur.fetchone()[0]:
            print('    [FALTA] La base "restaurante" existe pero esta vacia.')
            return 2
        cur.execute("select (select count(*) from producto), (select count(*) from pedido)")
        productos, pedidos = cur.fetchone()
        print(f"    [OK] Base de datos lista: {productos} productos, {pedidos} pedidos.")
        return 0
    except Exception as e:
        print(f"    [ERROR] No se pudo leer la base: {str(e).strip().splitlines()[0][:150]}")
        return 3
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
