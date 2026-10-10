--
-- PostgreSQL database dump
--

\restrict KRHFsrFfhHNaYFQXutqk787Bc0XnEdMj5xwTznYuzwtfZQQT7guRriSEGRUeCcY

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

-- Started on 2026-10-09 21:03:11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 16389)
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- TOC entry 5377 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 228 (class 1259 OID 16488)
-- Name: categoria; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.categoria (
    id integer NOT NULL,
    tipo_id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    orden integer DEFAULT 0 NOT NULL,
    activo boolean DEFAULT true NOT NULL
);


ALTER TABLE public.categoria OWNER TO restaurante;

--
-- TOC entry 227 (class 1259 OID 16487)
-- Name: categoria_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.categoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categoria_id_seq OWNER TO restaurante;

--
-- TOC entry 5378 (class 0 OID 0)
-- Dependencies: 227
-- Name: categoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.categoria_id_seq OWNED BY public.categoria.id;


--
-- TOC entry 234 (class 1259 OID 16545)
-- Name: categoria_insumo; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.categoria_insumo (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion text,
    activo boolean DEFAULT true NOT NULL
);


ALTER TABLE public.categoria_insumo OWNER TO restaurante;

--
-- TOC entry 233 (class 1259 OID 16544)
-- Name: categoria_insumo_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.categoria_insumo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categoria_insumo_id_seq OWNER TO restaurante;

--
-- TOC entry 5379 (class 0 OID 0)
-- Dependencies: 233
-- Name: categoria_insumo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.categoria_insumo_id_seq OWNED BY public.categoria_insumo.id;


--
-- TOC entry 256 (class 1259 OID 16864)
-- Name: cierre; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.cierre (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    abierto_en timestamp with time zone NOT NULL,
    cerrado_en timestamp with time zone,
    total_pedidos integer DEFAULT 0 NOT NULL,
    total_venta_comida numeric(12,2) DEFAULT 0 NOT NULL,
    total_venta_bebida numeric(12,2) DEFAULT 0 NOT NULL,
    total_efectivo numeric(12,2) DEFAULT 0 NOT NULL,
    total_tarjeta numeric(12,2) DEFAULT 0 NOT NULL,
    total_transferencia numeric(12,2) DEFAULT 0 NOT NULL,
    total_vale numeric(12,2) DEFAULT 0 NOT NULL,
    cantidad_vales integer DEFAULT 0 NOT NULL,
    total_didi_tarjeta numeric(12,2) DEFAULT 0 NOT NULL,
    total_didi_efectivo numeric(12,2) DEFAULT 0 NOT NULL,
    total_entradas_caja numeric(12,2) DEFAULT 0 NOT NULL,
    total_salidas_caja numeric(12,2) DEFAULT 0 NOT NULL,
    cantidad_egresos integer DEFAULT 0 NOT NULL,
    total_devoluciones numeric(12,2) DEFAULT 0 NOT NULL,
    preparados_reutilizados integer DEFAULT 0 NOT NULL,
    preparados_descartados integer DEFAULT 0 NOT NULL,
    total_ventas numeric(12,2) DEFAULT 0 NOT NULL,
    total_efectivo_final numeric(12,2) DEFAULT 0 NOT NULL,
    total_por_cobrar numeric(12,2) DEFAULT 0 NOT NULL,
    notas text,
    es_demo boolean DEFAULT false NOT NULL
);


ALTER TABLE public.cierre OWNER TO restaurante;

--
-- TOC entry 255 (class 1259 OID 16863)
-- Name: cierre_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.cierre_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cierre_id_seq OWNER TO restaurante;

--
-- TOC entry 5380 (class 0 OID 0)
-- Dependencies: 255
-- Name: cierre_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.cierre_id_seq OWNED BY public.cierre.id;


--
-- TOC entry 240 (class 1259 OID 16619)
-- Name: componente_combo; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.componente_combo (
    id integer NOT NULL,
    combo_producto_id integer NOT NULL,
    producto_hijo_id integer NOT NULL,
    cantidad numeric(10,2) DEFAULT 1 NOT NULL
);


ALTER TABLE public.componente_combo OWNER TO restaurante;

--
-- TOC entry 239 (class 1259 OID 16618)
-- Name: componente_combo_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.componente_combo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.componente_combo_id_seq OWNER TO restaurante;

--
-- TOC entry 5381 (class 0 OID 0)
-- Dependencies: 239
-- Name: componente_combo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.componente_combo_id_seq OWNED BY public.componente_combo.id;


--
-- TOC entry 260 (class 1259 OID 16975)
-- Name: compra; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.compra (
    id integer NOT NULL,
    proveedor_id integer,
    usuario_id integer NOT NULL,
    descripcion text,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    es_demo boolean DEFAULT false NOT NULL
);


ALTER TABLE public.compra OWNER TO restaurante;

--
-- TOC entry 259 (class 1259 OID 16974)
-- Name: compra_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.compra_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.compra_id_seq OWNER TO restaurante;

--
-- TOC entry 5382 (class 0 OID 0)
-- Dependencies: 259
-- Name: compra_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.compra_id_seq OWNED BY public.compra.id;


--
-- TOC entry 220 (class 1259 OID 16427)
-- Name: configuracion; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.configuracion (
    clave character varying(50) NOT NULL,
    valor text NOT NULL,
    descripcion text
);


ALTER TABLE public.configuracion OWNER TO restaurante;

--
-- TOC entry 262 (class 1259 OID 16998)
-- Name: detalle_compra; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.detalle_compra (
    id integer NOT NULL,
    compra_id integer NOT NULL,
    ingrediente_id integer NOT NULL,
    cantidad numeric(12,4) NOT NULL,
    costo_unitario numeric(12,4) NOT NULL,
    costo_total numeric(12,4) NOT NULL
);


ALTER TABLE public.detalle_compra OWNER TO restaurante;

--
-- TOC entry 261 (class 1259 OID 16997)
-- Name: detalle_compra_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.detalle_compra_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detalle_compra_id_seq OWNER TO restaurante;

--
-- TOC entry 5383 (class 0 OID 0)
-- Dependencies: 261
-- Name: detalle_compra_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.detalle_compra_id_seq OWNED BY public.detalle_compra.id;


--
-- TOC entry 246 (class 1259 OID 16704)
-- Name: detalle_pedido; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.detalle_pedido (
    id integer NOT NULL,
    pedido_id integer NOT NULL,
    ronda integer DEFAULT 1 NOT NULL,
    producto_id integer NOT NULL,
    cantidad numeric(10,2) DEFAULT 1 NOT NULL,
    precio_unitario numeric(12,2) NOT NULL,
    variacion_snapshot jsonb,
    estado character varying(20) DEFAULT 'ENVIADO'::character varying NOT NULL,
    preparado_en timestamp with time zone,
    listo_en timestamp with time zone,
    entregado_en timestamp with time zone,
    cancelado_en timestamp with time zone,
    CONSTRAINT detalle_pedido_estado_check CHECK (((estado)::text = ANY ((ARRAY['ENVIADO'::character varying, 'PREPARANDO'::character varying, 'LISTO'::character varying, 'ENTREGADO'::character varying, 'CANCELADO'::character varying])::text[])))
);


ALTER TABLE public.detalle_pedido OWNER TO restaurante;

--
-- TOC entry 245 (class 1259 OID 16703)
-- Name: detalle_pedido_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.detalle_pedido_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detalle_pedido_id_seq OWNER TO restaurante;

--
-- TOC entry 5384 (class 0 OID 0)
-- Dependencies: 245
-- Name: detalle_pedido_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.detalle_pedido_id_seq OWNED BY public.detalle_pedido.id;


--
-- TOC entry 238 (class 1259 OID 16595)
-- Name: detalle_receta; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.detalle_receta (
    id integer NOT NULL,
    product_id integer NOT NULL,
    ingrediente_id integer NOT NULL,
    cantidad numeric(12,4) NOT NULL,
    unidad character varying(20) NOT NULL,
    solo_llevar boolean DEFAULT false NOT NULL
);


ALTER TABLE public.detalle_receta OWNER TO restaurante;

--
-- TOC entry 237 (class 1259 OID 16594)
-- Name: detalle_receta_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.detalle_receta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detalle_receta_id_seq OWNER TO restaurante;

--
-- TOC entry 5385 (class 0 OID 0)
-- Dependencies: 237
-- Name: detalle_receta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.detalle_receta_id_seq OWNED BY public.detalle_receta.id;


--
-- TOC entry 264 (class 1259 OID 17026)
-- Name: historial_accion; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.historial_accion (
    id integer NOT NULL,
    usuario_id integer,
    accion character varying(100) NOT NULL,
    entidad character varying(50),
    entidad_id integer,
    detalle text,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    es_demo boolean DEFAULT false NOT NULL
);


ALTER TABLE public.historial_accion OWNER TO restaurante;

--
-- TOC entry 263 (class 1259 OID 17025)
-- Name: historial_accion_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.historial_accion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.historial_accion_id_seq OWNER TO restaurante;

--
-- TOC entry 5386 (class 0 OID 0)
-- Dependencies: 263
-- Name: historial_accion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.historial_accion_id_seq OWNED BY public.historial_accion.id;


--
-- TOC entry 236 (class 1259 OID 16560)
-- Name: ingrediente; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.ingrediente (
    id integer NOT NULL,
    categoria_insumo_id integer,
    nombre character varying(100) NOT NULL,
    unidad_base character varying(20) NOT NULL,
    costo_unitario numeric(12,4) DEFAULT 0 NOT NULL,
    costo_proveedor text,
    stock_actual numeric(12,4) DEFAULT 0 NOT NULL,
    stock_minimo numeric(12,4) DEFAULT 0 NOT NULL,
    stock_ideal numeric(12,4),
    proveedor_id integer,
    activo boolean DEFAULT true NOT NULL,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    actualizado_en timestamp with time zone DEFAULT now() NOT NULL,
    tipo_articulo character varying(30) DEFAULT 'INSUMO_RECETA'::character varying,
    precio_venta numeric(12,2) DEFAULT 0,
    CONSTRAINT ingrediente_tipo_articulo_check CHECK (((tipo_articulo)::text = ANY ((ARRAY['INSUMO_RECETA'::character varying, 'VENTA_DIRECTA'::character varying, 'DESECHABLE_SERVICIO'::character varying, 'GASTO_OPERATIVO'::character varying])::text[]))),
    CONSTRAINT ingrediente_unidad_base_check CHECK (((unidad_base)::text = ANY ((ARRAY['GRAMO'::character varying, 'MILILITRO'::character varying, 'UNIDAD'::character varying, 'LONJA'::character varying, 'PORCION'::character varying, 'PAQUETE'::character varying])::text[])))
);


ALTER TABLE public.ingrediente OWNER TO restaurante;

--
-- TOC entry 235 (class 1259 OID 16559)
-- Name: ingrediente_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.ingrediente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ingrediente_id_seq OWNER TO restaurante;

--
-- TOC entry 5387 (class 0 OID 0)
-- Dependencies: 235
-- Name: ingrediente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.ingrediente_id_seq OWNED BY public.ingrediente.id;


--
-- TOC entry 242 (class 1259 OID 16643)
-- Name: mesa; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.mesa (
    id integer NOT NULL,
    numero integer NOT NULL,
    estado character varying(20) DEFAULT 'DISPONIBLE'::character varying NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    CONSTRAINT mesa_estado_check CHECK (((estado)::text = ANY ((ARRAY['DISPONIBLE'::character varying, 'EN_CURSO'::character varying, 'OCUPADA'::character varying])::text[])))
);


ALTER TABLE public.mesa OWNER TO restaurante;

--
-- TOC entry 241 (class 1259 OID 16642)
-- Name: mesa_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.mesa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mesa_id_seq OWNER TO restaurante;

--
-- TOC entry 5388 (class 0 OID 0)
-- Dependencies: 241
-- Name: mesa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.mesa_id_seq OWNED BY public.mesa.id;


--
-- TOC entry 252 (class 1259 OID 16796)
-- Name: movimiento_caja; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.movimiento_caja (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo character varying(10) NOT NULL,
    categoria character varying(20) NOT NULL,
    concepto character varying(100) NOT NULL,
    descripcion text NOT NULL,
    valor numeric(12,2) NOT NULL,
    pedido_id integer,
    vale_id integer,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    cierre_id integer,
    es_demo boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_movcaja_categoria CHECK (((categoria)::text = ANY ((ARRAY['PAGO_TURNO'::character varying, 'PRESTAMO'::character varying, 'ADELANTO'::character varying, 'PROVEEDOR'::character varying, 'DEVOLUCION'::character varying, 'COBRO_VALE'::character varying, 'CAMBIO_INICIAL'::character varying, 'GASTO_OPERATIVO'::character varying, 'OTRO'::character varying])::text[]))),
    CONSTRAINT movimiento_caja_categoria_check CHECK (((categoria)::text = ANY ((ARRAY['PAGO_TURNO'::character varying, 'PRESTAMO'::character varying, 'ADELANTO'::character varying, 'PROVEEDOR'::character varying, 'DEVOLUCION'::character varying, 'COBRO_VALE'::character varying, 'CAMBIO_INICIAL'::character varying, 'OTRO'::character varying])::text[]))),
    CONSTRAINT movimiento_caja_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['ENTRADA'::character varying, 'SALIDA'::character varying])::text[])))
);


ALTER TABLE public.movimiento_caja OWNER TO restaurante;

--
-- TOC entry 251 (class 1259 OID 16795)
-- Name: movimiento_caja_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.movimiento_caja_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimiento_caja_id_seq OWNER TO restaurante;

--
-- TOC entry 5389 (class 0 OID 0)
-- Dependencies: 251
-- Name: movimiento_caja_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.movimiento_caja_id_seq OWNED BY public.movimiento_caja.id;


--
-- TOC entry 254 (class 1259 OID 16831)
-- Name: movimiento_inventario; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.movimiento_inventario (
    id integer NOT NULL,
    ingrediente_id integer NOT NULL,
    pedido_id integer,
    compra_id integer,
    usuario_id integer NOT NULL,
    cantidad numeric(12,4) NOT NULL,
    unidad character varying(20) DEFAULT 'u'::character varying,
    saldo_anterior numeric(12,4),
    saldo_nuevo numeric(12,4),
    costo_unitario_momento numeric(12,4),
    tipo character varying(20) NOT NULL,
    referencia text,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    es_demo boolean DEFAULT false NOT NULL,
    CONSTRAINT movimiento_inventario_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['VENTA'::character varying, 'COMPRA'::character varying, 'MERMA'::character varying, 'AJUSTE'::character varying, 'DEVOLUCION'::character varying, 'DESPERDICIO'::character varying])::text[])))
);


ALTER TABLE public.movimiento_inventario OWNER TO restaurante;

--
-- TOC entry 253 (class 1259 OID 16830)
-- Name: movimiento_inventario_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.movimiento_inventario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimiento_inventario_id_seq OWNER TO restaurante;

--
-- TOC entry 5390 (class 0 OID 0)
-- Dependencies: 253
-- Name: movimiento_inventario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.movimiento_inventario_id_seq OWNED BY public.movimiento_inventario.id;


--
-- TOC entry 248 (class 1259 OID 16736)
-- Name: pago; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.pago (
    id integer NOT NULL,
    pedido_id integer NOT NULL,
    cierre_id integer,
    metodo character varying(20) NOT NULL,
    monto numeric(12,2) NOT NULL,
    recibido numeric(12,2),
    cambio numeric(12,2),
    didi_orden_id character varying(50),
    estado character varying(15) DEFAULT 'VALIDO'::character varying NOT NULL,
    usuario_id integer,
    devuelto_por integer,
    devuelto_en timestamp with time zone,
    motivo_devolucion text,
    pagado_en timestamp with time zone DEFAULT now() NOT NULL,
    es_demo boolean DEFAULT false NOT NULL,
    CONSTRAINT pago_estado_check CHECK (((estado)::text = ANY ((ARRAY['VALIDO'::character varying, 'DEVUELTO'::character varying])::text[]))),
    CONSTRAINT pago_metodo_check CHECK (((metodo)::text = ANY ((ARRAY['EFECTIVO'::character varying, 'TARJETA'::character varying, 'TRANSFERENCIA'::character varying, 'VALE'::character varying, 'DIDI_TARJETA'::character varying, 'DIDI_EFECTIVO'::character varying])::text[])))
);


ALTER TABLE public.pago OWNER TO restaurante;

--
-- TOC entry 247 (class 1259 OID 16735)
-- Name: pago_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.pago_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pago_id_seq OWNER TO restaurante;

--
-- TOC entry 5391 (class 0 OID 0)
-- Dependencies: 247
-- Name: pago_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.pago_id_seq OWNED BY public.pago.id;


--
-- TOC entry 244 (class 1259 OID 16659)
-- Name: pedido; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.pedido (
    id integer NOT NULL,
    consecutivo integer NOT NULL,
    fecha_dia date DEFAULT CURRENT_DATE NOT NULL,
    canal character varying(20) NOT NULL,
    mesa_id integer,
    usuario_id integer NOT NULL,
    estado character varying(25) DEFAULT 'NUEVO'::character varying NOT NULL,
    cliente character varying(100),
    telefono character varying(30),
    direccion text,
    nota_interna text,
    didi_orden_id character varying(50),
    subtotal numeric(12,2) DEFAULT 0 NOT NULL,
    iva numeric(12,2) DEFAULT 0 NOT NULL,
    total numeric(12,2) DEFAULT 0 NOT NULL,
    motivo_cancelacion text,
    idempotency_key character varying(100),
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    enviado_en timestamp with time zone,
    finalizado_en timestamp with time zone,
    pagado_en timestamp with time zone,
    cancelado_en timestamp with time zone,
    tipo_consumo character varying(15) DEFAULT 'LOCAL'::character varying,
    recargo_empaque numeric(12,2) DEFAULT 0,
    es_demo boolean DEFAULT false NOT NULL,
    CONSTRAINT pedido_canal_check CHECK (((canal)::text = ANY ((ARRAY['MESA'::character varying, 'MOSTRADOR'::character varying, 'DIDI'::character varying, 'DOMICILIO'::character varying])::text[]))),
    CONSTRAINT pedido_estado_check CHECK (((estado)::text = ANY ((ARRAY['NUEVO'::character varying, 'ENVIADO_A_COCINA'::character varying, 'EN_PREPARACION'::character varying, 'FINALIZADO'::character varying, 'ENTREGADO'::character varying, 'PAGADO'::character varying, 'CERRADO'::character varying, 'CANCELADO'::character varying])::text[]))),
    CONSTRAINT pedido_tipo_consumo_check CHECK (((tipo_consumo)::text = ANY ((ARRAY['LOCAL'::character varying, 'LLEVAR'::character varying])::text[])))
);


