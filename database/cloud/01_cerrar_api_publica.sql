-- ============================================================
-- SUPABASE: cerrar el acceso por la API pública (PostgREST)
-- ============================================================
-- El sistema NO usa la API de Supabase: el backend de Render entra directo a PostgreSQL
-- con el rol `postgres` (dueño de las tablas, exento de RLS). Pero Supabase publica por
-- defecto todo el esquema `public` a los roles `anon` y `authenticated`, de modo que con
-- la clave pública del proyecto se podía leer, modificar y borrar cualquier tabla.
--
-- Este script es idempotente: se puede ejecutar las veces que haga falta.
-- Aplicar con:  supabase db query --linked -f database/cloud/01_cerrar_api_publica.sql
-- ============================================================

-- 1. Quitar todos los permisos de los roles públicos sobre lo que ya existe
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated;

-- 2. Que las tablas que el backend cree en el futuro tampoco nazcan abiertas
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON TABLES    FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM anon, authenticated;

-- 3. Segunda barrera: seguridad por filas activa y sin políticas = nadie pasa por la API.
--    (El rol `postgres` es dueño y tiene BYPASSRLS, así que el backend no se ve afectado.)
DO $$
DECLARE t record;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
    END LOOP;
END $$;
