# xerenity

Librería Python para acceder a datos financieros, series de tiempo y marcas de mercado de la plataforma [Xerenity](https://xerenity.co).

## Instalación

```bash
pip install xerenity
```

## Uso básico

```python
from xerenity import Xerenity

x = Xerenity("tu@email.com", "tu_password")

# Series de tiempo
ibr = x.series.search("IBR_1D")

# Marcas de mercado diarias
mark = x.marks.all("2026-02-27")
print(mark["ibr"]["ibr_1d"])    # → 9.636
print(mark["has_sofr"])          # → True

# Curva IBR
ibr_curve = x.marks.ibr("2026-02-27")

# Curva SOFR OIS (22 nodos)
import pandas as pd
sofr_df = pd.DataFrame(x.marks.sofr("2026-02-27"))

# Puntos forward NDF COP/USD
ndf_df = pd.DataFrame(x.marks.ndf("2026-02-27"))

# Curva TES soberanos colombianos
tes_df = pd.DataFrame(x.marks.tes("2026-02-27"))
```

## Motor de datos (`x.data`) — nuevo en 0.4.0

Acceso por el mismo motor que usa la plataforma: búsqueda por lenguaje natural
(exacta, por alias, por similitud y por texto completo) sobre **todo** el
catálogo, incluidas las fuentes internacionales y los índices de costos de
construcción. Es aditivo: `x.series` y `x.marks` siguen funcionando igual.

```python
from xerenity import Xerenity

x = Xerenity("tu@email.com", "tu_password")

# Buscar: devuelve candidatos ordenados por relevancia
x.data.search("inflación")
# → [{"label": "Inflación IPC — Total Nacional", "table_name": "banrep_series_value_v2",
#     "slice_value": "...", "confidence": 0.95, "has_data": True}, ...]

# Buscar y traer los datos del mejor resultado, en un solo paso
trm = x.data.get("TRM", desde="2026-01-01")
trm["resolved"]      # → qué serie eligió y con qué confianza
trm["rows"]          # → [{"time": "2026-01-02T00:00:00", "value": 3790.1, ...}, ...]
trm["date_column"]   # → nombre de la columna de fecha en esas filas

# Leer una serie conocida por tabla y slice
x.data.series("currency", "USD:COP", desde="2026-09-01")

# Qué tablas existen, con categoría, país y frescura
x.data.catalog()
```

> `x.data` requiere una cuenta habilitada para el motor. Si tu cuenta no lo
> está, las llamadas devuelven `{"error": ...}` en lugar de lanzar excepción.

## Catálogo de series

El paquete incluye un catálogo estático con **más de 900 series** organizadas por categoría y subcategoría. No requiere conexión para explorar.

### Explorar sin login

```python
from xerenity import CATALOG

# Ver grupos disponibles
print(list(CATALOG.keys()))
# → ['Agregados Crediticios', 'Agregados Monetarios', 'Divisas',
#    'IBR-SWAP', 'Índices de Precios', 'Inflación', 'Política Monetaria',
#    'Renta Fija', 'Sector Externo', 'Sector Fiscal', 'Sector Real',
#    'Tasas Implícitas', 'Tasas Internacionales', 'Tasas de Captación',
#    'Tasas de Colocación', 'Tasas de Interés']

# Ver subcategorías de un grupo
print(list(CATALOG["Sector Real"].keys()))
# → ['Cuentas Nacionales', 'Empleo', 'PIB 1994', 'PIB 2000',
#    'PIB 2005', 'PIB 2015', 'PIB Componentes', ...]

# Ver series de una subcategoría
print(list(CATALOG["Sector Real"]["PIB Componentes"].keys()))
# → ['Consumo final, nominal', 'Consumo final, real',
#    'Exportaciones, nominal', 'Exportaciones, real',
#    'Formación bruta de capital, nominal', 'Formación bruta de capital, real',
#    'Importaciones, nominal', 'Importaciones, real']
```

### Buscar y traer series

```python
from xerenity import Xerenity

x = Xerenity("tu@email.com", "tu_password")

# Buscar por nombre parcial (sin llamada API extra)
resultados = x.series.find("PIB")
# → [{"display_name": "Consumo final, nominal", "grupo": "Sector Real",
#     "sub_group": "PIB Componentes", "ticker": "19bc916..."}]

resultados = x.series.find("IBR")
resultados = x.series.find("inflación")

# Traer datos por nombre exacto (sin conocer el ticker)
consumo = x.series.get("Consumo final, nominal")
# → [{"time": "2024-09-30", "value": 424676.58}, ...]

ibr_1d = x.series.get("Tasa de política monetaria")
sofr_5y = x.series.get("SOFR Swap 5Y")

# Usando el catálogo directamente (con autocomplete en IDEs)
from xerenity import CATALOG

ticker = CATALOG["Sector Real"]["PIB Componentes"]["Consumo final, nominal"]
data = x.series.search(ticker)
```

### Traer un grupo completo con pandas

```python
import pandas as pd
from xerenity import Xerenity, CATALOG

x = Xerenity("tu@email.com", "tu_password")

# Todos los componentes del PIB en un DataFrame
pib = CATALOG["Sector Real"]["PIB Componentes"]
dfs = {name: pd.DataFrame(x.series.search(ticker)).set_index("time")["value"]
       for name, ticker in pib.items()}
pib_df = pd.DataFrame(dfs)
pib_df.index = pd.to_datetime(pib_df.index)
print(pib_df.tail())

# IBR swaps
ibr_swaps = CATALOG["IBR-SWAP"]["IBR-OIS"]
dfs = {name: pd.DataFrame(x.series.search(ticker)).set_index("time")["value"]
       for name, ticker in ibr_swaps.items()}
ibr_df = pd.DataFrame(dfs)
```

### Series de construcción, vivienda y suelo

El catálogo incluye el grupo **`Construcción`** con las series de Camacol
(PIB, ICOCED, Cemento, Financiación, IPVN), el **ICOCIV** del DANE y los
**valores de referencia del suelo de Bogotá** (Catastro / UAECD). Ideal para
exportar a un notebook:

```python
import pandas as pd
from xerenity import Xerenity, CATALOG

x = Xerenity("tu@email.com", "tu_password")

# Sub-grupos disponibles
print(list(CATALOG["Construcción"].keys()))
# → ['Cemento', 'Costos', 'Financiacion', 'PIB', 'Precios Vivienda',
#    'Suelo Bogota (Catastro)']

# Traer una serie puntual por nombre (crudo, sin transformar)
icociv = pd.DataFrame(x.series.get("ICOCIV Total"))          # DANE, base dic-2020=100
ipvn   = pd.DataFrame(x.series.get("IPVN Indice Nacional"))  # Camacol
suelo  = pd.DataFrame(x.series.get("Precio del suelo Bogota - Promedio $/m2 (Catastro)"))

# Traer todo un sub-grupo a un solo DataFrame
costos = CATALOG["Construcción"]["Costos"]   # {display_name: ticker}
df = pd.DataFrame({
    name: pd.DataFrame(x.series.search(t)).set_index("time")["value"]
    for name, t in costos.items()
})
```

Todo llega **crudo** (`[{"time": "YYYY-MM-DD", "value": float}]`); la
normalización a índice base fija queda a tu criterio en el notebook.

## Módulos

| Módulo | Descripción |
|--------|-------------|
| `x.series` | Series de tiempo por ticker, nombre o categoría |
| `x.marks` | Marcas diarias de curvas de tasas (IBR, SOFR, NDF, TES) |
| `x.loans` | Gestión de créditos |
| `CATALOG` | Catálogo estático de series (sin login requerido) |

## Regenerar el catálogo

El archivo `xerenity/catalog.py` es generado automáticamente. Para actualizarlo:

```bash
# Con xerenity-db en la ruta por defecto (../xerenity-db)
python3 scripts/generate_catalog.py

# O especificando la ruta
python3 scripts/generate_catalog.py /ruta/a/xerenity-db
```

## Registro

Requiere cuenta en [xerenity.co](https://xerenity.co/login).