ALTER TABLE public.pedido OWNER TO restaurante;

--
-- TOC entry 243 (class 1259 OID 16658)
-- Name: pedido_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.pedido_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pedido_id_seq OWNER TO restaurante;

--
-- TOC entry 5392 (class 0 OID 0)
-- Dependencies: 243
-- Name: pedido_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.pedido_id_seq OWNED BY public.pedido.id;


--
-- TOC entry 258 (class 1259 OID 16930)
-- Name: preparado; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.preparado (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    pedido_origen_id integer NOT NULL,
    detalle_origen_id integer NOT NULL,
    variacion_snapshot jsonb,
    cantidad numeric(10,2) DEFAULT 1 NOT NULL,
    estado character varying(15) DEFAULT 'DISPONIBLE'::character varying NOT NULL,
    pedido_nuevo_id integer,
    usuario_id integer,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    asignado_en timestamp with time zone,
    descartado_en timestamp with time zone,
    motivo_descarte text,
    es_demo boolean DEFAULT false NOT NULL,
    CONSTRAINT preparado_estado_check CHECK (((estado)::text = ANY ((ARRAY['DISPONIBLE'::character varying, 'ASIGNADO'::character varying, 'DESCARTADO'::character varying])::text[])))
);


ALTER TABLE public.preparado OWNER TO restaurante;

--
-- TOC entry 257 (class 1259 OID 16929)
-- Name: preparado_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.preparado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.preparado_id_seq OWNER TO restaurante;

--
-- TOC entry 5393 (class 0 OID 0)
-- Dependencies: 257
-- Name: preparado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.preparado_id_seq OWNED BY public.preparado.id;


--
-- TOC entry 230 (class 1259 OID 16507)
-- Name: producto; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.producto (
    id integer NOT NULL,
    categoria_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    imagen_url text,
    precio numeric(12,2) DEFAULT 0 NOT NULL,
    iva_incluido boolean DEFAULT true NOT NULL,
    manual_disponible boolean,
    activo boolean DEFAULT true NOT NULL,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    actualizado_en timestamp with time zone DEFAULT now() NOT NULL,
    empaque_llevar_id integer,
    permite_adiciones boolean DEFAULT true NOT NULL
);


ALTER TABLE public.producto OWNER TO restaurante;

--
-- TOC entry 229 (class 1259 OID 16506)
-- Name: producto_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.producto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.producto_id_seq OWNER TO restaurante;

--
-- TOC entry 5394 (class 0 OID 0)
-- Dependencies: 229
-- Name: producto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.producto_id_seq OWNED BY public.producto.id;


--
-- TOC entry 232 (class 1259 OID 16534)
-- Name: proveedor; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.proveedor (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    contacto character varying(100),
    telefono character varying(30),
    activo boolean DEFAULT true NOT NULL
);


ALTER TABLE public.proveedor OWNER TO restaurante;

--
-- TOC entry 231 (class 1259 OID 16533)
-- Name: proveedor_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.proveedor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.proveedor_id_seq OWNER TO restaurante;

--
-- TOC entry 5395 (class 0 OID 0)
-- Dependencies: 231
-- Name: proveedor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.proveedor_id_seq OWNED BY public.proveedor.id;


--
-- TOC entry 268 (class 1259 OID 17063)
-- Name: registro_sync; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.registro_sync (
    id integer NOT NULL,
    op_id character varying(64) NOT NULL,
    sucursal_id character varying(32) NOT NULL,
    dispositivo_id character varying(64),
    origen character varying(10) DEFAULT 'LOCAL'::character varying NOT NULL,
    tipo character varying(50) NOT NULL,
    entidad character varying(50) NOT NULL,
    entidad_id integer,
    entidad_uuid character varying(64),
    payload jsonb NOT NULL,
    estado character varying(20) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    reintentos integer DEFAULT 0 NOT NULL,
    ultimo_error text,
    resolucion_nota text,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    sincronizado_en timestamp with time zone
);


ALTER TABLE public.registro_sync OWNER TO restaurante;

--
-- TOC entry 267 (class 1259 OID 17062)
-- Name: registro_sync_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.registro_sync_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.registro_sync_id_seq OWNER TO restaurante;

--
-- TOC entry 5396 (class 0 OID 0)
-- Dependencies: 267
-- Name: registro_sync_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.registro_sync_id_seq OWNED BY public.registro_sync.id;


--
-- TOC entry 222 (class 1259 OID 16437)
-- Name: rol; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.rol (
    id integer NOT NULL,
    nombre character varying(30) NOT NULL,
    descripcion text
);


ALTER TABLE public.rol OWNER TO restaurante;

--
-- TOC entry 221 (class 1259 OID 16436)
-- Name: rol_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.rol_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rol_id_seq OWNER TO restaurante;

--
-- TOC entry 5397 (class 0 OID 0)
-- Dependencies: 221
-- Name: rol_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.rol_id_seq OWNED BY public.rol.id;


--
-- TOC entry 226 (class 1259 OID 16477)
-- Name: tipo_categoria; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.tipo_categoria (
    id integer NOT NULL,
    nombre character varying(20) NOT NULL
);


ALTER TABLE public.tipo_categoria OWNER TO restaurante;

--
-- TOC entry 225 (class 1259 OID 16476)
-- Name: tipo_categoria_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.tipo_categoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipo_categoria_id_seq OWNER TO restaurante;

--
-- TOC entry 5398 (class 0 OID 0)
-- Dependencies: 225
-- Name: tipo_categoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.tipo_categoria_id_seq OWNED BY public.tipo_categoria.id;


--
-- TOC entry 266 (class 1259 OID 17046)
-- Name: turno_laboral; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.turno_laboral (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    entrada_en timestamp with time zone DEFAULT now() NOT NULL,
    salida_en timestamp with time zone,
    motivo_cierre character varying(50),
    es_demo boolean DEFAULT false NOT NULL,
    rol character varying(50) DEFAULT 'cajero'::character varying NOT NULL
);


ALTER TABLE public.turno_laboral OWNER TO restaurante;

--
-- TOC entry 265 (class 1259 OID 17045)
-- Name: turno_laboral_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.turno_laboral_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.turno_laboral_id_seq OWNER TO restaurante;

--
-- TOC entry 5399 (class 0 OID 0)
-- Dependencies: 265
-- Name: turno_laboral_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.turno_laboral_id_seq OWNED BY public.turno_laboral.id;


--
-- TOC entry 224 (class 1259 OID 16450)
-- Name: usuario; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.usuario (
    id integer NOT NULL,
    rol_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    usuario character varying(50) NOT NULL,
    password_hash text NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    actualizado_en timestamp with time zone DEFAULT now() NOT NULL,
    fijado boolean DEFAULT false NOT NULL,
    es_demo boolean DEFAULT false NOT NULL
);


ALTER TABLE public.usuario OWNER TO restaurante;

--
-- TOC entry 223 (class 1259 OID 16449)
-- Name: usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuario_id_seq OWNER TO restaurante;

--
-- TOC entry 5400 (class 0 OID 0)
-- Dependencies: 223
-- Name: usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.usuario_id_seq OWNED BY public.usuario.id;


--
-- TOC entry 250 (class 1259 OID 16770)
-- Name: vale; Type: TABLE; Schema: public; Owner: restaurante
--

CREATE TABLE public.vale (
    id integer NOT NULL,
    pedido_id integer NOT NULL,
    cliente_nombre character varying(100) NOT NULL,
    cliente_cedula character varying(20),
    cliente_telefono character varying(30),
    monto numeric(12,2) NOT NULL,
    estado character varying(15) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    cobrado_por integer,
    cobrado_en timestamp with time zone,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    es_demo boolean DEFAULT false NOT NULL,
    CONSTRAINT vale_estado_check CHECK (((estado)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'COBRADO'::character varying])::text[])))
);


ALTER TABLE public.vale OWNER TO restaurante;

--
-- TOC entry 249 (class 1259 OID 16769)
-- Name: vale_id_seq; Type: SEQUENCE; Schema: public; Owner: restaurante
--

CREATE SEQUENCE public.vale_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vale_id_seq OWNER TO restaurante;

--
-- TOC entry 5401 (class 0 OID 0)
-- Dependencies: 249
-- Name: vale_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: restaurante
--

ALTER SEQUENCE public.vale_id_seq OWNED BY public.vale.id;


--
-- TOC entry 4920 (class 2604 OID 16491)
-- Name: categoria id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.categoria ALTER COLUMN id SET DEFAULT nextval('public.categoria_id_seq'::regclass);


--
-- TOC entry 4932 (class 2604 OID 16548)
-- Name: categoria_insumo id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.categoria_insumo ALTER COLUMN id SET DEFAULT nextval('public.categoria_insumo_id_seq'::regclass);


--
-- TOC entry 4979 (class 2604 OID 16867)
-- Name: cierre id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.cierre ALTER COLUMN id SET DEFAULT nextval('public.cierre_id_seq'::regclass);


--
-- TOC entry 4945 (class 2604 OID 16622)
-- Name: componente_combo id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.componente_combo ALTER COLUMN id SET DEFAULT nextval('public.componente_combo_id_seq'::regclass);


--
-- TOC entry 5005 (class 2604 OID 16978)
-- Name: compra id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.compra ALTER COLUMN id SET DEFAULT nextval('public.compra_id_seq'::regclass);


--
-- TOC entry 5008 (class 2604 OID 17001)
-- Name: detalle_compra id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_compra ALTER COLUMN id SET DEFAULT nextval('public.detalle_compra_id_seq'::regclass);


--
-- TOC entry 4960 (class 2604 OID 16707)
-- Name: detalle_pedido id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_pedido ALTER COLUMN id SET DEFAULT nextval('public.detalle_pedido_id_seq'::regclass);


--
-- TOC entry 4943 (class 2604 OID 16598)
-- Name: detalle_receta id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_receta ALTER COLUMN id SET DEFAULT nextval('public.detalle_receta_id_seq'::regclass);


--
-- TOC entry 5009 (class 2604 OID 17029)
-- Name: historial_accion id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.historial_accion ALTER COLUMN id SET DEFAULT nextval('public.historial_accion_id_seq'::regclass);


--
-- TOC entry 4934 (class 2604 OID 16563)
-- Name: ingrediente id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.ingrediente ALTER COLUMN id SET DEFAULT nextval('public.ingrediente_id_seq'::regclass);


--
-- TOC entry 4947 (class 2604 OID 16646)
-- Name: mesa id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.mesa ALTER COLUMN id SET DEFAULT nextval('public.mesa_id_seq'::regclass);


--
-- TOC entry 4972 (class 2604 OID 16799)
-- Name: movimiento_caja id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_caja ALTER COLUMN id SET DEFAULT nextval('public.movimiento_caja_id_seq'::regclass);


--
-- TOC entry 4975 (class 2604 OID 16834)
-- Name: movimiento_inventario id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_inventario ALTER COLUMN id SET DEFAULT nextval('public.movimiento_inventario_id_seq'::regclass);


--
-- TOC entry 4964 (class 2604 OID 16739)
-- Name: pago id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pago ALTER COLUMN id SET DEFAULT nextval('public.pago_id_seq'::regclass);


--
-- TOC entry 4950 (class 2604 OID 16662)
-- Name: pedido id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pedido ALTER COLUMN id SET DEFAULT nextval('public.pedido_id_seq'::regclass);


--
-- TOC entry 5000 (class 2604 OID 16933)
-- Name: preparado id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.preparado ALTER COLUMN id SET DEFAULT nextval('public.preparado_id_seq'::regclass);


--
-- TOC entry 4923 (class 2604 OID 16510)
-- Name: producto id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.producto ALTER COLUMN id SET DEFAULT nextval('public.producto_id_seq'::regclass);


--
-- TOC entry 4930 (class 2604 OID 16537)
-- Name: proveedor id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.proveedor ALTER COLUMN id SET DEFAULT nextval('public.proveedor_id_seq'::regclass);


--
-- TOC entry 5016 (class 2604 OID 17066)
-- Name: registro_sync id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.registro_sync ALTER COLUMN id SET DEFAULT nextval('public.registro_sync_id_seq'::regclass);


--
-- TOC entry 4912 (class 2604 OID 16440)
-- Name: rol id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.rol ALTER COLUMN id SET DEFAULT nextval('public.rol_id_seq'::regclass);


--
-- TOC entry 4919 (class 2604 OID 16480)
-- Name: tipo_categoria id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.tipo_categoria ALTER COLUMN id SET DEFAULT nextval('public.tipo_categoria_id_seq'::regclass);


--
-- TOC entry 5012 (class 2604 OID 17049)
-- Name: turno_laboral id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.turno_laboral ALTER COLUMN id SET DEFAULT nextval('public.turno_laboral_id_seq'::regclass);


--
-- TOC entry 4913 (class 2604 OID 16453)
-- Name: usuario id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.usuario ALTER COLUMN id SET DEFAULT nextval('public.usuario_id_seq'::regclass);


--
-- TOC entry 4968 (class 2604 OID 16773)
-- Name: vale id; Type: DEFAULT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.vale ALTER COLUMN id SET DEFAULT nextval('public.vale_id_seq'::regclass);


--
-- TOC entry 5331 (class 0 OID 16488)
-- Dependencies: 228
-- Data for Name: categoria; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.categoria (id, tipo_id, nombre, orden, activo) FROM stdin;
1	1	HAMBURGUESAS	1	t
2	1	COMBOS	2	t
3	1	PERROS CALIENTES	3	t
4	1	ASADOS	4	t
5	1	MAZORCAS Y DESGRANADOS	5	t
6	1	ALITAS	6	t
7	1	PARA COMPARTIR Y ADICIONES	7	t
8	2	BEBIDAS	8	t
99	3	OTROS SERVICIOS	9	t
\.


--
-- TOC entry 5337 (class 0 OID 16545)
-- Dependencies: 234
-- Data for Name: categoria_insumo; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.categoria_insumo (id, nombre, descripcion, activo) FROM stdin;
1	CARNES	Carnes de res, pollo, salchichas, tocineta	t
2	VERDURAS	Tomate, lechuga, cebolla, etc.	t
3	PANADERIA	Panes para hamburguesa y perro	t
4	LACTEOS	Queso cheddar, mozzarella, costeño	t
5	SALSAS_CONDIMENTOS	Salsas de la casa, mayonesa, ketchup, chimichurri	t
6	ABARROTES_ACEITES	Papa cruda, aceites, harinas, sal	t
7	BEBIDAS	Gaseosas, aguas, pulpas, cervezas	t
9	OTRO	Otros insumos no categorizados	t
8	DESECHABLES_EMPAQUES	Servilletas, vasos, cajas, bolsas	t
10	GASTOS_OPERATIVOS	Artículos de aseo, papelería y mantenimiento (NO RECETAS)	t
\.


--
-- TOC entry 5359 (class 0 OID 16864)
-- Dependencies: 256
-- Data for Name: cierre; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.cierre (id, usuario_id, abierto_en, cerrado_en, total_pedidos, total_venta_comida, total_venta_bebida, total_efectivo, total_tarjeta, total_transferencia, total_vale, cantidad_vales, total_didi_tarjeta, total_didi_efectivo, total_entradas_caja, total_salidas_caja, cantidad_egresos, total_devoluciones, preparados_reutilizados, preparados_descartados, total_ventas, total_efectivo_final, total_por_cobrar, notas, es_demo) FROM stdin;
1	5	2026-10-08 20:49:51.192555-05	2026-10-08 20:56:01.042321-05	0	0.00	0.00	0.00	0.00	0.00	0.00	0	0.00	0.00	521650.00	0.00	0	0.00	0	0	0.00	521650.00	0.00	Arqueo físico: Billetes: $521.600 COP | Monedas: $0 COP | Total Efectivo: $521.600 COP | Datáfono/Transferencias: $0 COP. 	f
2	5	2026-10-09 19:50:00.923797-05	\N	0	0.00	0.00	0.00	0.00	0.00	0.00	0	0.00	0.00	0.00	0.00	0	0.00	0	0	0.00	0.00	0.00	\N	f
\.


--
-- TOC entry 5343 (class 0 OID 16619)
-- Dependencies: 240
-- Data for Name: componente_combo; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.componente_combo (id, combo_producto_id, producto_hijo_id, cantidad) FROM stdin;
7	27	63	1.00
8	27	55	1.00
9	26	63	1.00
10	26	55	1.00
\.


--
-- TOC entry 5363 (class 0 OID 16975)
-- Dependencies: 260
-- Data for Name: compra; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.compra (id, proveedor_id, usuario_id, descripcion, creado_en, es_demo) FROM stdin;
1	\N	1	Proveedor: Pan Guadalupe. Factura Insumos Panadería y Carnes. Subtotal: $556,046.46 | IVA (19%): $105,648.83 | Total a Pagar: $661,695.29 COP	2026-10-09 19:12:24.791171-05	f
\.


--
-- TOC entry 5323 (class 0 OID 16427)
-- Dependencies: 220
-- Data for Name: configuracion; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.configuracion (clave, valor, descripcion) FROM stdin;
iva_porcentaje	0	IVA/Impuesto en porcentaje. 0 = Régimen No Responsable (Art. 512-13 E.T.)
minutos_cocina	28	Temporizador por defecto de cocina (minutos)
modo_impuestos	INCLUIDO	INCLUIDO = el precio ya lleva IVA y se separa en recibo
max_rondas_disponible	1	Futuro: rondas
didi_comision_pct	0	Comisión DiDi (solo referencia informativa)
leyenda_tributaria	Régimen No Responsable de IVA (Art. 512-13 E.T.) - Documento de Control Interno	Leyenda legal en pie de tirilla
sku_empaque_llevar	c1	Código (SKU) del empaque principal a cobrar en pedidos PARA LLEVAR
precio_empaque_llevar	1500	Precio dinámico del empaque (c1) que se cobra al cliente
migracion_demo_fijados_v1	1	Marcado inicial de cuentas demo y fijadas
migracion_empaques_llevar_v1	1	Empaque para llevar por defecto en platos
nombre_local	Mr.Burger	Nombre del restaurante que sale en el recibo
adiciones_disponibles	[{"id": "ad-tocineta", "nombre": "Tocineta Ahumada", "precio": 3000.0, "activo": true}, {"id": "ad-cheddar", "nombre": "Doble Queso Cheddar", "precio": 2500.0, "activo": true}, {"id": "ad-carne", "nombre": "Carne Extra 125g", "precio": 5000.0, "activo": true}, {"id": "ad-huevo", "nombre": "Huevo Frito", "precio": 2000.0, "activo": true}, {"id": "ad-cebolla-caram", "nombre": "Cebolla Caramelizada", "precio": 1500.0, "activo": true}, {"id": "ad-costeno", "nombre": "Queso Costeño Rallado", "precio": 2000.0, "activo": true}, {"id": "ad-papas", "nombre": "Porción Papas Extra", "precio": 4000.0, "activo": true}]	Catálogo de adiciones extra con costo disponibles en comanda
politica_stock_insuficiente	ADVERTIR_Y_PERMITIR	Política ante faltante de stock: BLOQUEAR o ADVERTIR_Y_PERMITIR
\.


