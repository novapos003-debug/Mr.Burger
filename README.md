# Mr. Burger POS

Sistema de punto de venta para el restaurante Mr. Burger (Cali): caja, meseros, cocina,
inventario con recetas y panel de administración.

- **En el local:** un PC con Windows es el servidor. Celulares y tablet se conectan por Wi-Fi a
  su IP. Funciona sin internet.
- **En la nube:** un espejo (Render + Supabase + Firebase) que la caja mantiene al día para que
  el dueño vea y administre desde cualquier lugar.

## Documentos

| Documento | Para qué |
|---|---|
| [`GUIA_INSTALACION_RESTAURANTE.txt`](GUIA_INSTALACION_RESTAURANTE.txt) | Pasos para instalar y poner a funcionar el sistema en el local |
| [`DOCUMENTO_DE_LA_VERDAD.md`](DOCUMENTO_DE_LA_VERDAD.md) | Referencia completa: arquitectura, reglas del negocio, base de datos, sincronización y estado actual |

## Instalar o actualizar (PC de caja, Windows)

Requisitos: Windows 10/11, Git, Python 3.11, PostgreSQL y Google Chrome.

1. Doble clic en `actualizar_windows.bat`. Descarga la última versión, revisa componentes, base
   de datos, token de la nube, respaldo diario, firewall e impresora, y abre la caja.
2. Si avisa que falta el firewall: clic derecho en `configurar_firewall_windows.bat` >
   "Ejecutar como administrador".

Para el día a día: `iniciar_windows.bat`. Si algo falla: `estado_sistema.bat`.

## Tecnología

FastAPI + SQLAlchemy + PostgreSQL en `backend/`; React + Vite (PWA) en `frontend/`, cuyo
compilado (`frontend/dist`) va en el repositorio para que el PC de caja no necesite Node.
Pruebas automáticas en `pruebas/`.
