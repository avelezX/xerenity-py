"""
Script para generar xerenity/catalog.py parseando los archivos de migración SQL.

Uso:
    python3 scripts/generate_catalog.py [ruta-xerenity-db]

Por defecto asume que xerenity-db está en ../../xerenity-db relativo a este script.
No requiere conexión a la base de datos ni dependencias externas.

Genera el archivo xerenity/catalog.py con el catálogo completo de series
organizado por grupo → sub_group → display_name: ticker.

Ejecutar antes de cada release para mantener el catálogo actualizado.
"""

import hashlib
import os
import re
import sys
from collections import defaultdict
from datetime import date

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(SCRIPT_DIR, "..")
OUTPUT_PATH = os.path.join(REPO_ROOT, "xerenity", "catalog.py")

# Default path to xerenity-db (sibling repo)
DEFAULT_XERENITY_DB = os.path.join(REPO_ROOT, "..", "xerenity-db")


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


# ── Banrep series parser ───────────────────────────────────────────────────────

# Pattern matches: (int, 'str', 'str', 'str', 'str', 'str')
# Values can contain escaped single quotes ('')
_ROW_RE = re.compile(
    r"\(\s*(\d+)\s*,"           # id
    r"\s*'((?:[^']|'')*?)'\s*," # nombre
    r"\s*'((?:[^']|'')*?)'\s*," # description
    r"\s*'((?:[^']|'')*?)'\s*," # fuente
    r"\s*'((?:[^']|'')*?)'\s*," # sub_group
    r"\s*'((?:[^']|'')*?)'\s*\)",  # grupo
)


def parse_banrep_series(migration_file: str) -> list[dict]:
    """Parse banrep_serie_v2 INSERT rows from a migration SQL file."""
    with open(migration_file, encoding="utf-8") as f:
        content = f.read()

    series = []
    for m in _ROW_RE.finditer(content):
        id_ = int(m.group(1))
        nombre = m.group(2).replace("''", "'")
        sub_group = m.group(5).replace("''", "'")
        grupo = m.group(6).replace("''", "'")
        series.append({
            "id": id_,
            "display_name": nombre,
            "grupo": grupo or "Sin categoría",
            "sub_group": sub_group or "General",
            "ticker": md5(str(id_)),
        })
    return series


# ── Hardcoded series from search_mv ──────────────────────────────────────────
# These are series defined inline in the search_mv SQL (not from a table).
# source: migrations/202502191201_update_search_mv_fic_categorization.sql
#         migrations/202502201500_us_rates_in_series_catalog.sql