--
-- TOC entry 5365 (class 0 OID 16998)
-- Dependencies: 262
-- Data for Name: detalle_compra; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.detalle_compra (id, compra_id, ingrediente_id, cantidad, costo_unitario, costo_total) FROM stdin;
1	1	21	50.0000	795.0000	39750.0000
2	1	22	30.0000	905.0000	27150.0000
3	1	17	20.0000	1184.8740	23697.4800
4	1	18	36.0000	1512.6050	54453.7800
5	1	20	20.0000	2176.4705	43529.4100
6	1	19	8.0000	4952.5500	39620.4000
7	1	36	80.0000	662.5000	53000.0000
8	1	37	2500.0000	35.2000	88000.0000
9	1	16	2000.0000	13.0252	26050.4200
10	1	25	20.0000	672.2690	13445.3800
11	1	24	7500.0000	6.3870	47902.5000
12	1	47	4000.0000	3.5713	14285.2000
13	1	27	3000.0000	8.9076	26722.8000
14	1	68	50.0000	458.8200	22941.0000
15	1	61	50.0000	239.5000	11975.0000
16	1	65	100.0000	77.3109	7731.0900
17	1	67	1200.0000	13.1600	15792.0000
\.


--
-- TOC entry 5349 (class 0 OID 16704)
-- Dependencies: 246
-- Data for Name: detalle_pedido; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.detalle_pedido (id, pedido_id, ronda, producto_id, cantidad, precio_unitario, variacion_snapshot, estado, preparado_en, listo_en, entregado_en, cancelado_en) FROM stdin;
1	1	1	8	1.00	21900.00	null	ENTREGADO	2026-10-09 19:52:23.637378-05	2026-10-09 19:52:23.637378-05	2026-10-09 19:52:23.637378-05	\N
2	2	1	49	2.00	21900.00	{"es_preparado": false, "modificaciones": ["Sin Salsa BBQ"]}	ENTREGADO	2026-10-09 20:06:50.350451-05	2026-10-09 20:07:55.438819-05	2026-10-09 20:08:46.429554-05	\N
3	2	2	35	1.00	35400.00	null	ENTREGADO	2026-10-09 20:07:27.514409-05	2026-10-09 20:07:55.607982-05	2026-10-09 20:08:46.429554-05	\N
\.


--
-- TOC entry 5341 (class 0 OID 16595)
-- Dependencies: 238
-- Data for Name: detalle_receta; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.detalle_receta (id, product_id, ingrediente_id, cantidad, unidad, solo_llevar) FROM stdin;
1	2	1	2.0000	u	f
2	2	2	125.0000	g	f
3	2	3	2.0000	lonja	f
4	2	4	0.7500	u	f
5	2	5	30.0000	g	f
6	2	6	20.0000	ml	f
7	1	1	2.0000	u	f
8	1	2	125.0000	g	f
9	1	3	1.0000	lonja	f
10	1	5	20.0000	g	f
11	1	6	15.0000	ml	f
12	3	1	1.0000	u	f
13	3	6	15.0000	ml	f
14	3	7	1.0000	u	f
15	7	21	1.0000	UNIDAD	f
16	7	10	125.0000	GRAMO	f
17	7	16	20.0000	GRAMO	f
18	7	35	1.0000	LONJA	f
19	7	29	1.0000	UNIDAD	f
20	7	32	20.0000	GRAMO	f
21	7	27	15.0000	GRAMO	f
22	7	42	20.0000	MILILITRO	f
23	7	61	1.0000	UNIDAD	t
24	8	21	1.0000	UNIDAD	f
25	8	10	250.0000	GRAMO	f
26	8	16	30.0000	GRAMO	f
27	8	35	2.0000	LONJA	f
28	8	29	1.0000	UNIDAD	f
29	8	32	20.0000	GRAMO	f
30	8	27	15.0000	GRAMO	f
31	8	42	25.0000	MILILITRO	f
32	8	61	1.0000	UNIDAD	t
33	9	21	1.0000	UNIDAD	f
34	9	12	130.0000	GRAMO	f
35	9	16	20.0000	GRAMO	f
36	9	35	1.0000	LONJA	f
37	9	29	1.0000	UNIDAD	f
38	9	32	20.0000	GRAMO	f
39	9	27	15.0000	GRAMO	f
40	9	42	20.0000	MILILITRO	f
41	9	61	1.0000	UNIDAD	t
42	10	21	1.0000	UNIDAD	f
43	10	12	260.0000	GRAMO	f
44	10	16	30.0000	GRAMO	f
45	10	35	2.0000	LONJA	f
46	10	29	1.0000	UNIDAD	f
47	10	32	20.0000	GRAMO	f
48	10	27	15.0000	GRAMO	f
49	10	42	25.0000	MILILITRO	f
50	10	61	1.0000	UNIDAD	t
51	11	21	1.0000	UNIDAD	f
52	11	10	125.0000	GRAMO	f
53	11	12	130.0000	GRAMO	f
54	11	16	25.0000	GRAMO	f
55	11	35	2.0000	LONJA	f
56	11	29	1.0000	UNIDAD	f
57	11	32	20.0000	GRAMO	f
58	11	27	15.0000	GRAMO	f
59	11	42	25.0000	MILILITRO	f
60	11	61	1.0000	UNIDAD	t
61	12	21	1.0000	UNIDAD	f
62	12	10	250.0000	GRAMO	f
63	12	26	3.0000	UNIDAD	f
64	12	35	2.0000	LONJA	f
65	12	16	30.0000	GRAMO	f
66	12	42	25.0000	MILILITRO	f
67	12	61	1.0000	UNIDAD	t
68	13	21	1.0000	UNIDAD	f
69	13	12	260.0000	GRAMO	f
70	13	26	3.0000	UNIDAD	f
71	13	35	2.0000	LONJA	f
72	13	16	30.0000	GRAMO	f
73	13	42	25.0000	MILILITRO	f
74	13	61	1.0000	UNIDAD	t
75	14	21	1.0000	UNIDAD	f
76	14	11	300.0000	GRAMO	f
77	14	26	3.0000	UNIDAD	f
78	14	35	2.0000	LONJA	f
79	14	16	35.0000	GRAMO	f
80	14	42	25.0000	MILILITRO	f
81	14	61	1.0000	UNIDAD	t
82	15	21	1.0000	UNIDAD	f
83	15	11	150.0000	GRAMO	f
84	15	38	1.0000	LONJA	f
85	15	16	25.0000	GRAMO	f
86	15	31	20.0000	GRAMO	f
87	15	32	20.0000	GRAMO	f
88	15	42	20.0000	MILILITRO	f
89	15	61	1.0000	UNIDAD	t
90	16	21	1.0000	UNIDAD	f
91	16	11	300.0000	GRAMO	f
92	16	38	2.0000	LONJA	f
93	16	16	35.0000	GRAMO	f
94	16	31	20.0000	GRAMO	f
95	16	32	20.0000	GRAMO	f
96	16	42	25.0000	MILILITRO	f
97	16	61	1.0000	UNIDAD	t
98	17	21	1.0000	UNIDAD	f
99	17	10	125.0000	GRAMO	f
100	17	16	30.0000	GRAMO	f
101	17	36	2.0000	LONJA	f
102	17	30	30.0000	GRAMO	f
103	17	44	20.0000	MILILITRO	f
104	17	61	1.0000	UNIDAD	t
105	18	21	1.0000	UNIDAD	f
106	18	10	250.0000	GRAMO	f
107	18	16	40.0000	GRAMO	f
108	18	36	2.0000	LONJA	f
109	18	30	30.0000	GRAMO	f
110	18	44	25.0000	MILILITRO	f
111	18	61	1.0000	UNIDAD	t
112	19	21	1.0000	UNIDAD	f
113	19	12	130.0000	GRAMO	f
114	19	16	30.0000	GRAMO	f
115	19	36	2.0000	LONJA	f
116	19	30	30.0000	GRAMO	f
117	19	44	20.0000	MILILITRO	f
118	19	61	1.0000	UNIDAD	t
119	20	21	1.0000	UNIDAD	f
120	20	12	260.0000	GRAMO	f
121	20	16	40.0000	GRAMO	f
122	20	36	2.0000	LONJA	f
123	20	30	30.0000	GRAMO	f
124	20	44	25.0000	MILILITRO	f
125	20	61	1.0000	UNIDAD	t
126	21	21	1.0000	UNIDAD	f
127	21	10	125.0000	GRAMO	f
128	21	12	130.0000	GRAMO	f
129	21	16	35.0000	GRAMO	f
130	21	36	2.0000	LONJA	f
131	21	30	30.0000	GRAMO	f
132	21	44	25.0000	MILILITRO	f
133	21	61	1.0000	UNIDAD	t
134	22	21	1.0000	UNIDAD	f
135	22	10	125.0000	GRAMO	f
136	22	18	2.0000	UNIDAD	f
137	22	36	1.0000	LONJA	f
138	22	41	15.0000	MILILITRO	f
139	22	61	1.0000	UNIDAD	t
140	23	21	1.0000	UNIDAD	f
141	23	10	250.0000	GRAMO	f
142	23	18	2.0000	UNIDAD	f
143	23	36	2.0000	LONJA	f
144	23	41	20.0000	MILILITRO	f
145	23	61	1.0000	UNIDAD	t
146	24	21	1.0000	UNIDAD	f
147	24	10	125.0000	GRAMO	f
148	24	26	2.0000	UNIDAD	f
149	24	35	1.0000	LONJA	f
150	24	16	20.0000	GRAMO	f
151	24	42	20.0000	MILILITRO	f
152	24	61	1.0000	UNIDAD	t
153	25	21	1.0000	UNIDAD	f
154	25	10	250.0000	GRAMO	f
155	25	26	3.0000	UNIDAD	f
156	25	35	2.0000	LONJA	f
157	25	16	30.0000	GRAMO	f
158	25	42	25.0000	MILILITRO	f
159	25	61	1.0000	UNIDAD	t
160	28	22	1.0000	UNIDAD	f
161	28	19	1.0000	UNIDAD	f
162	28	16	15.0000	GRAMO	f
163	28	36	1.0000	LONJA	f
164	28	27	15.0000	GRAMO	f
165	28	32	10.0000	GRAMO	f
166	28	42	15.0000	MILILITRO	f
167	28	68	1.0000	UNIDAD	t
168	29	22	1.0000	UNIDAD	f
169	29	17	1.0000	UNIDAD	f
170	29	16	15.0000	GRAMO	f
171	29	36	1.0000	LONJA	f
172	29	27	15.0000	GRAMO	f
173	29	32	10.0000	GRAMO	f
174	29	42	15.0000	MILILITRO	f
175	29	68	1.0000	UNIDAD	t
176	30	22	1.0000	UNIDAD	f
177	30	18	2.0000	UNIDAD	f
178	30	16	15.0000	GRAMO	f
179	30	36	1.0000	LONJA	f
180	30	27	15.0000	GRAMO	f
181	30	32	10.0000	GRAMO	f
182	30	42	15.0000	MILILITRO	f
183	30	68	1.0000	UNIDAD	t
184	31	22	1.0000	UNIDAD	f
185	31	20	1.0000	UNIDAD	f
186	31	16	15.0000	GRAMO	f
187	31	35	1.0000	LONJA	f
188	31	42	15.0000	MILILITRO	f
189	31	68	1.0000	UNIDAD	t
190	32	22	1.0000	UNIDAD	f
191	32	20	1.0000	UNIDAD	f
192	32	16	15.0000	GRAMO	f
193	32	36	2.0000	LONJA	f
194	32	25	0.5000	UNIDAD	f
195	32	42	15.0000	MILILITRO	f
196	32	68	1.0000	UNIDAD	t
197	33	22	1.0000	UNIDAD	f
198	33	17	1.0000	UNIDAD	f
199	33	16	15.0000	GRAMO	f
200	33	36	1.0000	LONJA	f
201	33	27	15.0000	GRAMO	f
202	33	32	10.0000	GRAMO	f
203	33	41	15.0000	MILILITRO	f
204	33	42	15.0000	MILILITRO	f
205	33	68	1.0000	UNIDAD	t
206	52	24	150.0000	GRAMO	f
207	52	20	1.0000	UNIDAD	f
208	52	42	20.0000	MILILITRO	f
209	52	43	15.0000	MILILITRO	f
210	52	61	1.0000	UNIDAD	t
211	53	24	180.0000	GRAMO	f
212	53	20	1.0000	UNIDAD	f
213	53	16	20.0000	GRAMO	f
214	53	36	2.0000	LONJA	f
215	53	42	25.0000	MILILITRO	f
216	53	61	1.0000	UNIDAD	t
217	54	24	150.0000	GRAMO	f
218	54	36	2.0000	LONJA	f
219	54	16	20.0000	GRAMO	f
220	54	61	1.0000	UNIDAD	t
221	55	24	150.0000	GRAMO	f
222	55	49	20.0000	MILILITRO	f
223	55	61	1.0000	UNIDAD	t
240	37	12	250.0000	GRAMO	f
241	37	41	30.0000	MILILITRO	f
242	37	24	150.0000	GRAMO	f
243	37	61	1.0000	UNIDAD	t
257	41	25	1.0000	UNIDAD	f
258	41	40	20.0000	GRAMO	f
259	41	10	80.0000	GRAMO	f
260	41	12	80.0000	GRAMO	f
261	41	36	1.0000	LONJA	f
262	41	27	15.0000	GRAMO	f
263	41	42	20.0000	MILILITRO	f
264	41	61	1.0000	UNIDAD	t
265	42	25	1.0000	UNIDAD	f
266	42	40	20.0000	GRAMO	f
267	42	10	150.0000	GRAMO	f
268	42	36	1.0000	LONJA	f
269	42	27	15.0000	GRAMO	f
270	42	42	20.0000	MILILITRO	f
271	42	61	1.0000	UNIDAD	t
272	43	25	1.0000	UNIDAD	f
273	43	40	20.0000	GRAMO	f
274	43	12	150.0000	GRAMO	f
275	43	36	1.0000	LONJA	f
276	43	27	15.0000	GRAMO	f
277	43	42	20.0000	MILILITRO	f
278	43	61	1.0000	UNIDAD	t
279	44	25	1.0000	UNIDAD	f
280	44	40	20.0000	GRAMO	f
281	44	18	2.0000	UNIDAD	f
282	44	36	1.0000	LONJA	f
283	44	27	15.0000	GRAMO	f
284	44	42	20.0000	MILILITRO	f
285	44	61	1.0000	UNIDAD	t
286	45	25	1.0000	UNIDAD	f
287	45	18	1.0000	UNIDAD	f
288	45	36	1.0000	LONJA	f
289	45	61	1.0000	UNIDAD	t
290	46	25	1.0000	UNIDAD	f
291	46	36	2.0000	LONJA	f
292	46	42	20.0000	MILILITRO	f
293	46	61	1.0000	UNIDAD	t
294	47	25	1.0000	UNIDAD	f
295	47	40	20.0000	GRAMO	f
296	47	42	20.0000	MILILITRO	f
297	47	61	1.0000	UNIDAD	t
298	48	25	1.0000	UNIDAD	f
299	48	12	100.0000	GRAMO	f
300	48	36	1.0000	LONJA	f
301	48	61	1.0000	UNIDAD	t
314	26	61	1.0000	UNIDAD	t
315	27	61	1.0000	UNIDAD	t
316	49	86	6.0000	u	f
317	49	44	25.0000	MILILITRO	f
318	49	24	375.0000	g	f
319	49	68	1.0000	u	t
324	50	24	375.0000	GRAMO	f
325	50	47	25.0000	MILILITRO	f
326	50	86	6.0000	u	f
327	50	68	1.0000	u	f
328	51	86	6.0000	u	f
329	51	68	1.0000	u	t
330	51	88	25.0000	ml	f
331	51	24	375.0000	g	f
332	56	26	6.0000	UNIDAD	f
333	56	61	1.0000	UNIDAD	t
334	35	13	200.0000	GRAMO	f
335	35	41	25.0000	MILILITRO	f
336	35	24	150.0000	GRAMO	f
337	35	68	1.0000	u	t
338	35	44	25.0000	ml	f
339	35	89	65.0000	g	f
340	35	48	5.0000	ml	f
341	36	14	200.0000	GRAMO	f
342	36	41	25.0000	MILILITRO	f
343	36	24	125.0000	GRAMO	f
344	36	68	1.0000	u	t
345	36	44	25.0000	ml	f
355	39	12	200.0000	GRAMO	f
356	39	41	25.0000	MILILITRO	f
357	39	24	125.0000	GRAMO	f
358	39	68	1.0000	u	f
359	39	44	25.0000	ml	f
360	38	10	200.0000	GRAMO	f
361	38	41	20.0000	MILILITRO	f
362	38	24	125.0000	GRAMO	f
363	38	68	1.0000	u	t
369	40	10	100.0000	GRAMO	f
370	40	12	100.0000	GRAMO	f
371	40	41	25.0000	MILILITRO	f
372	40	24	125.0000	GRAMO	f
373	40	68	1.0000	u	f
374	40	44	25.0000	ml	f
387	34	15	200.0000	GRAMO	f
388	34	44	25.0000	MILILITRO	f
389	34	41	25.0000	ml	f
390	34	24	125.0000	g	f
391	34	89	65.0000	g	f
392	34	68	1.0000	u	t
\.


