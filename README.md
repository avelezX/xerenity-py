# xerenity

Librería Python para acceder a datos financieros, series de tiempo y marcas de mercado de la plataforma [Xerenity](https://xerenity.vercel.app).

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

## Módulos

| Módulo | Descripción |
|--------|-------------|
| `x.series` | Series de tiempo por ticker |
| `x.marks` | Marcas diarias de curvas de tasas |
| `x.loans` | Gestión de créditos |

## Registro

Requiere cuenta en [xerenity.vercel.app](https://xerenity.vercel.app/login).