HARDCODED_SERIES = [
    # Tasas Implícitas (IBR forward)
    {"source_name": "ibr_implicita_1m",  "display_name": "IBR 1M",   "grupo": "Tasas Implícitas", "sub_group": "IBR Implicito"},
    {"source_name": "ibr_implicita_3m",  "display_name": "IBR 3M",   "grupo": "Tasas Implícitas", "sub_group": "IBR Implicito"},
    {"source_name": "ibr_implicita_6m",  "display_name": "IBR 6M",   "grupo": "Tasas Implícitas", "sub_group": "IBR Implicito"},
    {"source_name": "ibr_implicita_12m", "display_name": "IBR 12M",  "grupo": "Tasas Implícitas", "sub_group": "IBR Implicito"},
    # Divisas
    {"source_name": "TRM",           "display_name": "Tasa Representativa del Mercado (TRM)", "grupo": "Divisas", "sub_group": "Colombia"},
    {"source_name": "cop_ndf_interpol", "display_name": "COP NDF Interpol", "grupo": "Divisas", "sub_group": "COP NDF"},
    # Precios
    {"source_name": "uvr_projection",    "display_name": "Proyección UVR",       "grupo": "Índices de Precios", "sub_group": "IPC Implícito"},
    {"source_name": "inflacion_implicita","display_name": "Inflación Implícita",  "grupo": "Índices de Precios", "sub_group": "IPC Implícito"},
    # IBR-OIS (DTCC swaps)
    {"source_name": "ibr_1m",  "display_name": "IBR OIS 1 mes",   "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_3m",  "display_name": "IBR OIS 3 meses", "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_6m",  "display_name": "IBR OIS 6 meses", "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_9m",  "display_name": "IBR OIS 9 meses", "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_12m", "display_name": "IBR OIS 12 meses","grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_2y",  "display_name": "IBR OIS 2 años",  "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_3y",  "display_name": "IBR OIS 3 años",  "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_4y",  "display_name": "IBR OIS 4 años",  "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_5y",  "display_name": "IBR OIS 5 años",  "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_7y",  "display_name": "IBR OIS 7 años",  "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_10y", "display_name": "IBR OIS 10 años", "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_12y", "display_name": "IBR OIS 12 años", "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_15y", "display_name": "IBR OIS 15 años", "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    {"source_name": "ibr_20y", "display_name": "IBR OIS 20 años", "grupo": "IBR-SWAP", "sub_group": "IBR-OIS"},
    # SOFR OIS swaps (22 tenors)
    *[
        {"source_name": f"sofr_swap_{m}", "display_name": f"SOFR Swap {label}", "grupo": "Tasas Internacionales", "sub_group": "SOFR Swaps"}
        for m, label in [
            (1,"1M"),(2,"2M"),(3,"3M"),(6,"6M"),(9,"9M"),(12,"1Y"),
            (18,"18M"),(24,"2Y"),(36,"3Y"),(48,"4Y"),(60,"5Y"),(84,"7Y"),
            (120,"10Y"),(144,"12Y"),(180,"15Y"),(240,"20Y"),(360,"30Y"),
            (420,"35Y"),(480,"40Y"),(540,"45Y"),(600,"50Y"),
        ]
    ],
    # US Treasury Nominal
    *[
        {"source_name": f"ust_nominal_{m}", "display_name": f"UST Nominal {label}", "grupo": "Tasas Internacionales", "sub_group": "UST Nominal"}
        for m, label in [
            (1,"1M"),(2,"2M"),(3,"3M"),(6,"6M"),(12,"1Y"),
            (24,"2Y"),(36,"3Y"),(60,"5Y"),(84,"7Y"),(120,"10Y"),
            (240,"20Y"),(360,"30Y"),
        ]
    ],
    # US Reference Rates
    {"source_name": "SOFR",         "display_name": "SOFR Overnight",         "grupo": "Tasas Internacionales", "sub_group": "Tasas de Referencia US"},
    {"source_name": "EFFR",         "display_name": "Fed Funds Rate (EFFR)",   "grupo": "Tasas Internacionales", "sub_group": "Tasas de Referencia US"},
    {"source_name": "OBFR",         "display_name": "Overnight Bank Funding Rate (OBFR)", "grupo": "Tasas Internacionales", "sub_group": "Tasas de Referencia US"},
    {"source_name": "SOFR_AVG_30D", "display_name": "SOFR Promedio 30 días",  "grupo": "Tasas Internacionales", "sub_group": "Tasas de Referencia US"},
    {"source_name": "SOFR_AVG_90D", "display_name": "SOFR Promedio 90 días",  "grupo": "Tasas Internacionales", "sub_group": "Tasas de Referencia US"},
    {"source_name": "SOFR_AVG_180D","display_name": "SOFR Promedio 180 días", "grupo": "Tasas Internacionales", "sub_group": "Tasas de Referencia US"},
    # COP forward tenors
    *[
        {"source_name": f"cop_fwd_{t}", "display_name": f"COP Forward {label}", "grupo": "Divisas", "sub_group": "COP Forward"}
        for t, label in [
            ("spot","Spot"),("1m","1M"),("2m","2M"),("3m","3M"),
            ("6m","6M"),("9m","9M"),("1y","1Y"),
        ]
    ],
]

# Compute tickers for hardcoded series
for s in HARDCODED_SERIES:
    s["ticker"] = md5(s["source_name"])


# ── Series de construcción / vivienda / suelo ────────────────────────────────
# Camacol (camacol_serie), DANE ICOCIV (icociv_serie) y UAECD/Catastro
# (catastro_series_value). Estas alimentan el tab /construccion del FE.
# El ticker en search_mv es md5('<fuente>_<id>') (namespaced, ver migraciones
# 20260731_lagos_torca_* e 20260731_icociv_dane_collector.sql). Verificado
# contra search_mv el 2026-08-03.
# Formato: (prefijo_fuente, id, display_name, sub_group)
_CONSTRUCCION_RAW = [
    ("camacol", 1, "PIB Edificaciones", "PIB"),
    ("camacol", 2, "PIB Obras Civiles", "PIB"),
    ("camacol", 3, "PIB Actividades Especializadas", "PIB"),
    ("camacol", 4, "PIB Construccion Total", "PIB"),
    ("camacol", 5, "PIB Total Colombia", "PIB"),
    ("camacol", 6, "PIB Edificaciones Var%", "PIB"),
    ("camacol", 7, "PIB Obras Civiles Var%", "PIB"),
    ("camacol", 8, "PIB Act. Especializadas Var%", "PIB"),
    ("camacol", 9, "PIB Construccion Total Var%", "PIB"),
    ("camacol", 10, "PIB Total Colombia Var%", "PIB"),
    ("camacol", 11, "ICOCED Total", "Costos"),
    ("camacol", 12, "ICOCED Var Mensual", "Costos"),
    ("camacol", 13, "ICOCED Var Ano Corrido", "Costos"),
    ("camacol", 14, "ICOCED Var Anual", "Costos"),
    ("camacol", 15, "Cemento Produccion", "Cemento"),
    ("camacol", 16, "Cemento Despachos", "Cemento"),
    ("camacol", 17, "Cemento Produccion Var% Anual", "Cemento"),
    ("camacol", 18, "Cemento Despachos Var% Anual", "Cemento"),
    ("camacol", 19, "Financiacion Constr NoVIS Pesos", "Financiacion"),
    ("camacol", 20, "Financiacion Constr NoVIS UVR", "Financiacion"),
    ("camacol", 21, "Financiacion Constr VIS Pesos", "Financiacion"),
    ("camacol", 22, "Financiacion Constr VIS UVR", "Financiacion"),
    ("camacol", 23, "Financiacion Adq NoVIS Pesos", "Financiacion"),
    ("camacol", 24, "Financiacion Adq NoVIS UVR", "Financiacion"),
    ("camacol", 25, "Financiacion Adq VIS Pesos", "Financiacion"),
    ("camacol", 26, "Financiacion Adq VIS UVR", "Financiacion"),
    ("camacol", 27, "IPVN Indice Nacional", "Precios Vivienda"),
    ("camacol", 28, "IPVN Var Trimestral", "Precios Vivienda"),
    ("camacol", 29, "IPVN Var Anual", "Precios Vivienda"),
    ("camacol", 30, "PIB Edificaciones Var% anual", "PIB"),
    ("camacol", 31, "PIB Obras Civiles Var% anual", "PIB"),
    ("camacol", 32, "PIB Act. Especializadas Var% anual", "PIB"),
    ("camacol", 33, "PIB Construccion Total Var% anual", "PIB"),
    ("camacol", 34, "PIB Total Colombia Var% anual", "PIB"),
    ("catastro", 1, "Precio del suelo Bogota - Mediana $/m2 (Catastro)", "Suelo Bogota (Catastro)"),
    ("catastro", 2, "Precio del suelo Bogota - Promedio $/m2 (Catastro)", "Suelo Bogota (Catastro)"),
    ("icociv", 1, "ICOCIV Total", "Costos"),
    ("icociv", 2, "ICOCIV Var Mensual", "Costos"),
    ("icociv", 3, "ICOCIV Var Ano Corrido", "Costos"),
    ("icociv", 4, "ICOCIV Var Anual", "Costos"),
]

CONSTRUCCION_SERIES = [
    {
        "display_name": name,
        "grupo": "Construcción",
        "sub_group": sub,
        "ticker": md5(f"{prefix}_{id_}"),
    }
    for prefix, id_, name, sub in _CONSTRUCCION_RAW
]


# ── Series BanRep con id 1–33 ────────────────────────────────────────────────
# La migración 202502191200_expand_banrep_series_v2_metadata.sql (fuente del
# parser) arranca en id 34, así que los ids 1–33 (sembrados en migraciones
# anteriores) nunca entraban al catálogo — incluyendo IPC, IBR, TRM, política
# monetaria, COLCAP, M1/M2/M3, DTF, UVR y TES. Ticker = md5(str(id)) como el
# resto de banrep_serie_v2. Snapshot de banrep_serie_v2 el 2026-08-03.
# Formato: (id, display_name, grupo, sub_group)
_BANREP_LOW_IDS = [
    (1,  "Tasa de Desempleo", "Empleo y Salarios", "Empleo"),
    (2,  "Tasa de Empleo", "Empleo y Salarios", "Empleo"),
    (3,  "PIB Trimestral - Oferta - Total - Precios Constantes de 2015", "Cuentas Nacionales", "PIB Oferta"),
    (4,  "PIB Trimestral - Oferta - Construcción - Precios Constantes de 2015", "Cuentas Nacionales", "PIB Construcción"),
    (5,  "PIB Trimestral - Demanda - Formación bruta de capital - Precios Constantes de 2015", "Cuentas Nacionales", "PIB Demanda"),
    (6,  "PIB Trimestral - Demanda - Consumo Final - Precios Constantes de 2015", "Cuentas Nacionales", "PIB Demanda"),
    (7,  "IPC Base 2018", "Índices de Precios", "IPC"),
    (8,  "Tasa de Politica Monetaria", "Política Monetaria", "Tasa de Política Monetaria"),
    (9,  "Indicador Bancario de Referencia (IBR) overnight, nominal", "Tasas de Interés", "IBR"),
    (10, "Indicador Bancario de Referencia (IBR) overnight, efectiva", "Tasas de Interés", "IBR"),
    (11, "Indicador Bancario de Referencia (IBR) 1 Mes, nominal", "Tasas de Interés", "IBR"),
    (12, "Indicador Bancario de Referencia (IBR) 1 Mes, efectiva", "Tasas de Interés", "IBR"),
    (13, "Indicador Bancario de Referencia (IBR) 3 Meses, nominal", "Tasas de Interés", "IBR"),
    (14, "Indicador Bancario de Referencia (IBR) 3 Meses, efectiva", "Tasas de Interés", "IBR"),
    (15, "Indicador Bancario de Referencia (IBR) 6 Meses, nominal", "Tasas de Interés", "IBR"),
    (16, "Indicador Bancario de Referencia (IBR) 6 Meses, efectiva", "Tasas de Interés", "IBR"),
    (17, "Indicador Bancario de Referencia (IBR) 12 Meses, nominal", "Tasas de Interés", "IBR"),
    (18, "Indicador Bancario de Referencia (IBR) 12 Meses, efectiva", "Tasas de Interés", "IBR"),
    (19, "Unidad de Valor Real (UVR)", "Índices de Precios", "IPC"),
    (20, "Tasas de interés de los certificados de depósito a término 90 días (DTF) - Mensual", "Tasas de Captación", "DTF"),
    (21, "Tasas de interés de los certificados de depósito a término 90 días (DTF) - Semanal", "Tasas de Captación", "DTF"),
    (22, "Tasas de interés de los certificados de depósito a término (CDT) 180 días - Semanal", "Tasas de Captación", "CDT"),
    (23, "Tasas de interés de los certificados de depósito a término (CDT) 360 días - Semanal", "Tasas de Captación", "CDT"),
    (24, "Tasa interbancaria (TIB)", "Tasas de Interés", "TIB"),
    (25, "Tasa Representativa del Mercado (TRM)", "Divisas", "TRM"),
    (26, "Índice COLCAP", "Sector Externo", "COLCAP"),
    (27, "M1, mensual", "Agregados Monetarios", "Agregados"),
    (28, "M2, mensual", "Agregados Monetarios", "Agregados"),
    (29, "M3, mensual", "Agregados Monetarios", "Agregados"),
    (30, "Tasa de interés fin de mes de los certificados de depósito a término a 90 días, CDT 90 para bancos y corporaciones", "Tasas de Captación", "CDT Mensual"),
    (31, "Tasa de interés Cero Cupón, Títulos de Tesorería (TES), pesos - 1 año", "Renta Fija", "TES Tasas"),
    (32, "Tasa de interés Cero Cupón, Títulos de Tesorería (TES), pesos - 5 años", "Renta Fija", "TES Tasas"),
    (33, "Tasa de interés Cero Cupón, Títulos de Tesorería (TES), pesos - 10 años", "Renta Fija", "TES Tasas"),
]

BANREP_LOW_ID_SERIES = [
    {"display_name": name, "grupo": grupo, "sub_group": sub, "ticker": md5(str(id_))}
    for id_, name, grupo, sub in _BANREP_LOW_IDS
]


# ── Catalog builder ───────────────────────────────────────────────────────────

def build_catalog(all_series: list[dict]) -> dict:
    catalog = defaultdict(lambda: defaultdict(dict))
    seen = set()
    for s in all_series:
        grupo = (s.get("grupo") or "Sin categoría").strip()
        sub = (s.get("sub_group") or "General").strip()
        name = (s.get("display_name") or "").strip()
        ticker = (s.get("ticker") or "").strip()
        key = (grupo, sub, name)
        if name and ticker and key not in seen:
            catalog[grupo][sub][name] = ticker
            seen.add(key)
    return catalog


def render_catalog(catalog: dict) -> str:
    lines = [
        '"""',
        "Xerenity Series Catalog",
        f"Generado automáticamente el {date.today().isoformat()}.",
        "NO EDITAR MANUALMENTE.",
        "",
        "Para regenerar:",
        "    python3 scripts/generate_catalog.py",
        '"""',
        "",
        "from typing import Dict",
        "",
        "CATALOG: Dict[str, Dict[str, Dict[str, str]]] = {",
    ]

    for grupo in sorted(catalog):
        lines.append(f"    {grupo!r}: {{")
        for sub in sorted(catalog[grupo]):
            lines.append(f"        {sub!r}: {{")
            for name in sorted(catalog[grupo][sub]):
                ticker = catalog[grupo][sub][name]
                lines.append(f"            {name!r}: {ticker!r},")
            lines.append("        },")
        lines.append("    },")

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    db_root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XERENITY_DB
    db_root = os.path.abspath(db_root)

    migration_file = os.path.join(
        db_root, "migrations", "202502191200_expand_banrep_series_v2_metadata.sql"
    )

    if not os.path.exists(migration_file):
        print(f"ERROR: No se encontró el archivo de migración:\n  {migration_file}")
        print(f"Pasa la ruta de xerenity-db como argumento:")
        print(f"  python3 scripts/generate_catalog.py /ruta/a/xerenity-db")
        sys.exit(1)

    print(f"Parseando series BanRep desde migraciones...")
    banrep = parse_banrep_series(migration_file)
    print(f"  {len(banrep)} series BanRep encontradas")
    print(f"  {len(HARDCODED_SERIES)} series adicionales (IBR-OIS, SOFR, UST, Divisas...)")
    print(f"  {len(CONSTRUCCION_SERIES)} series de construcción/vivienda/suelo (Camacol, ICOCIV, Catastro)")
    print(f"  {len(BANREP_LOW_ID_SERIES)} series BanRep id 1-33 (IPC, IBR, TRM, política monetaria...)")

    all_series = banrep + HARDCODED_SERIES + CONSTRUCCION_SERIES + BANREP_LOW_ID_SERIES
    catalog = build_catalog(all_series)

    total = sum(len(s) for sg in catalog.values() for s in sg.values())
    print(f"  {len(catalog)} grupos, {total} series en catálogo")

    content = render_catalog(catalog)
    out = os.path.abspath(OUTPUT_PATH)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Escrito en: {out}")
    print("Listo.")


if __name__ == "__main__":
    main()