--
-- TOC entry 5367 (class 0 OID 17026)
-- Dependencies: 264
-- Data for Name: historial_accion; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.historial_accion (id, usuario_id, accion, entidad, entidad_id, detalle, creado_en, es_demo) FROM stdin;
1	1	CREAR_USUARIO	usuario	5	usuario=felix123 rol=cajero fijado=True demo=False	2026-10-08 20:12:39.608194-05	f
2	5	ABRIR_TURNO	cierre	1	fondo=521650.00	2026-10-08 20:49:51.192555-05	f
3	5	CERRAR_TURNO	cierre	1	ventas=0 efectivo_final=521650.00	2026-10-08 20:56:01.042321-05	f
4	1	MODIFICAR_INGREDIENTE	ingrediente	21	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 17:48:37.825464-05	f
5	1	AJUSTAR_INVENTARIO	ingrediente	21	Pan Hamburguesa: delta=62	2026-10-09 17:48:54.576245-05	f
6	1	MODIFICAR_INGREDIENTE	ingrediente	21	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 17:50:35.5137-05	f
7	1	AJUSTAR_INVENTARIO	ingrediente	22	Pan Perro: delta=32	2026-10-09 17:50:47.867365-05	f
8	1	MODIFICAR_INGREDIENTE	ingrediente	22	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 17:51:14.593363-05	f
9	1	AJUSTAR_INVENTARIO	ingrediente	23	Pan Brillo: delta=5	2026-10-09 17:51:27.937801-05	f
10	1	MODIFICAR_INGREDIENTE	ingrediente	23	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 17:51:43.21931-05	f
11	1	MODIFICAR_INGREDIENTE	ingrediente	18	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 17:53:12.788809-05	f
12	1	AJUSTAR_INVENTARIO	ingrediente	18	Salchicha Ranchera: delta=6	2026-10-09 17:53:26.889469-05	f
13	1	AJUSTAR_INVENTARIO	ingrediente	17	Salchicha Ideal: delta=9	2026-10-09 17:59:27.168965-05	f
14	1	MODIFICAR_INGREDIENTE	ingrediente	17	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 17:59:39.231669-05	f
15	1	AJUSTAR_INVENTARIO	ingrediente	19	Salchicha Suiza: delta=16	2026-10-09 17:59:55.487931-05	f
16	1	MODIFICAR_INGREDIENTE	ingrediente	19	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 18:00:22.12125-05	f
17	1	AJUSTAR_INVENTARIO	ingrediente	20	Salchicha Americana: delta=16	2026-10-09 18:00:46.567308-05	f
18	1	AJUSTAR_INVENTARIO	ingrediente	51	Gaseosa 400ml: delta=59	2026-10-09 18:01:24.342034-05	f
19	1	MODIFICAR_INGREDIENTE	ingrediente	51	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 18:01:33.369152-05	f
20	1	MODIFICAR_INGREDIENTE	ingrediente	52	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 18:02:22.111273-05	f
21	1	AJUSTAR_INVENTARIO	ingrediente	52	Gaseosa litro 1/5: delta=34	2026-10-09 18:02:27.216044-05	f
22	1	CREAR_INGREDIENTE	ingrediente	85	Coca Cola 400ml	2026-10-09 18:03:34.827748-05	f
23	1	AJUSTAR_INVENTARIO	ingrediente	53	Agua Botella: delta=59	2026-10-09 18:03:50.346715-05	f
24	1	MODIFICAR_INGREDIENTE	ingrediente	53	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 18:03:58.88425-05	f
25	1	AJUSTAR_INVENTARIO	ingrediente	41	Chimichurry: delta=4000	2026-10-09 18:04:20.288972-05	f
26	1	MODIFICAR_INGREDIENTE	ingrediente	41	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 18:04:38.907545-05	f
27	1	AJUSTAR_INVENTARIO	ingrediente	42	Salsa Mr Burger: delta=4000	2026-10-09 18:05:06.445201-05	f
28	1	MODIFICAR_INGREDIENTE	ingrediente	42	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 18:05:21.072165-05	f
29	1	MODIFICAR_INGREDIENTE	ingrediente	46	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 18:06:08.039296-05	f
30	7	MODIFICAR_INGREDIENTE	ingrediente	46	costo_unitario, nombre	2026-10-09 18:16:50.444703-05	f
31	1	AJUSTAR_INVENTARIO	ingrediente	46	Salsa Piña Dieffer: delta=8000	2026-10-09 18:22:41.666879-05	f
32	1	AJUSTAR_INVENTARIO	ingrediente	43	Salsa de Tomate: delta=4000	2026-10-09 18:22:57.796359-05	f
33	1	MODIFICAR_INGREDIENTE	ingrediente	43	categoria_insumo_id, costo_unitario, nombre, precio_venta, stock_minimo, tipo_articulo	2026-10-09 18:23:09.345197-05	f
34	1	REGISTRAR_COMPRA	compra	1	proveedor_id=None total=556046.4600	2026-10-09 19:12:24.791171-05	f
35	5	ABRIR_TURNO	cierre	2	fondo=100000.00	2026-10-09 19:50:00.923797-05	f
36	5	CREAR_PEDIDO	pedido	1	canal=MOSTRADOR total=23400.00	2026-10-09 19:51:17.256828-05	f
37	5	ENVIAR_COCINA	pedido	1	consecutivo=1	2026-10-09 19:51:17.790682-05	f
38	5	CAMBIAR_TIPO_CONSUMO	pedido	1	LLEVAR->LOCAL recargo=0 total=21900.00	2026-10-09 19:51:42.676254-05	f
39	5	CAMBIAR_TIPO_CONSUMO	pedido	1	LOCAL->LLEVAR recargo=1500.00 total=23400.00	2026-10-09 19:51:57.362588-05	f
40	5	COBRAR_PEDIDO	pedido	1	total=23400.00 metodos=EFECTIVO	2026-10-09 19:52:23.637378-05	f
41	3	CREAR_PEDIDO	pedido	2	canal=MESA total=43800.00	2026-10-09 20:06:15.732031-05	t
42	3	ENVIAR_COCINA	pedido	2	consecutivo=2	2026-10-09 20:06:17.864635-05	t
43	4	ACEPTAR_PREPARACION	detalle	2	pedido=2 producto=Alitas BBQ (6 piezas)	2026-10-09 20:06:50.350451-05	t
44	3	AGREGAR_RONDA	pedido	2	consecutivo=2 ronda=2	2026-10-09 20:07:12.364488-05	t
45	4	ACEPTAR_PREPARACION	detalle	3	pedido=2 producto=Asado Baby	2026-10-09 20:07:27.514409-05	t
46	4	MARCAR_LISTO	detalle	2	pedido=2 producto=Alitas BBQ (6 piezas)	2026-10-09 20:07:55.438819-05	t
47	4	MARCAR_LISTO	detalle	3	pedido=2 producto=Asado Baby	2026-10-09 20:07:55.607982-05	t
48	2	CAMBIAR_TIPO_CONSUMO	pedido	2	LOCAL->LLEVAR recargo=4500.00 total=83700.00	2026-10-09 20:08:36.012912-05	t
49	2	CAMBIAR_TIPO_CONSUMO	pedido	2	LLEVAR->LOCAL recargo=0 total=79200.00	2026-10-09 20:08:37.952476-05	t
50	2	COBRAR_PEDIDO	pedido	2	total=79200.00 metodos=EFECTIVO	2026-10-09 20:08:46.429554-05	t
51	1	CREAR_INGREDIENTE	ingrediente	86	Alitas	2026-10-09 20:24:00.535645-05	f
52	1	CREAR_INGREDIENTE	ingrediente	87	Porta Perro	2026-10-09 20:24:35.259226-05	f
53	1	MODIFICAR_RECETA	producto	49	lineas=4	2026-10-09 20:26:19.414206-05	f
54	1	MODIFICAR_RECETA	producto	50	lineas=4	2026-10-09 20:26:57.467216-05	f
55	1	MODIFICAR_RECETA	producto	50	lineas=4	2026-10-09 20:27:59.077361-05	f
56	1	CREAR_INGREDIENTE	ingrediente	88	Salsa Picante	2026-10-09 20:28:47.140604-05	f
57	1	MODIFICAR_RECETA	producto	51	lineas=4	2026-10-09 20:29:55.392827-05	f
58	1	MODIFICAR_RECETA	producto	56	lineas=2	2026-10-09 20:30:24.041574-05	f
59	1	CREAR_INGREDIENTE	ingrediente	89	Porcion Ensalda	2026-10-09 20:33:37.12017-05	f
60	1	MODIFICAR_RECETA	producto	35	lineas=7	2026-10-09 20:34:09.750683-05	f
61	1	MODIFICAR_PRODUCTO	producto	67	permite_adiciones	2026-10-09 20:34:26.563198-05	f
62	1	MODIFICAR_PRECIO	producto	36	Churrasco a la Plancha: 32200.00 -> 32200	2026-10-09 20:34:58.354488-05	f
63	1	MODIFICAR_RECETA	producto	36	lineas=5	2026-10-09 20:36:54.322381-05	f
64	1	MODIFICAR_RECETA	producto	39	lineas=4	2026-10-09 20:38:30.703925-05	f
65	1	MODIFICAR_RECETA	producto	39	lineas=5	2026-10-09 20:38:40.450397-05	f
70	1	MODIFICAR_COMBO	producto	27	componentes=2	2026-10-09 20:46:25.666128-05	f
71	1	MODIFICAR_COMBO	producto	27	componentes=2	2026-10-09 20:46:37.567975-05	f
66	1	MODIFICAR_RECETA	producto	39	lineas=5	2026-10-09 20:43:46.167553-05	f
67	1	MODIFICAR_RECETA	producto	38	lineas=4	2026-10-09 20:44:03.597128-05	f
69	1	MODIFICAR_RECETA	producto	40	lineas=6	2026-10-09 20:44:53.988953-05	f
72	1	MODIFICAR_COMBO	producto	26	componentes=2	2026-10-09 20:46:43.614737-05	f
74	1	MODIFICAR_RECETA	producto	34	lineas=6	2026-10-09 20:48:56.313635-05	f
68	1	MODIFICAR_RECETA	producto	40	lineas=5	2026-10-09 20:44:40.429791-05	f
73	1	MODIFICAR_RECETA	producto	34	lineas=6	2026-10-09 20:47:46.192203-05	f
75	1	MODIFICAR_RECETA	producto	34	lineas=6	2026-10-09 20:49:00.669315-05	f
\.


--
-- TOC entry 5339 (class 0 OID 16560)
-- Dependencies: 236
-- Data for Name: ingrediente; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.ingrediente (id, categoria_insumo_id, nombre, unidad_base, costo_unitario, costo_proveedor, stock_actual, stock_minimo, stock_ideal, proveedor_id, activo, creado_en, actualizado_en, tipo_articulo, precio_venta) FROM stdin;
11	1	Carne Angus	GRAMO	50.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-08 20:07:45.049354-05	INSUMO_RECETA	0.00
12	1	Pollo (Pechuga)	GRAMO	25.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-08 20:07:45.049354-05	INSUMO_RECETA	0.00
14	1	Churrasco	GRAMO	40.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-08 20:07:45.049354-05	INSUMO_RECETA	0.00
15	1	Costilla	GRAMO	35.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-08 20:07:45.049354-05	INSUMO_RECETA	0.00
26	6	Aros de Cebolla	UNIDAD	400.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.056034-05	2026-10-08 20:07:45.056034-05	INSUMO_RECETA	0.00
28	3	Arepas	UNIDAD	600.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.056034-05	2026-10-08 20:07:45.056034-05	INSUMO_RECETA	0.00
30	2	Cebolla Cabezona	GRAMO	2.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.057262-05	2026-10-08 20:07:45.057262-05	INSUMO_RECETA	0.00
31	2	Cebolla Morada	GRAMO	3.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.057262-05	2026-10-08 20:07:45.057262-05	INSUMO_RECETA	0.00
33	2	Lechuga Crespa	GRAMO	5.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.057262-05	2026-10-08 20:07:45.057262-05	INSUMO_RECETA	0.00
34	2	Limones	UNIDAD	300.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.057262-05	2026-10-08 20:07:45.057262-05	INSUMO_RECETA	0.00
38	4	Queso Cheddar	LONJA	900.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-08 20:07:45.05839-05	INSUMO_RECETA	0.00
39	4	Leche	MILILITRO	3.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-08 20:07:45.05839-05	INSUMO_RECETA	0.00
40	4	Mantequilla	GRAMO	15.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-08 20:07:45.05839-05	INSUMO_RECETA	0.00
45	5	Mayonesa	MILILITRO	9.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-08 20:07:45.05839-05	INSUMO_RECETA	0.00
48	5	Vinagreta	MILILITRO	15.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-08 20:07:45.05839-05	INSUMO_RECETA	0.00
50	7	Cerveza	UNIDAD	3500.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-08 20:07:45.059761-05	VENTA_DIRECTA	0.00
54	7	Pulpa Maracuyá	UNIDAD	1200.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-08 20:07:45.059761-05	INSUMO_RECETA	0.00
55	7	Pulpa Mango	UNIDAD	1200.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-08 20:07:45.059761-05	INSUMO_RECETA	0.00
56	7	Pulpa Mandarina	UNIDAD	1200.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-08 20:07:45.059761-05	INSUMO_RECETA	0.00
57	7	Pulpa Fresa	UNIDAD	1200.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-08 20:07:45.059761-05	INSUMO_RECETA	0.00
58	7	Pulpa Mora	UNIDAD	1200.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-08 20:07:45.059761-05	INSUMO_RECETA	0.00
59	7	Pulpa Guanábana	UNIDAD	1500.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-08 20:07:45.059761-05	INSUMO_RECETA	0.00
60	7	Limonada de Coco (Insumos Base)	PORCION	2000.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-08 20:07:45.059761-05	INSUMO_RECETA	0.00
62	8	Vaso Grande	UNIDAD	300.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-08 20:07:45.089551-05	DESECHABLE_SERVICIO	0.00
63	8	Vaso Pequeño	UNIDAD	200.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-08 20:07:45.089551-05	DESECHABLE_SERVICIO	0.00
64	8	Vaso 12oz	UNIDAD	250.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-08 20:07:45.089551-05	DESECHABLE_SERVICIO	0.00
66	8	Pitillo	UNIDAD	20.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-08 20:07:45.089551-05	DESECHABLE_SERVICIO	0.00
69	8	Bolsa Empaque	UNIDAD	150.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-08 20:07:45.089551-05	DESECHABLE_SERVICIO	0.00
70	8	Papel Aluminio	GRAMO	5.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-08 20:07:45.089551-05	DESECHABLE_SERVICIO	0.00
71	10	Axion (Lavaplatos)	UNIDAD	5500.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
72	10	Jabón en polvo	UNIDAD	4500.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
10	1	Carne de res	GRAMO	30.0000	\N	-250.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-09 19:52:23.637378-05	INSUMO_RECETA	0.00
21	3	Pan Hamburguesa	UNIDAD	795.0000	\N	111.0000	10.0000	\N	\N	t	2026-10-08 20:07:45.056034-05	2026-10-09 19:52:23.637378-05	INSUMO_RECETA	0.00
29	2	Tomate	UNIDAD	500.0000	\N	-1.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.057262-05	2026-10-09 19:52:23.637378-05	INSUMO_RECETA	0.00
32	2	Lechuga Batavia	GRAMO	4.0000	\N	-20.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.057262-05	2026-10-09 19:52:23.637378-05	INSUMO_RECETA	0.00
23	3	Pan Brillo	UNIDAD	1000.0000	\N	5.0000	3.0000	\N	\N	t	2026-10-08 20:07:45.056034-05	2026-10-09 17:51:43.21931-05	INSUMO_RECETA	0.00
35	4	Queso Americano	LONJA	800.0000	\N	-2.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 19:52:23.637378-05	INSUMO_RECETA	0.00
53	7	Agua Botella	UNIDAD	0.0000	\N	59.0000	10.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-09 18:03:58.88425-05	VENTA_DIRECTA	0.00
42	5	Salsa Mr Burger	MILILITRO	0.0000	\N	3975.0000	200.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 19:52:23.637378-05	INSUMO_RECETA	0.00
51	7	Gaseosa 400ml	UNIDAD	0.0000	\N	59.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-09 18:01:33.369152-05	VENTA_DIRECTA	0.00
52	7	Gaseosa litro 1/5	UNIDAD	0.0000	\N	34.0000	10.0000	\N	\N	t	2026-10-08 20:07:45.059761-05	2026-10-09 18:02:27.216044-05	VENTA_DIRECTA	0.00
46	5	Salsa Piña Dieffer	MILILITRO	100.0000	\N	8000.0000	200.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 18:22:41.666879-05	INSUMO_RECETA	0.00
41	5	Chimichurry	MILILITRO	0.0000	\N	3970.0000	200.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 20:07:27.514409-05	INSUMO_RECETA	0.00
43	5	Salsa de Tomate	MILILITRO	0.0000	\N	4000.0000	200.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 18:23:09.345197-05	INSUMO_RECETA	0.00
22	3	Pan Perro	UNIDAD	905.0000	\N	62.0000	10.0000	\N	\N	t	2026-10-08 20:07:45.056034-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
17	1	Salchicha Ideal	UNIDAD	1184.8740	\N	29.0000	3.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
18	1	Salchicha Ranchera	UNIDAD	1512.6050	\N	42.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
20	1	Salchicha Americana	UNIDAD	2176.4705	\N	36.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
19	1	Salchicha Suiza	UNIDAD	4952.5500	\N	24.0000	3.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
36	4	Queso Tajado	LONJA	662.5000	\N	80.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
44	5	Salsa BBQ	MILILITRO	10.0000	\N	-80.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 20:06:50.350451-05	INSUMO_RECETA	0.00
49	6	Aceite	MILILITRO	6.0000	\N	-60.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 20:06:50.350451-05	INSUMO_RECETA	0.00
13	1	Baby Beef	GRAMO	40.0000	\N	-250.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-09 20:07:27.514409-05	INSUMO_RECETA	0.00
73	10	Límpido	UNIDAD	3000.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
74	10	Fabuloso	UNIDAD	4000.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
75	10	Esponjas	UNIDAD	1500.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
76	10	Papel de baño	UNIDAD	2500.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
77	10	Rollos impresora térmica	UNIDAD	3500.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
78	10	Guantes de cocina	UNIDAD	12000.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
79	10	Tapabocas	UNIDAD	800.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.090937-05	2026-10-08 20:07:45.090937-05	GASTO_OPERATIVO	0.00
84	10	Papel de cocina	UNIDAD	3500.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:09:03.262403-05	2026-10-08 20:09:03.262403-05	GASTO_OPERATIVO	0.00
80	8	Bolsa T20 (Para Llevar Pequeña)	UNIDAD	100.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:09:03.262403-05	2026-10-08 20:09:03.262403-05	DESECHABLE_SERVICIO	200.00
81	8	Bolsa T25 (Para Llevar Mediana)	UNIDAD	150.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:09:03.262403-05	2026-10-08 20:09:03.262403-05	DESECHABLE_SERVICIO	300.00
82	8	Bolsa T30 (Para Llevar Grande)	UNIDAD	200.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:09:03.262403-05	2026-10-08 20:09:03.262403-05	DESECHABLE_SERVICIO	400.00
83	8	Bolsa T40 (Para Llevar Extra Grande)	UNIDAD	300.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-08 20:09:03.262403-05	2026-10-08 20:09:03.262403-05	DESECHABLE_SERVICIO	500.00
37	4	Queso Vitafilado	GRAMO	35.2000	\N	2500.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
25	6	Mazorcas	UNIDAD	672.2690	\N	20.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.056034-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
47	5	Mostaza	MILILITRO	3.5713	\N	4000.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.05839-05	2026-10-09 19:12:24.791171-05	INSUMO_RECETA	0.00
85	7	Coca Cola 400ml	UNIDAD	0.0000	\N	175.0000	10.0000	\N	\N	t	2026-10-09 18:03:34.827748-05	2026-10-09 18:03:34.827748-05	INSUMO_RECETA	0.00
16	1	Tocineta	GRAMO	13.0252	\N	1970.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.049354-05	2026-10-09 19:52:23.637378-05	INSUMO_RECETA	0.00
27	6	Ripio de Papa	GRAMO	8.9076	\N	2985.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.056034-05	2026-10-09 19:52:23.637378-05	INSUMO_RECETA	0.00
24	6	Papa a la Francesa	GRAMO	6.3870	\N	7050.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.056034-05	2026-10-09 20:07:27.514409-05	INSUMO_RECETA	0.00
1	\N	Pan	UNIDAD	500.0000	Pan baguette $500/unidad	40.0000	10.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
2	\N	Carne	GRAMO	56.0000	Kg de carne $56.000	5000.0000	1500.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
3	\N	Queso Cheddar	LONJA	800.0000	Lonja de cheddar $800	100.0000	30.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
4	\N	Tomate	UNIDAD	2000.0000	Tomate $2.000/unidad	20.0000	5.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
65	8	Copa y Tapa	UNIDAD	77.3109	\N	100.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-09 19:12:24.791171-05	DESECHABLE_SERVICIO	0.00
67	8	Servilletas	UNIDAD	13.1600	\N	1200.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-09 19:12:24.791171-05	DESECHABLE_SERVICIO	0.00
5	\N	Lechuga	GRAMO	25.0000	Kg de lechuga $25.000	1500.0000	400.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
6	\N	Salsa	MILILITRO	2.0000	Galón de salsa $8.000	5000.0000	1000.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
7	\N	Salchicha	UNIDAD	1500.0000	Paquete x10 $15.000	60.0000	20.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
68	8	P1 (Porta Perro Caliente)	UNIDAD	350.0000	\N	50.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-09 19:12:24.791171-05	DESECHABLE_SERVICIO	500.00
61	8	C1 (Empaque Térmico)	UNIDAD	500.0000	\N	49.0000	0.0000	\N	\N	t	2026-10-08 20:07:45.089551-05	2026-10-09 20:30:24.041574-05	DESECHABLE_SERVICIO	400.00
8	\N	Papas	GRAMO	3.0000	Kg de papa $3.000	8000.0000	2000.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
9	\N	Gaseosa	UNIDAD	2000.0000	Caja x24 $48.000	96.0000	24.0000	\N	\N	f	2026-10-08 20:07:44.203042-05	2026-10-08 20:07:44.203042-05	INSUMO_RECETA	0.00
86	1	Alitas	UNIDAD	0.0000	\N	10.0000	5.0000	\N	\N	t	2026-10-09 20:24:00.535645-05	2026-10-09 20:24:00.535645-05	INSUMO_RECETA	0.00
87	8	Porta Perro	UNIDAD	0.0000	\N	0.0000	10.0000	\N	\N	t	2026-10-09 20:24:35.259226-05	2026-10-09 20:24:35.259226-05	DESECHABLE_SERVICIO	300.00
88	\N	Salsa Picante	MILILITRO	150.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-09 20:28:47.140604-05	2026-10-09 20:28:47.140604-05	INSUMO_RECETA	0.00
89	\N	Porcion Ensalda	GRAMO	1000.0000	\N	0.0000	0.0000	\N	\N	t	2026-10-09 20:33:37.12017-05	2026-10-09 20:33:37.12017-05	INSUMO_RECETA	0.00
\.


