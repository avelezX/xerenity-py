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

    all_series = banrep + HARDCODED_SERIES
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
