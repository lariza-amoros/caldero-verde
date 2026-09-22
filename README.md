# Caldero Verde — Prototipo MVP

Prototipo funcional para reducir el desperdicio de alimentos completando el ciclo:

`Inventario -> Receta -> Preparación -> Sobra -> Reutilización`

## Demostración

- **Aplicación pública:** https://sage-kelpie-5644bb.netlify.app/
- **Repositorio independiente:** https://github.com/lariza-amoros/caldero-verde

La demostración permite consultar inventario y recetas sin credenciales. Las
operaciones que modifican datos requieren el código privado del prototipo.

## Funciones del MVP

- Inventario con cantidad, unidad, categoría y fecha de vencimiento.
- Priorización de alimentos próximos a vencer.
- Recetas con ingredientes, cantidades e instrucciones.
- Estado **Puedes preparar** o detalle de ingredientes faltantes.
- Preparación transaccional que descuenta primero lo que vence antes.
- Registro de sobras y reutilización como ingredientes.
- Conversiones seguras entre unidades compatibles y biblioteca puertorriqueña.

## Preparación en Windows y VS Code

1. Instala Python 3.11 o 3.12 desde python.org y marca **Add python.exe to PATH** durante la instalación.
2. Cierra y vuelve a abrir VS Code.
3. En la terminal integrada, desde esta carpeta, ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

La API queda disponible en `http://127.0.0.1:5000`. `run.py` usa Waitress,
un servidor apropiado para ejecutar el backend en Windows. Usa `python app.py`
solamente durante desarrollo y depuración.

## Arquitectura de producción

- `frontend/`: aplicación estática publicada en Netlify.
- `netlify/functions/api.ts`: backend serverless de producción. La carga inicial
  se combina en una sola invocación para reducir el consumo de créditos.
- `app.py`: backend Flask equivalente para desarrollo local.
- Supabase: datos persistentes y una función transaccional para preparar recetas.

Las escrituras requieren `APP_ACCESS_PIN`. El navegador conserva el código solo
durante la sesión; la clave secreta de Supabase permanece en el servidor.

## Endpoints

| Método | Ruta | Uso |
|---|---|---|
| GET | `/api/health` | Comprueba la conexión con Supabase |
| GET | `/api/inventory` | Combina productos y sobras, priorizados por vencimiento |
| POST | `/api/inventory` | Registra un alimento |
| GET | `/api/catalog/products` | Productos comunes de la despensa puertorriqueña |
| GET | `/api/catalog/units` | Unidades estándar y alias aceptados |
| GET | `/api/bootstrap` | Inventario, recetas y catálogos en una solicitud |
| GET | `/api/recipes` | Lista recetas, ingredientes y disponibilidad |
| GET | `/api/recipes/<id>/availability` | Explica ingredientes disponibles y faltantes |
| POST | `/api/recipes/<id>/prepare` | Descuenta ingredientes por vencimiento más cercano |
| POST | `/api/leftovers` | Registra una sobra reutilizable |

Ejemplo de un alimento:

```json
{
  "name": "Pimientos",
  "category": "Vegetales",
  "quantity": 3,
  "unit": "unidad",
  "expiration_date": "2026-09-28"
}
```

Ejemplo de una sobra:

```json
{
  "recipe_id": 1,
  "name": "Arroz",
  "quantity": 1,
  "unit": "taza",
  "expiration_date": "2026-09-24"
}
```

Ejecuta las pruebas de la lógica con:

```powershell
python -m unittest discover -s tests -v
```

Pruebas de la Function de producción:

```powershell
node --experimental-strip-types --test tests-js/*.test.mjs
```

VS Code está configurado para seleccionar `.venv\Scripts\python.exe`. Si no lo hace,
usa **Python: Select Interpreter** en la paleta de comandos y selecciona ese archivo.

## Si la consulta devuelve cero filas

Confirma primero en Supabase que `public.products` tenga registros. Si los tiene,
abre **Authentication > Policies** (o la sección de políticas de la tabla) y crea
una política `SELECT` apropiada para el rol que usa la aplicación. Para una tabla
pública de productos, una política típica usa la expresión `true` para `SELECT`.
No desactives RLS globalmente ni pongas la `service_role` key en el frontend.

El archivo `.env` debe contener:

```dotenv
SUPABASE_URL=https://TU_PROJECT_REF.supabase.co
SUPABASE_KEY=TU_CLAVE_PUBLICA_ANON_O_PUBLISHABLE
```

`.env` está excluido de Git porque contiene credenciales.

Para las operaciones de escritura, un backend privado puede usar
`SUPABASE_SECRET_KEY`. No copies esa clave al frontend. Si se mantiene la
Publishable Key, Supabase necesita políticas RLS explícitas para cada escritura.

## Conversiones

El sistema convierte unidades de masa entre sí (`g`, `kg`, `oz`, `lb`) y
unidades de volumen entre sí (`ml`, `l`, `taza`, `cucharada`, `cucharadita`).
Solo convierte masa a volumen cuando existe un perfil específico del alimento.
Actualmente el perfil de arroz seco usa `185 g/taza`. No se convierten libras
de pollo, frutas u otros alimentos a tazas porque el resultado dependería del
corte, preparación y compactación.

RapidFuzz en Flask y `fast-fuzzy` en Netlify reconocen variaciones y errores
menores en nombres de productos. El umbral es deliberadamente alto para evitar
descontar un alimento equivocado.

## Migraciones aplicadas en Supabase

1. `prepare_inventory_transaction`: aplica todos los descuentos de una receta
   en una transacción y revierte todo si el inventario cambió.
2. `seed_puerto_rican_recipe_library`: añade cinco recetas de despensa
   puertorriqueña sin duplicar las existentes.