--
-- TOC entry 5345 (class 0 OID 16643)
-- Dependencies: 242
-- Data for Name: mesa; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.mesa (id, numero, estado, activo) FROM stdin;
1	1	DISPONIBLE	t
2	2	DISPONIBLE	t
4	4	DISPONIBLE	t
5	5	DISPONIBLE	t
6	6	DISPONIBLE	t
7	7	DISPONIBLE	t
8	8	DISPONIBLE	t
9	9	DISPONIBLE	t
3	3	DISPONIBLE	t
\.


--
-- TOC entry 5355 (class 0 OID 16796)
-- Dependencies: 252
-- Data for Name: movimiento_caja; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.movimiento_caja (id, usuario_id, tipo, categoria, concepto, descripcion, valor, pedido_id, vale_id, creado_en, cierre_id, es_demo) FROM stdin;
1	5	ENTRADA	CAMBIO_INICIAL	Fondo inicial de caja	Monto inicial con el que abre el turno	521650.00	\N	\N	2026-10-08 20:49:51.192555-05	1	f
2	5	ENTRADA	CAMBIO_INICIAL	Fondo inicial de caja	Monto inicial con el que abre el turno	100000.00	\N	\N	2026-10-09 19:50:00.923797-05	2	f
\.


--
-- TOC entry 5357 (class 0 OID 16831)
-- Dependencies: 254
-- Data for Name: movimiento_inventario; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.movimiento_inventario (id, ingrediente_id, pedido_id, compra_id, usuario_id, cantidad, unidad, saldo_anterior, saldo_nuevo, costo_unitario_momento, tipo, referencia, creado_en, es_demo) FROM stdin;
1	21	\N	\N	1	62.0000	UNIDAD	0.0000	62.0000	800.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 17:48:54.576245-05	f
2	22	\N	\N	1	32.0000	UNIDAD	0.0000	32.0000	700.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 17:50:47.867365-05	f
3	23	\N	\N	1	5.0000	UNIDAD	0.0000	5.0000	900.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 17:51:27.937801-05	f
4	18	\N	\N	1	6.0000	UNIDAD	0.0000	6.0000	3025.2100	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 17:53:26.889469-05	f
5	17	\N	\N	1	9.0000	UNIDAD	0.0000	9.0000	1200.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 17:59:27.168965-05	f
6	19	\N	\N	1	16.0000	UNIDAD	0.0000	16.0000	1800.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 17:59:55.487931-05	f
7	20	\N	\N	1	16.0000	UNIDAD	0.0000	16.0000	1400.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 18:00:46.567308-05	f
8	51	\N	\N	1	59.0000	UNIDAD	0.0000	59.0000	2500.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 18:01:24.342034-05	f
9	52	\N	\N	1	34.0000	UNIDAD	0.0000	34.0000	0.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 18:02:27.216044-05	f
10	85	\N	\N	1	175.0000	UNIDAD	0.0000	175.0000	0.0000	AJUSTE	Stock inicial al crear el ingrediente	2026-10-09 18:03:34.827748-05	f
11	53	\N	\N	1	59.0000	UNIDAD	0.0000	59.0000	2000.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 18:03:50.346715-05	f
12	41	\N	\N	1	4000.0000	MILILITRO	0.0000	4000.0000	10.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 18:04:20.288972-05	f
13	42	\N	\N	1	4000.0000	MILILITRO	0.0000	4000.0000	12.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 18:05:06.445201-05	f
14	46	\N	\N	1	8000.0000	MILILITRO	0.0000	8000.0000	100.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 18:22:41.666879-05	f
15	43	\N	\N	1	4000.0000	MILILITRO	0.0000	4000.0000	8.0000	AJUSTE	Ajuste manual de stock por administrador	2026-10-09 18:22:57.796359-05	f
16	21	\N	1	1	50.0000	u	\N	\N	\N	COMPRA	Compra #1 - Pan Hamburguesa	2026-10-09 19:12:24.791171-05	f
17	22	\N	1	1	30.0000	u	\N	\N	\N	COMPRA	Compra #1 - Pan Perro	2026-10-09 19:12:24.791171-05	f
18	17	\N	1	1	20.0000	u	\N	\N	\N	COMPRA	Compra #1 - Salchicha Ideal	2026-10-09 19:12:24.791171-05	f
19	18	\N	1	1	36.0000	u	\N	\N	\N	COMPRA	Compra #1 - Salchicha Ranchera	2026-10-09 19:12:24.791171-05	f
20	20	\N	1	1	20.0000	u	\N	\N	\N	COMPRA	Compra #1 - Salchicha Americana	2026-10-09 19:12:24.791171-05	f
21	19	\N	1	1	8.0000	u	\N	\N	\N	COMPRA	Compra #1 - Salchicha Suiza	2026-10-09 19:12:24.791171-05	f
22	36	\N	1	1	80.0000	u	\N	\N	\N	COMPRA	Compra #1 - Queso Tajado	2026-10-09 19:12:24.791171-05	f
23	37	\N	1	1	2500.0000	u	\N	\N	\N	COMPRA	Compra #1 - Queso Vitafilado	2026-10-09 19:12:24.791171-05	f
24	16	\N	1	1	2000.0000	u	\N	\N	\N	COMPRA	Compra #1 - Tocineta	2026-10-09 19:12:24.791171-05	f
25	25	\N	1	1	20.0000	u	\N	\N	\N	COMPRA	Compra #1 - Mazorcas	2026-10-09 19:12:24.791171-05	f
26	24	\N	1	1	7500.0000	u	\N	\N	\N	COMPRA	Compra #1 - Papa a la Francesa	2026-10-09 19:12:24.791171-05	f
27	47	\N	1	1	4000.0000	u	\N	\N	\N	COMPRA	Compra #1 - Mostaza	2026-10-09 19:12:24.791171-05	f
28	27	\N	1	1	3000.0000	u	\N	\N	\N	COMPRA	Compra #1 - Ripio de Papa	2026-10-09 19:12:24.791171-05	f
29	68	\N	1	1	50.0000	u	\N	\N	\N	COMPRA	Compra #1 - P1 (Porta Perro Caliente)	2026-10-09 19:12:24.791171-05	f
30	61	\N	1	1	50.0000	u	\N	\N	\N	COMPRA	Compra #1 - C1 (Empaque Térmico)	2026-10-09 19:12:24.791171-05	f
31	65	\N	1	1	100.0000	u	\N	\N	\N	COMPRA	Compra #1 - Copa y Tapa	2026-10-09 19:12:24.791171-05	f
32	67	\N	1	1	1200.0000	u	\N	\N	\N	COMPRA	Compra #1 - Servilletas	2026-10-09 19:12:24.791171-05	f
33	10	1	\N	5	-250.0000	GRAMO	0.0000	-250.0000	30.0000	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
34	16	1	\N	5	-30.0000	GRAMO	2000.0000	1970.0000	13.0252	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
35	21	1	\N	5	-1.0000	UNIDAD	112.0000	111.0000	795.0000	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
36	27	1	\N	5	-15.0000	GRAMO	3000.0000	2985.0000	8.9076	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
37	29	1	\N	5	-1.0000	UNIDAD	0.0000	-1.0000	500.0000	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
38	32	1	\N	5	-20.0000	GRAMO	0.0000	-20.0000	4.0000	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
39	35	1	\N	5	-2.0000	LONJA	0.0000	-2.0000	800.0000	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
40	42	1	\N	5	-25.0000	MILILITRO	4000.0000	3975.0000	0.0000	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
41	61	1	\N	5	-1.0000	UNIDAD	50.0000	49.0000	500.0000	VENTA	Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res	2026-10-09 19:52:23.637378-05	f
42	24	2	\N	4	-300.0000	GRAMO	7500.0000	7200.0000	6.3870	VENTA	Pedido #2 - Alitas BBQ (6 piezas)	2026-10-09 20:06:50.350451-05	t
43	44	2	\N	4	-80.0000	MILILITRO	0.0000	-80.0000	10.0000	VENTA	Pedido #2 - Alitas BBQ (6 piezas)	2026-10-09 20:06:50.350451-05	t
44	49	2	\N	4	-60.0000	MILILITRO	0.0000	-60.0000	6.0000	VENTA	Pedido #2 - Alitas BBQ (6 piezas)	2026-10-09 20:06:50.350451-05	t
45	13	2	\N	4	-250.0000	GRAMO	0.0000	-250.0000	40.0000	VENTA	Pedido #2 - Asado Baby	2026-10-09 20:07:27.514409-05	t
46	24	2	\N	4	-150.0000	GRAMO	7200.0000	7050.0000	6.3870	VENTA	Pedido #2 - Asado Baby	2026-10-09 20:07:27.514409-05	t
47	41	2	\N	4	-30.0000	MILILITRO	4000.0000	3970.0000	0.0000	VENTA	Pedido #2 - Asado Baby	2026-10-09 20:07:27.514409-05	t
48	86	\N	\N	1	10.0000	UNIDAD	0.0000	10.0000	0.0000	AJUSTE	Stock inicial al crear el ingrediente	2026-10-09 20:24:00.535645-05	f
\.


--
-- TOC entry 5351 (class 0 OID 16736)
-- Dependencies: 248
-- Data for Name: pago; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.pago (id, pedido_id, cierre_id, metodo, monto, recibido, cambio, didi_orden_id, estado, usuario_id, devuelto_por, devuelto_en, motivo_devolucion, pagado_en, es_demo) FROM stdin;
1	1	\N	EFECTIVO	23400.00	30000.00	6600.00	\N	VALIDO	5	\N	\N	\N	2026-10-09 19:52:23.637378-05	f
2	2	\N	EFECTIVO	79200.00	100000.00	20800.00	\N	VALIDO	2	\N	\N	\N	2026-10-09 20:08:46.429554-05	t
\.


--
-- TOC entry 5347 (class 0 OID 16659)
-- Dependencies: 244
-- Data for Name: pedido; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.pedido (id, consecutivo, fecha_dia, canal, mesa_id, usuario_id, estado, cliente, telefono, direccion, nota_interna, didi_orden_id, subtotal, iva, total, motivo_cancelacion, idempotency_key, creado_en, enviado_en, finalizado_en, pagado_en, cancelado_en, tipo_consumo, recargo_empaque, es_demo) FROM stdin;
1	1	2026-10-09	MOSTRADOR	\N	5	PAGADO	\N	\N	\N	\N	\N	21900.00	0.00	23400.00	\N	\N	2026-10-09 19:51:17.256828-05	2026-10-09 19:51:17.790682-05	\N	2026-10-09 19:52:23.637378-05	\N	LLEVAR	1500.00	f
2	2	2026-10-09	MESA	3	3	PAGADO	\N	\N	\N	\N	\N	79200.00	0.00	79200.00	\N	ord-1791594365289-rsjn5	2026-10-09 20:06:15.732031-05	2026-10-09 20:06:17.864635-05	2026-10-09 20:07:55.652166-05	2026-10-09 20:08:46.429554-05	\N	LOCAL	0.00	t
\.


--
-- TOC entry 5361 (class 0 OID 16930)
-- Dependencies: 258
-- Data for Name: preparado; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.preparado (id, producto_id, pedido_origen_id, detalle_origen_id, variacion_snapshot, cantidad, estado, pedido_nuevo_id, usuario_id, creado_en, asignado_en, descartado_en, motivo_descarte, es_demo) FROM stdin;
\.


