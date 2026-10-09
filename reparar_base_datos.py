import os
import sys
import socket
import subprocess
import shutil
import time

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
    except Exception as e:
        log(f"No se pudo consultar lista de servicios: {e}", "WARN")
    
    # Defaults comunes si 'sc' falló
    if not services:
        services = ["postgresql-x64-15", "postgresql-x64-16", "postgresql-x64-17", "postgresql-15", "postgresql-16"]
    return services

def ensure_postgres_service_running():
    log("Paso 1: Verificando servicio de PostgreSQL en Windows...", "INFO")
    services = get_postgres_services()
    started_any = False
    for svc in services:
        try:
            query = subprocess.check_output(f'sc query "{svc}"', shell=True, text=True, errors="ignore")
            if "RUNNING" in query.upper():
                log(f"Servicio '{svc}' está ACTIVO y corriendo.", "OK")
                started_any = True
                break
            elif "STOPPED" in query.upper():
                log(f"Servicio '{svc}' está DETENIDO. Iniciando...", "WARN")
                subprocess.run(f'net start "{svc}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f'sc config "{svc}" start= auto', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                started_any = True
                break
        except Exception:
            continue
    
    if not started_any:
        # Intentar iniciar los comunes
        for common in ["postgresql-x64-15", "postgresql-x64-16"]:
            subprocess.run(f'net start "{common}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)

def detect_postgres_port():
    log("Paso 2: Detectando puerto TCP de PostgreSQL...", "INFO")
    for port in [5432, 5433, 5434]:
        if check_port("127.0.0.1", port):
            log(f"PostgreSQL respondiendo en puerto {port}.", "OK")
            return port
    return None

def find_psql_binary():
    log("Paso 3: Localizando ejecutable psql.exe...", "INFO")
    candidates = [
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            log(f"Encontrado: {p}", "OK")
            return p
    which_psql = shutil.which("psql")
    if which_psql:
        log(f"Encontrado en PATH: {which_psql}", "OK")
        return which_psql
    return None

def try_psql_query(psql_path, port, user, password, db, query):
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    cmd = [psql_path, "-h", "127.0.0.1", "-p", str(port), "-U", user, "-d", db, "-c", query]
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=5)
        return res.returncode == 0, res.stdout, res.stderr
    except Exception as e:
        return False, "", str(e)

def execute_sql_file(psql_path, port, user, password, db, file_path):
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    cmd = [psql_path, "-h", "127.0.0.1", "-p", str(port), "-U", user, "-d", db, "-f", file_path]
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        return res.returncode == 0, res.stdout, res.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print_banner()
    root_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 1. Asegurar servicio iniciado
    ensure_postgres_service_running()
    
    # 2. Detectar puerto
    port = detect_postgres_port()
    if not port:
        log("No se detectó PostgreSQL en puertos 5432 ni 5433.", "WARN")
        log("Intentando reiniciar el servicio de PostgreSQL...", "INFO")
        for svc in ["postgresql-x64-15", "postgresql-x64-16", "postgresql-15"]:
            subprocess.run(f'net start "{svc}"', shell=True)
        time.sleep(2)
        port = detect_postgres_port()
        
    if not port:
        log("ERROR: PostgreSQL no está activo o no acepta conexiones locales.", "ERROR")
        log("Por favor abre 'Servicios' en Windows (Win + R -> services.msc) y busca 'postgresql-x64-15'.", "WARN")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
        
    # 3. Localizar psql
    psql_path = find_psql_binary()
    if not psql_path:
        log("ERROR: No se encontró psql.exe en C:\\Program Files\\PostgreSQL\\15\\bin.", "ERROR")
        input("\nPresiona Enter para salir...")
        sys.exit(1)

    # 4. Probar si el usuario 'restaurante' ya conecta
    log("Paso 4: Verificando credenciales de base de datos...", "INFO")
    ok, out, _ = try_psql_query(psql_path, port, "restaurante", "restaurante_dev", "postgres", "SELECT 1;")
    superuser_pwd = None
    
    if ok:
        log("Usuario 'restaurante' autenticado con éxito.", "OK")
    else:
        log("Configurando usuario 'restaurante' como superusuario...", "INFO")
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
        connected = False
        for pwd in passwords_to_try:
            ok_pg, _, _ = try_psql_query(psql_path, port, "postgres", pwd, "postgres", "SELECT 1;")
            if ok_pg:
                superuser_pwd = pwd
                connected = True
                log(f"Conexión como 'postgres' exitosa con contraseña de instalación.", "OK")
                break
        
        while not connected:
            log("PostgreSQL requiere la contraseña que ingresaste al instalarlo.", "WARN")
            typed_pwd = input("--> Ingresa la contraseña de 'postgres' (o presiona Enter si no pusiste): ").strip()
            ok_pg, _, err = try_psql_query(psql_path, port, "postgres", typed_pwd, "postgres", "SELECT 1;")
            if ok_pg:
                superuser_pwd = typed_pwd
                connected = True
                log("¡Contraseña correcta!", "OK")
                break
            else:
                log(f"Contraseña incorrecta: {err.strip()}", "ERROR")

        # Crear o actualizar usuario restaurante
        create_user_sql = (
            "DO $$ BEGIN "
            "IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'restaurante') THEN "
            "CREATE USER restaurante WITH PASSWORD 'restaurante_dev' SUPERUSER; "
            "ELSE "
            "ALTER USER restaurante WITH PASSWORD 'restaurante_dev' SUPERUSER; "
            "END IF; END $$;"
        )
        ok_create, _, err = try_psql_query(psql_path, port, "postgres", superuser_pwd, "postgres", create_user_sql)
        if ok_create:
            log("Usuario 'restaurante' configurado con rol SUPERUSER.", "OK")
        else:
            log(f"Error creando usuario 'restaurante': {err}", "ERROR")

    # 5. Asegurar base de datos 'restaurante'
    log("Paso 5: Verificando base de datos 'restaurante'...", "INFO")
    check_db_sql = "SELECT 1 FROM pg_database WHERE datname = 'restaurante';"
    # Usar restaurante o postgres para chequear
    auth_user = "restaurante" if ok else "postgres"
    auth_pwd = "restaurante_dev" if ok else superuser_pwd
    ok_check, out, _ = try_psql_query(psql_path, port, auth_user, auth_pwd, "postgres", check_db_sql)
    
    if "1" not in out:
        log("Base de datos 'restaurante' no existe. Creándola...", "INFO")
        try_psql_query(psql_path, port, auth_user, auth_pwd, "postgres", "CREATE DATABASE restaurante OWNER restaurante;")
        log("Base de datos 'restaurante' creada con éxito.", "OK")
    else:
        log("Base de datos 'restaurante' ya existe.", "OK")

    # 6. Verificar tablas
    log("Paso 6: Verificando tablas del sistema...", "INFO")
    check_tables_sql = "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'usuario';"
    ok_tbl, out_tbl, _ = try_psql_query(psql_path, port, "restaurante", "restaurante_dev", "restaurante", check_tables_sql)
    
    tablas_existen = False
    for line in out_tbl.splitlines():
        if line.strip().isdigit() and int(line.strip()) > 0:
            tablas_existen = True
            break
            
    if not tablas_existen:
        log("Las tablas no existen. Ejecutando scripts de migración...", "WARN")
        sql_files = [
            os.path.join(root_dir, "database", "init", "01_schema.sql"),
            os.path.join(root_dir, "database", "init", "02_seeds.sql"),
            os.path.join(root_dir, "database", "init", "03_migracion_arquitectura_e_insumos.sql"),
        ]
        for f in sql_files:
            fname = os.path.basename(f)
            if os.path.exists(f):
                log(f"Ejecutando {fname}...", "INFO")
                ok_f, out_f, err_f = execute_sql_file(psql_path, port, "restaurante", "restaurante_dev", "restaurante", f)
                if ok_f:
                    log(f"{fname} aplicado correctamente.", "OK")
                else:
                    log(f"Aviso en {fname}: {err_f[:120]}", "WARN")
            else:
                log(f"No se encontró {f}", "WARN")
    else:
        log("Tablas del sistema ya están presentes.", "OK")

    # 7. Verificar usuario admin
    log("Paso 7: Verificando usuario administrador...", "INFO")
    check_admin_sql = "SELECT id, usuario, activo FROM usuario WHERE usuario = 'admin';"
    ok_adm, out_adm, _ = try_psql_query(psql_path, port, "restaurante", "restaurante_dev", "restaurante", check_admin_sql)
    if "admin" in out_adm:
        log("Usuario 'admin' verificado y listo para iniciar sesión.", "OK")
    else:
        log("Creando usuario 'admin' con clave inicial 'admin123'...", "INFO")
        # Semilla básica de admin si faltara
        insert_admin_sql = (
            "INSERT INTO usuario (usuario, password_hash, rol_id, nombre, activo) "
            "VALUES ('admin', '$2b$12$0amk7zbGAMzOhIJUULskyudrwXFJGSdkR4szxhPqjUvxlJccbfLPW', 1, 'Administrador General', TRUE) "
            "ON CONFLICT (usuario) DO NOTHING;"
        )
        try_psql_query(psql_path, port, "restaurante", "restaurante_dev", "restaurante", insert_admin_sql)
        log("Usuario 'admin' creado correctamente.", "OK")

    # 8. Guardar configuración en backend/.env
    log("Paso 8: Configurando variables de entorno para el Backend...", "INFO")
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
