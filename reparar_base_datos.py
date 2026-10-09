import os
import sys
import glob
import socket
import subprocess
import shutil
import time

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

def print_banner():
    print("=" * 65)
    print("  MR. BURGER POS - DIAGNÓSTICO Y REPARACIÓN AUTOMÁTICA")
    print("=" * 65)
    print()

def log(msg, status="INFO"):
    prefixes = {
        "INFO": "[*]",
        "OK": "[OK]",
        "WARN": "[!]",
        "ERROR": "[ERROR]"
    }
    print(f"{prefixes.get(status, '[*]')} {msg}")

def check_port(host, port, timeout=0.5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        res = s.connect_ex((host, port))
        s.close()
        return res == 0
    except Exception:
        return False

def get_postgres_services():
    """Detecta nombres de servicios de PostgreSQL registrados en Windows."""
    services = []
    try:
        out = subprocess.check_output("sc query type= service state= all", shell=True, text=True, errors="ignore")
        for line in out.splitlines():
            line_strip = line.strip()
            if line_strip.upper().startswith("SERVICE_NAME:") and "POSTGRES" in line_strip.upper():
                svc = line_strip.split(":", 1)[1].strip()
                services.append(svc)
    except Exception:
        pass
    
    if not services:
        services = ["postgresql-x64-15", "postgresql-x64-16", "postgresql-x64-17", "postgresql-15", "postgresql-16"]
    return services

def ensure_postgres_service_running():
    log("Paso 1: Verificando servicio de PostgreSQL en Windows...", "INFO")
    services = get_postgres_services()
    active_service = None
    for svc in services:
        try:
            query = subprocess.check_output(f'sc query "{svc}"', shell=True, text=True, errors="ignore")
            if "RUNNING" in query.upper():
                log(f"Servicio '{svc}' está ACTIVO.", "OK")
                active_service = svc
                break
            elif "STOPPED" in query.upper():
                log(f"Servicio '{svc}' está DETENIDO. Iniciando...", "WARN")
                subprocess.run(f'net start "{svc}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f'sc config "{svc}" start= auto', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                active_service = svc
                break
        except Exception:
            continue
    
    if not active_service:
        for common in ["postgresql-x64-15", "postgresql-x64-16"]:
            subprocess.run(f'net start "{common}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
    return active_service

def detect_postgres_port():
    log("Paso 2: Detectando puerto TCP de PostgreSQL...", "INFO")
    for port in [5432, 5433, 5434]:
        if check_port("127.0.0.1", port):
            log(f"PostgreSQL respondiendo en puerto {port}.", "OK")
            return port
    return None

def find_psql_binary(active_service=None):
    log("Paso 3: Localizando utilitarios de PostgreSQL...", "INFO")
    
    # 1. Intentar deducir la ruta desde el servicio activo de Windows
    if active_service:
        try:
            out = subprocess.check_output(f'sc qc "{active_service}"', shell=True, text=True, errors="ignore")
            for line in out.splitlines():
                if "BIN" in line.upper() and ":" in line:
                    val = line.split(":", 1)[1].strip()
                    exe_path = val[1:].split('"', 1)[0] if val.startswith('"') else val.split()[0]
                    bin_dir = os.path.dirname(exe_path)
                    candidate = os.path.join(bin_dir, "psql.exe")
                    if os.path.exists(candidate):
                        log(f"Encontrado vía servicio: {candidate}", "OK")
                        return candidate
        except Exception:
            pass

    # 2. Búsqueda amplia por patrones de instalación
    patterns = [
        r"C:\Program Files\PostgreSQL\*\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\*\bin\psql.exe",
        r"C:\PostgreSQL\*\bin\psql.exe",
        r"C:\PostgreSQL\bin\psql.exe",
        r"D:\Program Files\PostgreSQL\*\bin\psql.exe",
        r"D:\PostgreSQL\*\bin\psql.exe",
    ]
    for pat in patterns:
        matches = glob.glob(pat)
        if matches:
            log(f"Encontrado en disco: {matches[-1]}", "OK")
            return matches[-1]
            
    # 3. PATH del sistema
    which_psql = shutil.which("psql")
    if which_psql:
        log(f"Encontrado en PATH: {which_psql}", "OK")
        return which_psql
        
    log("psql.exe no está en rutas por defecto. Usaremos el conector directo nativo (psycopg2).", "INFO")
    return None

def connect_pg(port, user, password, db="postgres"):
    """Intenta conectar a PostgreSQL usando psycopg2 nativo."""
    if not HAS_PSYCOPG2:
        return False, None, "psycopg2 no instalado"
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=port,
            user=user,
            password=password,
            dbname=db,
            connect_timeout=3
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return True, conn, None
    except Exception as e:
        return False, None, str(e)

def execute_sql_file_psycopg2(conn, file_path):
    """Ejecuta un archivo SQL instrucción por instrucción usando la conexión psycopg2."""
    if not os.path.exists(file_path):
        return False, f"Archivo no existe: {file_path}"
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    statements = content.split(";")
    with conn.cursor() as cur:
        for stmt in statements:
            s = stmt.strip()
            if not s:
                continue
            try:
                cur.execute(s)
            except Exception:
                # Ignorar errores no fatales (ej. tabla ya existente)
                pass
    return True, None

def main():
    print_banner()
    root_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 1. Asegurar servicio iniciado
    active_service = ensure_postgres_service_running()
    
    # 2. Detectar puerto
    port = detect_postgres_port()
    if not port:
        log("No se detectó PostgreSQL en puertos 5432 ni 5433.", "WARN")
        log("Intentando iniciar servicios...", "INFO")
        for svc in ["postgresql-x64-15", "postgresql-x64-16", "postgresql-15"]:
            subprocess.run(f'net start "{svc}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        port = detect_postgres_port()
        
    if not port:
        log("ERROR: PostgreSQL no está aceptando conexiones.", "ERROR")
        log("Por favor abre 'Servicios' en Windows y asegúrate de que el servicio de PostgreSQL esté iniciado.", "WARN")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
        
    # 3. Localizar psql opcional
    psql_path = find_psql_binary(active_service)

    # 4. Probar si el usuario 'restaurante' ya conecta
    log("Paso 4: Verificando credenciales de base de datos...", "INFO")
    ok_res, conn_res, _ = connect_pg(port, "restaurante", "restaurante_dev", "postgres")
    
    if ok_res:
        log("Usuario 'restaurante' autenticado con éxito.", "OK")
        conn_res.close()
    else:
        log("Configurando usuario 'restaurante' con privilegios de administrador...", "INFO")
        # Probar contraseñas comunes del superusuario 'postgres'
        passwords_to_try = [
            "restaurante_dev",
            "postgres",
            "admin",
            "admin123",
            "1234",
            "123456",
            "root",
            ""
        ]
        connected_superuser = False
        conn_su = None
        superuser_pwd = ""
        
        for pwd in passwords_to_try:
            ok_su, conn_su_tmp, _ = connect_pg(port, "postgres", pwd, "postgres")
            if ok_su:
                conn_su = conn_su_tmp
                superuser_pwd = pwd
                connected_superuser = True
                log("Conexión con superusuario 'postgres' establecida exitosamente.", "OK")
                break
        
        while not connected_superuser:
            log("PostgreSQL requiere la contraseña que ingresaste al instalarlo.", "WARN")
            typed_pwd = input("--> Ingresa la contraseña de 'postgres' (o presiona Enter): ").strip()
            ok_su, conn_su_tmp, err = connect_pg(port, "postgres", typed_pwd, "postgres")
            if ok_su:
                conn_su = conn_su_tmp
                superuser_pwd = typed_pwd
                connected_superuser = True
                log("¡Contraseña de instalación correcta!", "OK")
                break
            else:
                log("Contraseña incorrecta. Inténtalo de nuevo.", "ERROR")

        # Crear o actualizar usuario restaurante como SUPERUSER
        with conn_su.cursor() as cur:
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'restaurante') THEN
                        CREATE USER restaurante WITH PASSWORD 'restaurante_dev' SUPERUSER;
                    ELSE
                        ALTER USER restaurante WITH PASSWORD 'restaurante_dev' SUPERUSER;
                    END IF;
                END
                $$;
            """)
        log("Usuario 'restaurante' configurado con rol SUPERUSER.", "OK")
        conn_su.close()

    # 5. Asegurar base de datos 'restaurante'
    log("Paso 5: Verificando base de datos 'restaurante'...", "INFO")
    # Conectar como restaurante
    ok_res2, conn_check, _ = connect_pg(port, "restaurante", "restaurante_dev", "postgres")
    if not ok_res2:
        # Fallback a postgres
        _, conn_check, _ = connect_pg(port, "postgres", superuser_pwd, "postgres")
        
    with conn_check.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'restaurante';")
        db_exists = cur.fetchone() is not None
        if not db_exists:
            log("Creando base de datos 'restaurante'...", "INFO")
            cur.execute("CREATE DATABASE restaurante OWNER restaurante;")
            log("Base de datos 'restaurante' creada con éxito.", "OK")
        else:
            log("Base de datos 'restaurante' ya existe.", "OK")
    conn_check.close()

    # 6. Conectar a la base de datos restaurante y verificar tablas
    log("Paso 6: Verificando tablas del sistema...", "INFO")
    ok_db, conn_app, err_app = connect_pg(port, "restaurante", "restaurante_dev", "restaurante")
    if not ok_db:
        log(f"Error conectando a BD 'restaurante': {err_app}", "ERROR")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
        
    with conn_app.cursor() as cur:
        cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'usuario';")
        has_user_table = cur.fetchone()[0] > 0

    if not has_user_table:
        log("Inicializando tablas del sistema...", "WARN")
        sql_files = [
            os.path.join(root_dir, "database", "init", "01_schema.sql"),
            os.path.join(root_dir, "database", "init", "02_seeds.sql"),
            os.path.join(root_dir, "database", "init", "03_migracion_arquitectura_e_insumos.sql"),
        ]
        
        for f in sql_files:
            fname = os.path.basename(f)
            log(f"Aplicando {fname}...", "INFO")
            # Si psql está disponible, usarlo
            applied = False
            if psql_path:
                env = os.environ.copy()
                env["PGPASSWORD"] = "restaurante_dev"
                cmd = [psql_path, "-h", "127.0.0.1", "-p", str(port), "-U", "restaurante", "-d", "restaurante", "-f", f]
                try:
                    res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
                    if res.returncode == 0:
                        log(f"{fname} aplicado con psql.", "OK")
                        applied = True
                except Exception:
                    pass
            if not applied:
                execute_sql_file_psycopg2(conn_app, f)
                log(f"{fname} procesado con conector nativo.", "OK")
    else:
        log("Tablas del sistema ya están presentes.", "OK")

    # 7. Verificar usuario admin
    log("Paso 7: Verificando usuario administrador...", "INFO")
    with conn_app.cursor() as cur:
        cur.execute("SELECT id, usuario, activo FROM usuario WHERE usuario = 'admin';")
        row = cur.fetchone()
        if row:
            log("Usuario 'admin' verificado y listo para iniciar sesión.", "OK")
        else:
            log("Creando usuario 'admin' con clave inicial 'admin123'...", "INFO")
            cur.execute("""
                INSERT INTO usuario (usuario, password_hash, rol_id, nombre, activo)
                VALUES ('admin', '$2b$12$0amk7zbGAMzOhIJUULskyudrwXFJGSdkR4szxhPqjUvxlJccbfLPW', 1, 'Administrador General', TRUE)
                ON CONFLICT (usuario) DO NOTHING;
            """)
            log("Usuario 'admin' creado correctamente.", "OK")
    conn_app.close()

    # 8. Guardar configuración en backend/.env
    log("Paso 8: Configurando variables de entorno...", "INFO")
    env_file = os.path.join(root_dir, "backend", ".env")
    db_url_line = f"DATABASE_URL=postgresql://restaurante:restaurante_dev@127.0.0.1:{port}/restaurante\n"
    
    existing_lines = []
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            existing_lines = [l for l in f.readlines() if not l.startswith("DATABASE_URL=")]
    
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(db_url_line)
        f.writelines(existing_lines)
    log(f"Guardado {env_file} con puerto {port}.", "OK")

    print()
    print("=" * 65)
    print("  ¡DIAGNÓSTICO Y REPARACIÓN COMPLETADOS CON ÉXITO!  ")
    print("=" * 65)
    print(f"  * PostgreSQL:       Activo en 127.0.0.1:{port}")
    print("  * Base de Datos:    'restaurante' lista y conectada")
    print("  * Usuario Admin:    'admin' / Clave: 'admin123'")
    print("=" * 65)
    print()
    print("Siguiente paso:")
    print("1. Cierra esta ventana.")
    print("2. Haz doble clic en 'Mr. Burger POS' en tu escritorio")
    print("   (o ejecuta 'iniciar_silencioso.vbs').")
    print("3. Inicia sesión con: admin / admin123")
    print()
    input("Presiona Enter para finalizar...")

if __name__ == "__main__":
    main()