--
-- TOC entry 5333 (class 0 OID 16507)
-- Dependencies: 230
-- Data for Name: producto; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.producto (id, categoria_id, nombre, descripcion, imagen_url, precio, iva_incluido, manual_disponible, activo, creado_en, actualizado_en, empaque_llevar_id, permite_adiciones) FROM stdin;
7	1	Hamburguesa Especial Res	Carne de res, tocineta, queso, tomate, lechuga, ripio y salsas	\N	18900.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
8	1	Hamburguesa Especial Doble Res	Doble carne de res, tocineta, queso, tomate, lechuga, ripio y salsas	\N	21900.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
9	1	Hamburguesa Especial Pollo	Pechuga de pollo, tocineta, queso, tomate, lechuga, ripio y salsas	\N	21600.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
10	1	Hamburguesa Especial Doble Pollo	Doble pechuga de pollo, tocineta, queso, tomate, lechuga, ripio y salsas	\N	24600.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
11	1	Hamburguesa Especial Mixta	Carne de res y pollo, tocineta, queso, tomate, lechuga, ripio y salsas	\N	25900.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
12	1	Hamburguesa Mr. Burger Doble Res	Todo doble (no vegetales, no ripio): deliciosos aros de cebolla fritos, doble queso americano y más tocineta	\N	25700.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
13	1	Hamburguesa Mr. Burger Doble Pollo	Todo doble con pollo (no vegetales, no ripio): aros de cebolla fritos, doble queso americano y tocineta	\N	25900.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
14	1	Hamburguesa Mr. Burger Doble Angus	Doble carne Angus, aros de cebolla fritos, doble queso americano y tocineta	\N	35000.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
15	1	Hamburguesa Angus Sencilla	Pan artesanal, carne 100% ANGUS, queso americano, más tocineta, cebolla morada y lechuga romana	\N	31000.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
16	1	Hamburguesa Angus Doble	Pan artesanal, doble carne 100% ANGUS, queso americano, más tocineta, cebolla morada y lechuga romana	\N	35000.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
17	1	Hamburguesa T.T Todo Terreno Res	Carne de res, doble tocineta, extra queso mozarella, cebolla grillé	\N	22900.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
18	1	Hamburguesa T.T Todo Terreno Doble Res	Doble carne de res, doble tocineta, extra queso mozarella, cebolla grillé	\N	25900.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
19	1	Hamburguesa T.T Todo Terreno Pollo	Pollo, doble tocineta, extra queso mozarella, cebolla grillé	\N	23100.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
20	1	Hamburguesa T.T Todo Terreno Doble Pollo	Doble pollo, doble tocineta, extra queso mozarella, cebolla grillé	\N	25500.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
21	1	Hamburguesa T.T Todo Terreno Mixta	Carne y pollo, doble tocineta, extra queso mozarella, cebolla grillé	\N	27500.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
22	1	Hamburguesa Ranchera Res	Carne de res, 2 salchichas Rancheras con queso rallado y chimichurri	\N	22500.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
23	1	Hamburguesa Ranchera Doble Res	Doble carne de res, 2 salchichas Rancheras con queso rallado y chimichurri	\N	25500.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
24	1	Hamburguesa Cinco Estrellas Res	Carne de res, aros de cebolla, queso americano, tocineta (no ripio)	\N	22900.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
25	1	Hamburguesa Cinco Estrellas Doble Res	Doble carne de res, aros de cebolla, queso americano, tocineta (no ripio)	\N	25200.00	t	\N	t	2026-10-08 20:07:44.674166-05	2026-10-08 20:07:44.674166-05	\N	t
26	2	Combo Con Papas	Gaseosa personal + porción de papas a la francesa	\N	15000.00	t	\N	t	2026-10-08 20:07:44.690701-05	2026-10-08 20:07:44.690701-05	\N	t
27	2	Combo Con Aros de Cebolla	Gaseosa personal + porción de aros de cebolla crocantes	\N	16500.00	t	\N	t	2026-10-08 20:07:44.690701-05	2026-10-08 20:07:44.690701-05	\N	t
28	3	Perro Ítalo Suizo	Salchicha Suiza, tocineta, queso mozarella, ripio, lechuga y salsa de la casa	\N	19900.00	t	\N	t	2026-10-08 20:07:44.691633-05	2026-10-08 20:07:44.691633-05	\N	t
29	3	Perro Mr. Burger	Salchicha Ideal, tocineta, queso mozarella, ripio, lechuga y salsa de la casa	\N	16500.00	t	\N	t	2026-10-08 20:07:44.691633-05	2026-10-08 20:07:44.691633-05	\N	t
30	3	Perro Ranchero	Dos salchichas Rancheras, tocineta, queso mozarella, ripio, lechuga y salsa de la casa	\N	17900.00	t	\N	t	2026-10-08 20:07:44.691633-05	2026-10-08 20:07:44.691633-05	\N	t
31	3	Perro Americano	Salchicha Americana, tocineta, queso americano y salsa de la casa	\N	18700.00	t	\N	t	2026-10-08 20:07:44.691633-05	2026-10-08 20:07:44.691633-05	\N	t
32	3	Perro Quesudo	Salchicha Americana, tocineta, mucho queso mozzarella, maíz dulce y salsa de la casa	\N	19700.00	t	\N	t	2026-10-08 20:07:44.691633-05	2026-10-08 20:07:44.691633-05	\N	t
33	3	Perro Mexicano	Salchicha Ideal, tocineta, queso rallado, ripio, lechuga, chimichurri y salsa de la casa	\N	16900.00	t	\N	t	2026-10-08 20:07:44.691633-05	2026-10-08 20:07:44.691633-05	\N	t
34	4	Costilla St. Louis	Costilla baby de cerdo bañada en salsa BBQ, acompañada de papas a la francesa y ensalada fresca	\N	36400.00	t	\N	t	2026-10-08 20:07:44.692702-05	2026-10-08 20:07:44.692702-05	\N	t
35	4	Asado Baby	Lomo viche a la brasa con chimichurri y BBQ, con papas y ensalada fresca	\N	35400.00	t	\N	t	2026-10-08 20:07:44.692702-05	2026-10-08 20:07:44.692702-05	\N	t
37	4	Filete de Pollo a la Brasa	Filete de pechuga de pollo con chimichurri y BBQ, con papas y ensalada fresca	\N	32400.00	t	\N	t	2026-10-08 20:07:44.692702-05	2026-10-08 20:07:44.692702-05	\N	t
38	4	Chuzo de Res	Carne de res en pincho a la brasa, con papas y ensalada fresca	\N	22300.00	t	\N	t	2026-10-08 20:07:44.692702-05	2026-10-08 20:07:44.692702-05	\N	t
39	4	Chuzo de Pollo	Pollo en pincho a la brasa, con papas y ensalada fresca	\N	22300.00	t	\N	t	2026-10-08 20:07:44.692702-05	2026-10-08 20:07:44.692702-05	\N	t
40	4	Chuzo Mixto	Carne de res y pollo en pincho a la brasa, con papas y ensalada fresca	\N	22300.00	t	\N	t	2026-10-08 20:07:44.692702-05	2026-10-08 20:07:44.692702-05	\N	t
41	5	Desgranado Mixto	Mazorca desgranada con mantequilla, salsa de la casa, queso rallado, lechuga, ripio de papa, res y pollo	\N	33500.00	t	\N	t	2026-10-08 20:07:44.693718-05	2026-10-08 20:07:44.693718-05	\N	t
42	5	Desgranado Res	Mazorca desgranada con mantequilla, salsa de la casa, queso rallado, lechuga, ripio de papa y res	\N	30500.00	t	\N	t	2026-10-08 20:07:44.693718-05	2026-10-08 20:07:44.693718-05	\N	t
43	5	Desgranado Pollo	Mazorca desgranada con mantequilla, salsa de la casa, queso rallado, lechuga, ripio de papa y pollo	\N	30500.00	t	\N	t	2026-10-08 20:07:44.693718-05	2026-10-08 20:07:44.693718-05	\N	t
44	5	Desgranado Ranchero	Mazorca desgranada con mantequilla, salsa de la casa, queso rallado, ripio y salchicha ranchera	\N	33000.00	t	\N	t	2026-10-08 20:07:44.693718-05	2026-10-08 20:07:44.693718-05	\N	t
45	5	Mazorca Ranchera	Mazorca tierna con salchicha ranchera y cubierta de abundante queso rallado	\N	18500.00	t	\N	t	2026-10-08 20:07:44.693718-05	2026-10-08 20:07:44.693718-05	\N	t
46	5	Mazorca Gratinada	Mazorca tierna bañada en salsa de la casa y gratinada con queso mozzarella	\N	17400.00	t	\N	t	2026-10-08 20:07:44.693718-05	2026-10-08 20:07:44.693718-05	\N	t
47	5	Mazorca Americana	Mazorca tierna tradicional con mantequilla y salsa americana	\N	15900.00	t	\N	t	2026-10-08 20:07:44.693718-05	2026-10-08 20:07:44.693718-05	\N	t
48	5	Mazorca Especial Pollo	Mazorca tierna acompañada con trozos de pechuga de pollo y queso rallado	\N	24500.00	t	\N	t	2026-10-08 20:07:44.693718-05	2026-10-08 20:07:44.693718-05	\N	t
49	6	Alitas BBQ (6 piezas)	6 piezas de alas apanadas bañadas en salsa BBQ, acompañadas con papas a la francesa	\N	21900.00	t	\N	t	2026-10-08 20:07:44.698638-05	2026-10-08 20:07:44.698638-05	\N	t
36	4	Churrasco a la Plancha	Churrasco a la brasa con chimichurri y BBQ, con papas y ensalada fresca	\N	32200.00	t	\N	t	2026-10-08 20:07:44.692702-05	2026-10-09 20:34:58.354488-05	\N	t
50	6	Alitas Miel Mostaza (6 piezas)	6 piezas de alas apanadas bañadas en salsa miel mostaza, con papas a la francesa	\N	21900.00	t	\N	t	2026-10-08 20:07:44.698638-05	2026-10-08 20:07:44.698638-05	\N	t
51	6	Alitas Picantes (6 piezas)	6 piezas de alas apanadas bañadas en salsa picante especial, con papas a la francesa	\N	21900.00	t	\N	t	2026-10-08 20:07:44.698638-05	2026-10-08 20:07:44.698638-05	\N	t
52	7	Salchipapa Americana	Papas a la francesa crocantes con salchicha Americana y salsas	\N	19900.00	t	\N	t	2026-10-08 20:07:44.701835-05	2026-10-08 20:07:44.701835-05	\N	t
53	7	Salchipapa Especial	Papas a la francesa con salchicha americana, queso rallado, queso mozzarella y tocineta	\N	23600.00	t	\N	t	2026-10-08 20:07:44.701835-05	2026-10-08 20:07:44.701835-05	\N	t
54	7	Papas con Queso	Porción generosa de papas a la francesa cubiertas con queso fundido y tocineta	\N	17900.00	t	\N	t	2026-10-08 20:07:44.701835-05	2026-10-08 20:07:44.701835-05	\N	t
55	7	Papas a la Francesa (Porción)	Porción individual de papas a la francesa crocantes	\N	12000.00	t	\N	t	2026-10-08 20:07:44.701835-05	2026-10-08 20:07:44.701835-05	\N	t
56	7	Aros de Cebolla (6 unidades)	6 aros de cebolla fritos dorados y crocantes	\N	13000.00	t	\N	t	2026-10-08 20:07:44.701835-05	2026-10-08 20:07:44.701835-05	\N	t
57	8	Limonada Natural	Limonada refrescante preparada al instante	\N	7700.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
58	8	Limonada de Coco	Limonada cremosa con leche de coco y hielo frappé	\N	9900.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
59	8	Limonada Cherry	Limonada refrescante con infusión dulce de cereza	\N	9900.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
60	8	Jugo de Mandarina	Jugo natural de mandarina recién exprimida	\N	8300.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
61	8	Jugos en Agua	Jugo natural de fruta en agua (Mora, Mango, Lulo, Maracuyá)	\N	8000.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
62	8	Jugos en Leche	Jugo natural de fruta en leche fresca	\N	9000.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
63	8	Gaseosa Personal	Gaseosa en presentación personal (Coca-Cola, Postobón, etc.)	\N	5500.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
64	8	Gaseosa 1.1/4 Litro	Gaseosa tamaño familiar 1.1/4 L	\N	12000.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
65	8	Fuze Tea	Té frío embotellado sabor limón / durazno	\N	5500.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
66	8	Agua en Botella	Agua pura sin gas en botella personal	\N	5000.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-08 20:07:44.703575-05	\N	t
1	1	Hamburguesa Clásica	Pan, carne, queso, lechuga	\N	12000.00	t	\N	f	2026-10-08 20:07:44.190781-05	2026-10-08 20:07:44.190781-05	\N	t
2	1	Hamburguesa Especial	Doble carne, queso cheddar, tomate	\N	15000.00	t	\N	f	2026-10-08 20:07:44.190781-05	2026-10-08 20:07:44.190781-05	\N	t
3	2	Perro Clásico	Salchicha, pan, salsas	\N	8000.00	t	\N	f	2026-10-08 20:07:44.190781-05	2026-10-08 20:07:44.190781-05	\N	t
4	3	Papas Fritas	Porción de 150 g	\N	6000.00	t	\N	f	2026-10-08 20:07:44.190781-05	2026-10-08 20:07:44.190781-05	\N	t
5	4	Gaseosa	350 ml	\N	3000.00	t	\N	f	2026-10-08 20:07:44.190781-05	2026-10-08 20:07:44.190781-05	\N	t
6	4	Agua	500 ml	\N	2000.00	t	\N	f	2026-10-08 20:07:44.190781-05	2026-10-08 20:07:44.190781-05	\N	t
999	99	Empaque Para Llevar (c1)	Empaque térmico principal desechable	\N	1500.00	t	\N	f	2026-10-08 20:07:45.072008-05	2026-10-08 20:07:45.072008-05	\N	t
67	8	Cerveza Nacional	Cerveza fría personal (Club Colombia, Águila, Poker)	\N	7000.00	t	\N	t	2026-10-08 20:07:44.703575-05	2026-10-09 20:34:26.563198-05	\N	f
\.


--
-- TOC entry 5335 (class 0 OID 16534)
-- Dependencies: 232
-- Data for Name: proveedor; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.proveedor (id, nombre, contacto, telefono, activo) FROM stdin;
1	Distribuidora Central Cali	Don Pedro	3123456789	t
\.


--
-- TOC entry 5371 (class 0 OID 17063)
-- Dependencies: 268
-- Data for Name: registro_sync; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.registro_sync (id, op_id, sucursal_id, dispositivo_id, origen, tipo, entidad, entidad_id, entidad_uuid, payload, estado, reintentos, ultimo_error, resolucion_nota, creado_en, sincronizado_en) FROM stdin;
3	33e73dce-ab10-4bed-9294-d030d4ffdf7a	SUC-01	SISTEMA_RECONCILIACION	LOCAL	CREAR_USUARIO	usuario	5	fd6dbc2c-d1cf-447b-a8d4-c9d2d8813401	{"id": 5, "activo": true, "fijado": true, "nombre": "felix", "rol_id": 2, "es_demo": false, "usuario": "felix123", "password_hash": "$2b$12$ckH.2JixWhrPP9n7gGFOe.LVLPpneTWmE45.IuhChXwDoCImmFVF6"}	APLICADO	53	\N	\N	2026-10-09 16:44:07.370116-05	2026-10-09 17:14:31.052772-05
4	2d4b9068-bb50-437a-a6cd-dcda2f80f04b	SUC-01	SISTEMA_RECONCILIACION	LOCAL	CREAR_USUARIO	usuario	7	4a08a80f-e7bd-4c8d-b470-43feb38077c8	{"id": 7, "activo": true, "fijado": true, "nombre": "Omar Velandia", "rol_id": 1, "es_demo": false, "usuario": "omarvelandia", "password_hash": "$2b$12$RQfxLYcs1pDDnUQwwYTd/ur7KQ2cbiqLn.llAAVjkU6ALrNolhVpS"}	APLICADO	89	\N	\N	2026-10-09 17:36:09.689443-05	2026-10-09 18:02:12.545628-05
1	25ef1586-ceb2-49e1-bf0a-0f3d1e7e92ac	SUC-01	CAJA_5	LOCAL	ABRIR_TURNO	cierre	1	178071c7-5712-48e3-88be-5417365e56a6	{"id": 1, "abierto_en": "2026-10-08 20:49:51.192555-05:00", "usuario_id": 5, "fondo_inicial": 521650.0}	APLICADO	187	\N	\N	2026-10-08 20:49:51.192555-05	2026-10-09 18:03:37.09105-05
11	b6ef10f3-66aa-4a88-88b2-9ec68a8302fa	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	37	89f8f2b6-530f-49c4-914c-1013afb7664e	{"id": 37, "tipo": "VENTA", "unidad": "UNIDAD", "cantidad": -1.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": -1.0, "ingrediente_id": 29, "saldo_anterior": 0.0, "ingrediente_nombre": "Tomate", "stock_actual_checkpoint": -1.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
12	7360563e-8789-4bc1-aa80-f940dd8bc3d2	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	38	8cdb969b-1d3b-42ea-a8fa-6c7bb537d65c	{"id": 38, "tipo": "VENTA", "unidad": "GRAMO", "cantidad": -20.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": -20.0, "ingrediente_id": 32, "saldo_anterior": 0.0, "ingrediente_nombre": "Lechuga Batavia", "stock_actual_checkpoint": -20.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
13	b47d4521-db30-44b0-91a6-303a977f0d09	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	39	e4284764-e5a9-4d8f-8913-5589f356d4a7	{"id": 39, "tipo": "VENTA", "unidad": "LONJA", "cantidad": -2.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": -2.0, "ingrediente_id": 35, "saldo_anterior": 0.0, "ingrediente_nombre": "Queso Americano", "stock_actual_checkpoint": -2.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
14	b5471e60-fa6d-474f-a18a-80cca8cce567	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	40	6b3d4404-72de-4edd-8756-34bb9f053f7a	{"id": 40, "tipo": "VENTA", "unidad": "MILILITRO", "cantidad": -25.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": 3975.0, "ingrediente_id": 42, "saldo_anterior": 4000.0, "ingrediente_nombre": "Salsa Mr Burger", "stock_actual_checkpoint": 3975.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
15	0b074b86-cb86-43e8-8359-084055b31d0b	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	41	a104562c-53b4-464c-a31f-e32b4b788019	{"id": 41, "tipo": "VENTA", "unidad": "UNIDAD", "cantidad": -1.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": 49.0, "ingrediente_id": 61, "saldo_anterior": 50.0, "ingrediente_nombre": "C1 (Empaque Térmico)", "stock_actual_checkpoint": 49.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
2	d5bb7b70-97b3-4f45-8448-fbc93478bff1	SUC-01	CAJA_5	LOCAL	CIERRE_TURNO	cierre	1	5cc23bb7-22fb-40e7-8fe3-f6e0a21040ea	{"id": 1, "notas": "Arqueo físico: Billetes: $521.600 COP | Monedas: $0 COP | Total Efectivo: $521.600 COP | Datáfono/Transferencias: $0 COP. ", "abierto_en": "2026-10-08 20:49:51.192555-05:00", "cerrado_en": "now()", "total_vale": 0.0, "usuario_id": 5, "total_ventas": 0.0, "total_pedidos": 0, "total_tarjeta": 0.0, "total_efectivo": 0.0, "total_por_cobrar": 0.0, "total_didi_tarjeta": 0.0, "total_salidas_caja": 0.0, "total_didi_efectivo": 0.0, "total_entradas_caja": 521650.0, "total_transferencia": 0.0, "total_efectivo_final": 521650.0}	APLICADO	187	\N	\N	2026-10-08 20:56:01.042321-05	2026-10-09 18:03:37.09105-05
5	c87c4586-222d-48b1-92cf-d147b7ea11bf	SUC-01	CAJA_5	LOCAL	ABRIR_TURNO	cierre	2	1a20f03b-1b81-482a-808a-cc3804b0d554	{"id": 2, "abierto_en": "2026-10-09 19:50:00.923797-05:00", "usuario_id": 5, "fondo_inicial": 100000.0}	APLICADO	0	\N	\N	2026-10-09 19:50:00.923797-05	2026-10-09 19:50:18.539114-05
6	9aae588f-2e6d-4688-98d7-f911d93f2800	SUC-01	USER_5	LOCAL	CREAR_PEDIDO	pedido	1	578678e8-445e-4e2d-bcda-edd673ecfafa	{"id": 1, "iva": 0.0, "canal": "MOSTRADOR", "total": 23400.0, "estado": "NUEVO", "cliente": null, "mesa_id": null, "detalles": [{"ronda": 1, "estado": null, "cantidad": 1.0, "producto_id": 8, "precio_unitario": 21900.0}], "subtotal": 21900.0, "fecha_dia": "2026-10-09", "consecutivo": 1}	ERROR_SERVIDOR	5	HTTP 500: Internal Server Error	\N	2026-10-09 19:51:17.256828-05	\N
8	9a809cc2-3303-450b-a7db-127540337a8b	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	34	60ba623b-67fa-4e22-a171-37de91a42d8c	{"id": 34, "tipo": "VENTA", "unidad": "GRAMO", "cantidad": -30.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": 1970.0, "ingrediente_id": 16, "saldo_anterior": 2000.0, "ingrediente_nombre": "Tocineta", "stock_actual_checkpoint": 1970.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
9	19e61133-25cd-428c-9622-ec78bd35e8b0	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	35	f682b6e0-823e-4244-a481-9dd73fc5f18d	{"id": 35, "tipo": "VENTA", "unidad": "UNIDAD", "cantidad": -1.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": 111.0, "ingrediente_id": 21, "saldo_anterior": 112.0, "ingrediente_nombre": "Pan Hamburguesa", "stock_actual_checkpoint": 111.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
10	07088306-5039-4b08-9b19-4953ec52c760	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	36	a32de442-26a7-4d0a-8e9f-2df3f5a5f430	{"id": 36, "tipo": "VENTA", "unidad": "GRAMO", "cantidad": -15.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": 2985.0, "ingrediente_id": 27, "saldo_anterior": 3000.0, "ingrediente_nombre": "Ripio de Papa", "stock_actual_checkpoint": 2985.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
7	6d07dad8-d2af-40ce-bd1e-6c0fbb4f2f6d	SUC-01	USER_5	LOCAL	DESCUENTO_STOCK	movimiento_inventario	33	e83f277a-3ec5-4d7b-9b4c-7bef3b1bada6	{"id": 33, "tipo": "VENTA", "unidad": "GRAMO", "cantidad": -250.0, "pedido_id": 1, "referencia": "Cobro en Caja Pedido #1 - Hamburguesa Especial Doble Res", "saldo_nuevo": -250.0, "ingrediente_id": 10, "saldo_anterior": 0.0, "ingrediente_nombre": "Carne de res", "stock_actual_checkpoint": -250.0}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
19	82dcfb2c-cee9-49a0-bf34-3b1c9f583901	SUC-01	USER_4	LOCAL	DESCUENTO_STOCK	movimiento_inventario	43	b14e2b4a-7325-4a3a-bdda-933e3f07d78f	{"id": 43, "tipo": "VENTA", "unidad": "MILILITRO", "cantidad": -80.0, "pedido_id": 2, "referencia": "Pedido #2 - Alitas BBQ (6 piezas)", "saldo_nuevo": -80.0, "ingrediente_id": 44, "saldo_anterior": 0.0, "ingrediente_nombre": "Salsa BBQ", "stock_actual_checkpoint": -80.0}	ERROR_SERVIDOR	5	HTTP 500: Internal Server Error	\N	2026-10-09 20:06:50.350451-05	\N
20	a888a0fc-b9d0-440c-b1cd-98157ed0332c	SUC-01	USER_4	LOCAL	DESCUENTO_STOCK	movimiento_inventario	44	d6156546-72aa-49a8-9a0a-f0de19c5dacf	{"id": 44, "tipo": "VENTA", "unidad": "MILILITRO", "cantidad": -60.0, "pedido_id": 2, "referencia": "Pedido #2 - Alitas BBQ (6 piezas)", "saldo_nuevo": -60.0, "ingrediente_id": 49, "saldo_anterior": 0.0, "ingrediente_nombre": "Aceite", "stock_actual_checkpoint": -60.0}	ERROR_SERVIDOR	5	HTTP 500: Internal Server Error	\N	2026-10-09 20:06:50.350451-05	\N
21	f57e01e6-341b-4ded-9c1b-6462bdbfac20	SUC-01	USER_3	LOCAL	AGREGAR_RONDA	detalle_pedido	2	0caefa06-99e6-4d2a-9e0c-a39d821e2729	{"ronda": 2, "detalles": [{"ronda": 2, "cantidad": 1.0, "producto_id": 35, "precio_unitario": 35400.0}], "pedido_id": 2, "consecutivo": 2, "nuevo_total": 79200.0}	ERROR_SERVIDOR	5	HTTP 500: Internal Server Error	\N	2026-10-09 20:07:12.364488-05	\N
16	4d818b06-3967-4c03-850a-5a1801c24570	SUC-01	CAJA_5	LOCAL	COBRO_PEDIDO	pago	1	91c3cfd0-d82b-49c2-9e4e-fc93ebbb0a71	{"id": 1, "monto": 23400.0, "cambio": 6600.0, "metodo": "EFECTIVO", "recibido": 30000.0, "pedido_id": 1, "consecutivo": 1, "didi_orden_id": null}	ERROR_SERVIDOR	40	HTTP 500: Internal Server Error	\N	2026-10-09 19:52:23.637378-05	\N
22	d89ca260-0024-4e18-ae50-46e1cf94ebb1	SUC-01	USER_4	LOCAL	DESCUENTO_STOCK	movimiento_inventario	45	8796687b-4f90-4085-8a4d-c62f5ab70633	{"id": 45, "tipo": "VENTA", "unidad": "GRAMO", "cantidad": -250.0, "pedido_id": 2, "referencia": "Pedido #2 - Asado Baby", "saldo_nuevo": -250.0, "ingrediente_id": 13, "saldo_anterior": 0.0, "ingrediente_nombre": "Baby Beef", "stock_actual_checkpoint": -250.0}	PENDIENTE	154	HTTP 409: {"detail":"Conflicto de integridad o concurrencia en base de datos. Verifique los datos o reintente."}	\N	2026-10-09 20:07:27.514409-05	\N
18	90da09fc-5f6d-4017-9e22-4dc2e5331913	SUC-01	USER_4	LOCAL	DESCUENTO_STOCK	movimiento_inventario	42	8c797731-469b-47fc-bc92-7fed47e8fcf4	{"id": 42, "tipo": "VENTA", "unidad": "GRAMO", "cantidad": -300.0, "pedido_id": 2, "referencia": "Pedido #2 - Alitas BBQ (6 piezas)", "saldo_nuevo": 7200.0, "ingrediente_id": 24, "saldo_anterior": 7500.0, "ingrediente_nombre": "Papa a la Francesa", "stock_actual_checkpoint": 7200.0}	ERROR_SERVIDOR	5	HTTP 500: Internal Server Error	\N	2026-10-09 20:06:50.350451-05	\N
17	fb31a1d4-0d0a-41eb-b503-02ebb47bbaa7	SUC-01	USER_3	LOCAL	CREAR_PEDIDO	pedido	2	2132f962-965e-48c5-9d09-5c0e46a5772d	{"id": 2, "iva": 0.0, "canal": "MESA", "total": 43800.0, "estado": "NUEVO", "cliente": null, "mesa_id": 3, "detalles": [{"ronda": 1, "estado": null, "cantidad": 2.0, "producto_id": 49, "precio_unitario": 21900.0}], "subtotal": 43800.0, "fecha_dia": "2026-10-09", "consecutivo": 2}	ERROR_SERVIDOR	5	HTTP 500: Internal Server Error	\N	2026-10-09 20:06:15.732031-05	\N
23	796abb4b-c1c7-418c-9d22-5818bf4a88a4	SUC-01	USER_4	LOCAL	DESCUENTO_STOCK	movimiento_inventario	46	a4d0eead-b58c-4bbf-9618-956c291c220d	{"id": 46, "tipo": "VENTA", "unidad": "GRAMO", "cantidad": -150.0, "pedido_id": 2, "referencia": "Pedido #2 - Asado Baby", "saldo_nuevo": 7050.0, "ingrediente_id": 24, "saldo_anterior": 7200.0, "ingrediente_nombre": "Papa a la Francesa", "stock_actual_checkpoint": 7050.0}	PENDIENTE	154	HTTP 409: {"detail":"Conflicto de integridad o concurrencia en base de datos. Verifique los datos o reintente."}	\N	2026-10-09 20:07:27.514409-05	\N
24	5ab0f391-044e-4582-9fc1-e3f61ced0db2	SUC-01	USER_4	LOCAL	DESCUENTO_STOCK	movimiento_inventario	47	bf897926-bcfd-4de9-8ea6-63273364e7bd	{"id": 47, "tipo": "VENTA", "unidad": "MILILITRO", "cantidad": -30.0, "pedido_id": 2, "referencia": "Pedido #2 - Asado Baby", "saldo_nuevo": 3970.0, "ingrediente_id": 41, "saldo_anterior": 4000.0, "ingrediente_nombre": "Chimichurry", "stock_actual_checkpoint": 3970.0}	PENDIENTE	154	HTTP 409: {"detail":"Conflicto de integridad o concurrencia en base de datos. Verifique los datos o reintente."}	\N	2026-10-09 20:07:27.514409-05	\N
25	f1792670-5bab-46b0-a64a-a969b85724bc	SUC-01	CAJA_2	LOCAL	COBRO_PEDIDO	pago	2	8705cd8b-c787-4221-9f74-918152f14571	{"id": 2, "monto": 79200.0, "cambio": 20800.0, "metodo": "EFECTIVO", "recibido": 100000.0, "pedido_id": 2, "consecutivo": 2, "didi_orden_id": null}	PENDIENTE	150	HTTP 409: {"detail":"Conflicto de integridad o concurrencia en base de datos. Verifique los datos o reintente."}	\N	2026-10-09 20:08:46.429554-05	\N
\.


--
-- TOC entry 5325 (class 0 OID 16437)
-- Dependencies: 222
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.rol (id, nombre, descripcion) FROM stdin;
1	admin	Acceso total: ventas, ganancias, inventario, recetas, gastos, cancelaciones
2	cajero	Cobrar, vales, pedidos Didi, cierre de su turno, devoluciones de dinero
3	mesero	Tomar y enviar pedidos, ver mesas, preparados y estado de cocina. Sin dinero
4	cocina	Ver tickets (sin precios), cambiar estados, temporizador
\.


--
-- TOC entry 5329 (class 0 OID 16477)
-- Dependencies: 226
-- Data for Name: tipo_categoria; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.tipo_categoria (id, nombre) FROM stdin;
1	COMIDA
2	BEBIDA
3	OTRO
\.


--
-- TOC entry 5369 (class 0 OID 17046)
-- Dependencies: 266
-- Data for Name: turno_laboral; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.turno_laboral (id, usuario_id, entrada_en, salida_en, motivo_cierre, es_demo, rol) FROM stdin;
1	5	2026-10-08 20:49:40.96381-05	2026-10-08 20:56:01.042321-05	CIERRE_CAJA	f	cajero
2	5	2026-10-08 20:56:01.169924-05	\N	\N	f	cajero
4	4	2026-10-09 20:05:28.867361-05	\N	\N	t	cocina
3	3	2026-10-09 20:03:38.045586-05	2026-10-09 20:07:32.215599-05	MANUAL	t	mesero
5	3	2026-10-09 20:07:32.285572-05	\N	\N	t	mesero
6	2	2026-10-09 20:07:42.393374-05	\N	\N	t	cajero
\.


--
-- TOC entry 5327 (class 0 OID 16450)
-- Dependencies: 224
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.usuario (id, rol_id, nombre, usuario, password_hash, activo, creado_en, actualizado_en, fijado, es_demo) FROM stdin;
1	1	Administrador	admin	$2b$12$/8tbC/F.WtMNVjSvRdwG9ecoLMDXColvgCAqeP2bAVVZcS/STbS.O	t	2026-10-08 20:07:44.266268-05	2026-10-08 20:07:44.266268-05	t	f
2	2	Cajero Demo	caja	$2b$12$UR9zR9cwj5ffRV9B9oJdteyUkDG5MKTTuANe8aYzqZ1hv0VO70cc.	t	2026-10-08 20:07:44.266268-05	2026-10-08 20:07:44.266268-05	t	t
3	3	Mesero Demo	mesero	$2b$12$ns9jFXxoo26ThkiIjdd7y.C/0POZqvxPRMKW5spYxCB3aIQ3JP5r6	t	2026-10-08 20:07:44.266268-05	2026-10-08 20:07:44.266268-05	t	t
4	4	Cocina Demo	cocina	$2b$12$vMsDVdpD.xW494pwpmb2k.gyxGbDLOvKdRRo2KLUDOErIjy75yiwa	t	2026-10-08 20:07:44.266268-05	2026-10-08 20:07:44.266268-05	t	t
5	2	felix	felix123	$2b$12$ckH.2JixWhrPP9n7gGFOe.LVLPpneTWmE45.IuhChXwDoCImmFVF6	t	2026-10-08 20:12:39.608194-05	2026-10-08 20:12:39.608194-05	t	f
7	1	Omar Velandia	omarvelandia	$2b$12$RQfxLYcs1pDDnUQwwYTd/ur7KQ2cbiqLn.llAAVjkU6ALrNolhVpS	t	2026-10-09 17:32:50.710057-05	2026-10-09 17:32:50.710057-05	t	f
\.


--
-- TOC entry 5353 (class 0 OID 16770)
-- Dependencies: 250
-- Data for Name: vale; Type: TABLE DATA; Schema: public; Owner: restaurante
--

COPY public.vale (id, pedido_id, cliente_nombre, cliente_cedula, cliente_telefono, monto, estado, cobrado_por, cobrado_en, creado_en, es_demo) FROM stdin;
\.


--
-- TOC entry 5402 (class 0 OID 0)
-- Dependencies: 227
-- Name: categoria_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.categoria_id_seq', 8, true);


--
-- TOC entry 5403 (class 0 OID 0)
-- Dependencies: 233
-- Name: categoria_insumo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.categoria_insumo_id_seq', 1, false);


--
-- TOC entry 5404 (class 0 OID 0)
-- Dependencies: 255
-- Name: cierre_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.cierre_id_seq', 2, true);


--
-- TOC entry 5405 (class 0 OID 0)
-- Dependencies: 239
-- Name: componente_combo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.componente_combo_id_seq', 10, true);


--
-- TOC entry 5406 (class 0 OID 0)
-- Dependencies: 259
-- Name: compra_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.compra_id_seq', 1, true);


--
-- TOC entry 5407 (class 0 OID 0)
-- Dependencies: 261
-- Name: detalle_compra_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.detalle_compra_id_seq', 17, true);


--
-- TOC entry 5408 (class 0 OID 0)
-- Dependencies: 245
-- Name: detalle_pedido_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.detalle_pedido_id_seq', 3, true);


--
-- TOC entry 5409 (class 0 OID 0)
-- Dependencies: 237
-- Name: detalle_receta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.detalle_receta_id_seq', 392, true);


--
-- TOC entry 5410 (class 0 OID 0)
-- Dependencies: 263
-- Name: historial_accion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.historial_accion_id_seq', 75, true);


--
-- TOC entry 5411 (class 0 OID 0)
-- Dependencies: 235
-- Name: ingrediente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.ingrediente_id_seq', 89, true);


--
-- TOC entry 5412 (class 0 OID 0)
-- Dependencies: 241
-- Name: mesa_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.mesa_id_seq', 9, true);


--
-- TOC entry 5413 (class 0 OID 0)
-- Dependencies: 251
-- Name: movimiento_caja_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.movimiento_caja_id_seq', 2, true);


--
-- TOC entry 5414 (class 0 OID 0)
-- Dependencies: 253
-- Name: movimiento_inventario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.movimiento_inventario_id_seq', 48, true);


--
-- TOC entry 5415 (class 0 OID 0)
-- Dependencies: 247
-- Name: pago_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.pago_id_seq', 2, true);


--
-- TOC entry 5416 (class 0 OID 0)
-- Dependencies: 243
-- Name: pedido_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.pedido_id_seq', 2, true);


--
-- TOC entry 5417 (class 0 OID 0)
-- Dependencies: 257
-- Name: preparado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.preparado_id_seq', 1, false);


--
-- TOC entry 5418 (class 0 OID 0)
-- Dependencies: 229
-- Name: producto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.producto_id_seq', 67, true);


--
-- TOC entry 5419 (class 0 OID 0)
-- Dependencies: 231
-- Name: proveedor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.proveedor_id_seq', 1, false);


--
-- TOC entry 5420 (class 0 OID 0)
-- Dependencies: 267
-- Name: registro_sync_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.registro_sync_id_seq', 25, true);


--
-- TOC entry 5421 (class 0 OID 0)
-- Dependencies: 221
-- Name: rol_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.rol_id_seq', 4, true);


--
-- TOC entry 5422 (class 0 OID 0)
-- Dependencies: 225
-- Name: tipo_categoria_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.tipo_categoria_id_seq', 3, true);


--
-- TOC entry 5423 (class 0 OID 0)
-- Dependencies: 265
-- Name: turno_laboral_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.turno_laboral_id_seq', 6, true);


--
-- TOC entry 5424 (class 0 OID 0)
-- Dependencies: 223
-- Name: usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.usuario_id_seq', 7, true);


--
-- TOC entry 5425 (class 0 OID 0)
-- Dependencies: 249
-- Name: vale_id_seq; Type: SEQUENCE SET; Schema: public; Owner: restaurante
--

SELECT pg_catalog.setval('public.vale_id_seq', 1, false);


--
-- TOC entry 5057 (class 2606 OID 16558)
-- Name: categoria_insumo categoria_insumo_nombre_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.categoria_insumo
    ADD CONSTRAINT categoria_insumo_nombre_key UNIQUE (nombre);


--
-- TOC entry 5059 (class 2606 OID 16556)
-- Name: categoria_insumo categoria_insumo_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.categoria_insumo
    ADD CONSTRAINT categoria_insumo_pkey PRIMARY KEY (id);


--
-- TOC entry 5051 (class 2606 OID 16500)
-- Name: categoria categoria_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT categoria_pkey PRIMARY KEY (id);


--
-- TOC entry 5110 (class 2606 OID 16912)
-- Name: cierre cierre_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.cierre
    ADD CONSTRAINT cierre_pkey PRIMARY KEY (id);


--
-- TOC entry 5067 (class 2606 OID 16631)
-- Name: componente_combo componente_combo_combo_producto_id_producto_hijo_id_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.componente_combo
    ADD CONSTRAINT componente_combo_combo_producto_id_producto_hijo_id_key UNIQUE (combo_producto_id, producto_hijo_id);


--
-- TOC entry 5069 (class 2606 OID 16629)
-- Name: componente_combo componente_combo_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.componente_combo
    ADD CONSTRAINT componente_combo_pkey PRIMARY KEY (id);


--
-- TOC entry 5117 (class 2606 OID 16986)
-- Name: compra compra_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.compra
    ADD CONSTRAINT compra_pkey PRIMARY KEY (id);


--
-- TOC entry 5037 (class 2606 OID 16435)
-- Name: configuracion configuracion_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.configuracion
    ADD CONSTRAINT configuracion_pkey PRIMARY KEY (clave);


--
-- TOC entry 5120 (class 2606 OID 17009)
-- Name: detalle_compra detalle_compra_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT detalle_compra_pkey PRIMARY KEY (id);


--
-- TOC entry 5086 (class 2606 OID 16722)
-- Name: detalle_pedido detalle_pedido_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_pedido
    ADD CONSTRAINT detalle_pedido_pkey PRIMARY KEY (id);


--
-- TOC entry 5063 (class 2606 OID 16605)
-- Name: detalle_receta detalle_receta_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_receta
    ADD CONSTRAINT detalle_receta_pkey PRIMARY KEY (id);


--
-- TOC entry 5065 (class 2606 OID 16607)
-- Name: detalle_receta detalle_receta_product_id_ingrediente_id_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_receta
    ADD CONSTRAINT detalle_receta_product_id_ingrediente_id_key UNIQUE (product_id, ingrediente_id);


--
-- TOC entry 5122 (class 2606 OID 17037)
-- Name: historial_accion historial_accion_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.historial_accion
    ADD CONSTRAINT historial_accion_pkey PRIMARY KEY (id);


--
-- TOC entry 5061 (class 2606 OID 16583)
-- Name: ingrediente ingrediente_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.ingrediente
    ADD CONSTRAINT ingrediente_pkey PRIMARY KEY (id);


--
-- TOC entry 5071 (class 2606 OID 16657)
-- Name: mesa mesa_numero_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.mesa
    ADD CONSTRAINT mesa_numero_key UNIQUE (numero);


--
-- TOC entry 5073 (class 2606 OID 16655)
-- Name: mesa mesa_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.mesa
    ADD CONSTRAINT mesa_pkey PRIMARY KEY (id);


--
-- TOC entry 5102 (class 2606 OID 16814)
-- Name: movimiento_caja movimiento_caja_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_caja
    ADD CONSTRAINT movimiento_caja_pkey PRIMARY KEY (id);


--
-- TOC entry 5108 (class 2606 OID 16847)
-- Name: movimiento_inventario movimiento_inventario_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_pkey PRIMARY KEY (id);


--
-- TOC entry 5092 (class 2606 OID 16753)
-- Name: pago pago_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pago
    ADD CONSTRAINT pago_pkey PRIMARY KEY (id);


--
-- TOC entry 5080 (class 2606 OID 16688)
-- Name: pedido pedido_fecha_dia_consecutivo_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_fecha_dia_consecutivo_key UNIQUE (fecha_dia, consecutivo);


--
-- TOC entry 5082 (class 2606 OID 16686)
-- Name: pedido pedido_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_idempotency_key_key UNIQUE (idempotency_key);


--
-- TOC entry 5084 (class 2606 OID 16684)
-- Name: pedido pedido_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_pkey PRIMARY KEY (id);


--
-- TOC entry 5115 (class 2606 OID 16948)
-- Name: preparado preparado_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.preparado
    ADD CONSTRAINT preparado_pkey PRIMARY KEY (id);


--
-- TOC entry 5053 (class 2606 OID 16527)
-- Name: producto producto_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.producto
    ADD CONSTRAINT producto_pkey PRIMARY KEY (id);


--
-- TOC entry 5055 (class 2606 OID 16543)
-- Name: proveedor proveedor_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.proveedor
    ADD CONSTRAINT proveedor_pkey PRIMARY KEY (id);


--
-- TOC entry 5133 (class 2606 OID 17086)
-- Name: registro_sync registro_sync_op_id_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.registro_sync
    ADD CONSTRAINT registro_sync_op_id_key UNIQUE (op_id);


--
-- TOC entry 5135 (class 2606 OID 17084)
-- Name: registro_sync registro_sync_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.registro_sync
    ADD CONSTRAINT registro_sync_pkey PRIMARY KEY (id);


--
-- TOC entry 5039 (class 2606 OID 16448)
-- Name: rol rol_nombre_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_nombre_key UNIQUE (nombre);


--
-- TOC entry 5041 (class 2606 OID 16446)
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id);


--
-- TOC entry 5047 (class 2606 OID 16486)
-- Name: tipo_categoria tipo_categoria_nombre_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.tipo_categoria
    ADD CONSTRAINT tipo_categoria_nombre_key UNIQUE (nombre);


--
-- TOC entry 5049 (class 2606 OID 16484)
-- Name: tipo_categoria tipo_categoria_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.tipo_categoria
    ADD CONSTRAINT tipo_categoria_pkey PRIMARY KEY (id);


--
-- TOC entry 5129 (class 2606 OID 17055)
-- Name: turno_laboral turno_laboral_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.turno_laboral
    ADD CONSTRAINT turno_laboral_pkey PRIMARY KEY (id);


--
-- TOC entry 5043 (class 2606 OID 16468)
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);


--
-- TOC entry 5045 (class 2606 OID 16470)
-- Name: usuario usuario_usuario_key; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_usuario_key UNIQUE (usuario);


--
-- TOC entry 5097 (class 2606 OID 16784)
-- Name: vale vale_pkey; Type: CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.vale
    ADD CONSTRAINT vale_pkey PRIMARY KEY (id);


--
-- TOC entry 5087 (class 1259 OID 16734)
-- Name: idx_detalle_estado; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_detalle_estado ON public.detalle_pedido USING btree (estado);


--
-- TOC entry 5088 (class 1259 OID 16733)
-- Name: idx_detalle_pedido; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_detalle_pedido ON public.detalle_pedido USING btree (pedido_id);


--
-- TOC entry 5123 (class 1259 OID 17043)
-- Name: idx_historial_fecha; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_historial_fecha ON public.historial_accion USING btree (creado_en);


--
-- TOC entry 5124 (class 1259 OID 17044)
-- Name: idx_historial_usuario; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_historial_usuario ON public.historial_accion USING btree (usuario_id);


--
-- TOC entry 5098 (class 1259 OID 17096)
-- Name: idx_movcaja_cierre; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_movcaja_cierre ON public.movimiento_caja USING btree (cierre_id);


--
-- TOC entry 5099 (class 1259 OID 17095)
-- Name: idx_movcaja_creado_en; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_movcaja_creado_en ON public.movimiento_caja USING btree (creado_en);


--
-- TOC entry 5103 (class 1259 OID 17091)
-- Name: idx_movinv_creado_en; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_movinv_creado_en ON public.movimiento_inventario USING btree (creado_en);


--
-- TOC entry 5104 (class 1259 OID 17089)
-- Name: idx_movinv_ingrediente; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_movinv_ingrediente ON public.movimiento_inventario USING btree (ingrediente_id);


--
-- TOC entry 5105 (class 1259 OID 17090)
-- Name: idx_movinv_pedido; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_movinv_pedido ON public.movimiento_inventario USING btree (pedido_id);


--
-- TOC entry 5089 (class 1259 OID 17092)
-- Name: idx_pago_pedido_id; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_pago_pedido_id ON public.pago USING btree (pedido_id);


--
-- TOC entry 5074 (class 1259 OID 16701)
-- Name: idx_pedido_estado; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_pedido_estado ON public.pedido USING btree (estado);


--
-- TOC entry 5075 (class 1259 OID 16702)
-- Name: idx_pedido_fecha; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_pedido_fecha ON public.pedido USING btree (fecha_dia, consecutivo);


--
-- TOC entry 5076 (class 1259 OID 16700)
-- Name: idx_pedido_mesa; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_pedido_mesa ON public.pedido USING btree (mesa_id) WHERE ((canal)::text = 'MESA'::text);


--
-- TOC entry 5130 (class 1259 OID 17087)
-- Name: idx_registro_sync_estado; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_registro_sync_estado ON public.registro_sync USING btree (estado, creado_en);


--
-- TOC entry 5131 (class 1259 OID 17088)
-- Name: idx_registro_sync_op_id; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_registro_sync_op_id ON public.registro_sync USING btree (op_id);


--
-- TOC entry 5126 (class 1259 OID 17061)
-- Name: idx_turno_laboral_usuario; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_turno_laboral_usuario ON public.turno_laboral USING btree (usuario_id, salida_en);


--
-- TOC entry 5093 (class 1259 OID 17094)
-- Name: idx_vale_estado; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_vale_estado ON public.vale USING btree (estado);


--
-- TOC entry 5094 (class 1259 OID 17093)
-- Name: idx_vale_pedido; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX idx_vale_pedido ON public.vale USING btree (pedido_id);


--
-- TOC entry 5111 (class 1259 OID 17132)
-- Name: ix_cierre_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_cierre_es_demo ON public.cierre USING btree (es_demo);


--
-- TOC entry 5118 (class 1259 OID 17141)
-- Name: ix_compra_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_compra_es_demo ON public.compra USING btree (es_demo);


--
-- TOC entry 5125 (class 1259 OID 17144)
-- Name: ix_historial_accion_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_historial_accion_es_demo ON public.historial_accion USING btree (es_demo);


--
-- TOC entry 5100 (class 1259 OID 17129)
-- Name: ix_movimiento_caja_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_movimiento_caja_es_demo ON public.movimiento_caja USING btree (es_demo);


--
-- TOC entry 5106 (class 1259 OID 17138)
-- Name: ix_movimiento_inventario_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_movimiento_inventario_es_demo ON public.movimiento_inventario USING btree (es_demo);


--
-- TOC entry 5090 (class 1259 OID 17123)
-- Name: ix_pago_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_pago_es_demo ON public.pago USING btree (es_demo);


--
-- TOC entry 5077 (class 1259 OID 17120)
-- Name: ix_pedido_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_pedido_es_demo ON public.pedido USING btree (es_demo);


--
-- TOC entry 5078 (class 1259 OID 16699)
-- Name: ix_pedido_idempotency_key; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_pedido_idempotency_key ON public.pedido USING btree (idempotency_key);


--
-- TOC entry 5113 (class 1259 OID 17147)
-- Name: ix_preparado_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_preparado_es_demo ON public.preparado USING btree (es_demo);


--
-- TOC entry 5127 (class 1259 OID 17135)
-- Name: ix_turno_laboral_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_turno_laboral_es_demo ON public.turno_laboral USING btree (es_demo);


--
-- TOC entry 5095 (class 1259 OID 17126)
-- Name: ix_vale_es_demo; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE INDEX ix_vale_es_demo ON public.vale USING btree (es_demo);


--
-- TOC entry 5112 (class 1259 OID 16918)
-- Name: uq_cierre_unico_abierto; Type: INDEX; Schema: public; Owner: restaurante
--

CREATE UNIQUE INDEX uq_cierre_unico_abierto ON public.cierre USING btree (((cerrado_en IS NULL))) WHERE (cerrado_en IS NULL);


--
-- TOC entry 5137 (class 2606 OID 16501)
-- Name: categoria categoria_tipo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.categoria
    ADD CONSTRAINT categoria_tipo_id_fkey FOREIGN KEY (tipo_id) REFERENCES public.tipo_categoria(id);


--
-- TOC entry 5164 (class 2606 OID 16913)
-- Name: cierre cierre_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.cierre
    ADD CONSTRAINT cierre_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 5144 (class 2606 OID 16632)
-- Name: componente_combo componente_combo_combo_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.componente_combo
    ADD CONSTRAINT componente_combo_combo_producto_id_fkey FOREIGN KEY (combo_producto_id) REFERENCES public.producto(id) ON DELETE CASCADE;


--
-- TOC entry 5145 (class 2606 OID 16637)
-- Name: componente_combo componente_combo_producto_hijo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.componente_combo
    ADD CONSTRAINT componente_combo_producto_hijo_id_fkey FOREIGN KEY (producto_hijo_id) REFERENCES public.producto(id) ON DELETE CASCADE;


--
-- TOC entry 5170 (class 2606 OID 16987)
-- Name: compra compra_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.compra
    ADD CONSTRAINT compra_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedor(id);


--
-- TOC entry 5171 (class 2606 OID 16992)
-- Name: compra compra_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.compra
    ADD CONSTRAINT compra_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 5172 (class 2606 OID 17010)
-- Name: detalle_compra detalle_compra_compra_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT detalle_compra_compra_id_fkey FOREIGN KEY (compra_id) REFERENCES public.compra(id) ON DELETE CASCADE;


--
-- TOC entry 5173 (class 2606 OID 17015)
-- Name: detalle_compra detalle_compra_ingrediente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_compra
    ADD CONSTRAINT detalle_compra_ingrediente_id_fkey FOREIGN KEY (ingrediente_id) REFERENCES public.ingrediente(id);


--
-- TOC entry 5148 (class 2606 OID 16723)
-- Name: detalle_pedido detalle_pedido_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_pedido
    ADD CONSTRAINT detalle_pedido_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedido(id) ON DELETE CASCADE;


--
-- TOC entry 5149 (class 2606 OID 16728)
-- Name: detalle_pedido detalle_pedido_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_pedido
    ADD CONSTRAINT detalle_pedido_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.producto(id);


--
-- TOC entry 5142 (class 2606 OID 16613)
-- Name: detalle_receta detalle_receta_ingrediente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_receta
    ADD CONSTRAINT detalle_receta_ingrediente_id_fkey FOREIGN KEY (ingrediente_id) REFERENCES public.ingrediente(id);


--
-- TOC entry 5143 (class 2606 OID 16608)
-- Name: detalle_receta detalle_receta_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.detalle_receta
    ADD CONSTRAINT detalle_receta_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.producto(id) ON DELETE CASCADE;


--
-- TOC entry 5156 (class 2606 OID 17171)
-- Name: movimiento_caja fk_movcaja_cierre; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_caja
    ADD CONSTRAINT fk_movcaja_cierre FOREIGN KEY (cierre_id) REFERENCES public.cierre(id);


--
-- TOC entry 5160 (class 2606 OID 17020)
-- Name: movimiento_inventario fk_movinv_compra; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT fk_movinv_compra FOREIGN KEY (compra_id) REFERENCES public.compra(id);


--
-- TOC entry 5150 (class 2606 OID 16919)
-- Name: pago fk_pago_cierre; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pago
    ADD CONSTRAINT fk_pago_cierre FOREIGN KEY (cierre_id) REFERENCES public.cierre(id);


--
-- TOC entry 5174 (class 2606 OID 17038)
-- Name: historial_accion historial_accion_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.historial_accion
    ADD CONSTRAINT historial_accion_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 5140 (class 2606 OID 16584)
-- Name: ingrediente ingrediente_categoria_insumo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.ingrediente
    ADD CONSTRAINT ingrediente_categoria_insumo_id_fkey FOREIGN KEY (categoria_insumo_id) REFERENCES public.categoria_insumo(id);


--
-- TOC entry 5141 (class 2606 OID 16589)
-- Name: ingrediente ingrediente_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.ingrediente
    ADD CONSTRAINT ingrediente_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedor(id);


--
-- TOC entry 5157 (class 2606 OID 16820)
-- Name: movimiento_caja movimiento_caja_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_caja
    ADD CONSTRAINT movimiento_caja_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedido(id);


--
-- TOC entry 5158 (class 2606 OID 16815)
-- Name: movimiento_caja movimiento_caja_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_caja
    ADD CONSTRAINT movimiento_caja_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 5159 (class 2606 OID 16825)
-- Name: movimiento_caja movimiento_caja_vale_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_caja
    ADD CONSTRAINT movimiento_caja_vale_id_fkey FOREIGN KEY (vale_id) REFERENCES public.vale(id);


--
-- TOC entry 5161 (class 2606 OID 16848)
-- Name: movimiento_inventario movimiento_inventario_ingrediente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_ingrediente_id_fkey FOREIGN KEY (ingrediente_id) REFERENCES public.ingrediente(id);


--
-- TOC entry 5162 (class 2606 OID 16853)
-- Name: movimiento_inventario movimiento_inventario_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedido(id);


--
-- TOC entry 5163 (class 2606 OID 16858)
-- Name: movimiento_inventario movimiento_inventario_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.movimiento_inventario
    ADD CONSTRAINT movimiento_inventario_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 5151 (class 2606 OID 16764)
-- Name: pago pago_devuelto_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pago
    ADD CONSTRAINT pago_devuelto_por_fkey FOREIGN KEY (devuelto_por) REFERENCES public.usuario(id);


--
-- TOC entry 5152 (class 2606 OID 16754)
-- Name: pago pago_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pago
    ADD CONSTRAINT pago_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedido(id);


--
-- TOC entry 5153 (class 2606 OID 16759)
-- Name: pago pago_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pago
    ADD CONSTRAINT pago_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 5146 (class 2606 OID 16689)
-- Name: pedido pedido_mesa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_mesa_id_fkey FOREIGN KEY (mesa_id) REFERENCES public.mesa(id);


--
-- TOC entry 5147 (class 2606 OID 16694)
-- Name: pedido pedido_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.pedido
    ADD CONSTRAINT pedido_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 5165 (class 2606 OID 16959)
-- Name: preparado preparado_detalle_origen_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.preparado
    ADD CONSTRAINT preparado_detalle_origen_id_fkey FOREIGN KEY (detalle_origen_id) REFERENCES public.detalle_pedido(id);


--
-- TOC entry 5166 (class 2606 OID 16964)
-- Name: preparado preparado_pedido_nuevo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.preparado
    ADD CONSTRAINT preparado_pedido_nuevo_id_fkey FOREIGN KEY (pedido_nuevo_id) REFERENCES public.pedido(id);


--
-- TOC entry 5167 (class 2606 OID 16954)
-- Name: preparado preparado_pedido_origen_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.preparado
    ADD CONSTRAINT preparado_pedido_origen_id_fkey FOREIGN KEY (pedido_origen_id) REFERENCES public.pedido(id);


--
-- TOC entry 5168 (class 2606 OID 16949)
-- Name: preparado preparado_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.preparado
    ADD CONSTRAINT preparado_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.producto(id);


--
-- TOC entry 5169 (class 2606 OID 16969)
-- Name: preparado preparado_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.preparado
    ADD CONSTRAINT preparado_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 5138 (class 2606 OID 16528)
-- Name: producto producto_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.producto
    ADD CONSTRAINT producto_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categoria(id);


--
-- TOC entry 5139 (class 2606 OID 17101)
-- Name: producto producto_empaque_llevar_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.producto
    ADD CONSTRAINT producto_empaque_llevar_id_fkey FOREIGN KEY (empaque_llevar_id) REFERENCES public.producto(id) ON DELETE SET NULL;


--
-- TOC entry 5175 (class 2606 OID 17056)
-- Name: turno_laboral turno_laboral_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.turno_laboral
    ADD CONSTRAINT turno_laboral_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE CASCADE;


--
-- TOC entry 5136 (class 2606 OID 16471)
-- Name: usuario usuario_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.rol(id);


--
-- TOC entry 5154 (class 2606 OID 16790)
-- Name: vale vale_cobrado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.vale
    ADD CONSTRAINT vale_cobrado_por_fkey FOREIGN KEY (cobrado_por) REFERENCES public.usuario(id);


--
-- TOC entry 5155 (class 2606 OID 16785)
-- Name: vale vale_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: restaurante
--

ALTER TABLE ONLY public.vale
    ADD CONSTRAINT vale_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedido(id);


-- Completed on 2026-10-09 21:03:12

--
-- PostgreSQL database dump complete
--

\unrestrict KRHFsrFfhHNaYFQXutqk787Bc0XnEdMj5xwTznYuzwtfZQQT7guRriSEGRUeCcY

