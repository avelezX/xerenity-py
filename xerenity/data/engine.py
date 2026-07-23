"""
Acceso canónico a datos — sobre el "motor único" de Xerenity.

Este módulo es la cara del SDK sobre las RPCs canónicas de xerenity-db
(`resolve_query`, `query_series`, `list_data_catalog_overview`) descritas en
DESIGN_DATA_ACCESS.md §3. A diferencia de `Series` (que lee el catálogo viejo
`search_mv` + RPC `search` por ticker MD5), acá todo pasa por el mismo motor
que usa el chart-bar del FE — así el SDK y el MCP heredan automáticamente:
  * búsqueda inteligente (exacto / alias / trigram / full-text), no substring;
  * TODAS las series catalogadas (crypto, camacol, curvas IBR, etc.);
  * una sola fuente de verdad (si el FE la encuentra, el SDK también).

Uso:
    x = Xerenity(username, password)
    matches = x.data.search("bitcoin")          # -> [{table_name, slice_value, ...}]
    serie   = x.data.get("TRM")                 # resuelve + trae en una llamada
    serie   = x.data.series("ibr_3m_rate")      # lectura directa por tabla
"""


class DataEngine:
    """Facade del SDK sobre las RPCs canónicas del motor (read-only)."""

    def __init__(self, connection):
        self._conn = connection

    def search(self, query: str, limit: int = 10) -> list:
        """
        Busca series por texto en lenguaje natural vía el resolver canónico
        (`resolve_query`) — el mismo del chart-bar.

        Args:
            query: Texto libre. Ej: 'bitcoin', 'TRM', 'IBR 3M', 'inflacion'.
            limit: Máximo de matches a devolver (ordenados por relevancia).

        Returns:
            [{"table_name", "slice_column", "slice_value", "label",
              "category", "confidence", "match_source"}]  (vacío si no hay match).
        """
        try:
            res = self._conn.call_rpc(
                "resolve_query", {"p_text": query, "p_limit": limit})
            return res or []
        except Exception as er:  # noqa: BLE001 — mantener el estilo del SDK
            return [{"error": str(er)}]

    def series(self, table: str, slice_value: str = None,
               desde: str = None, hasta: str = None, limit: int = 5000) -> dict:
        """
        Lee los valores de una serie vía `query_series` (lectura canónica).

        Args:
            table: Nombre de la tabla/vista. Ej: 'ibr_3m_rate', 'currency'.
            slice_value: Valor del slice si la tabla es sorteada. Ej: 'BTC:USD',
                'USD:COP'. None para tablas single-serie.
            desde / hasta: Rango de fechas 'YYYY-MM-DD' (None = sin acotar; el
                motor devuelve los más recientes hasta `limit`).
            limit: Máximo de filas (hard cap del motor: 50.000).

        Returns:
            {"table_name", "row_count", "rows": [{...}], ...}  o {"error": ...}.
        """
        try:
            return self._conn.call_rpc("query_series", {
                "p_table": table,
                "p_slice_value": slice_value,
                "p_from": desde,
                "p_to": hasta,
                "p_limit": limit,
            })
        except Exception as er:  # noqa: BLE001
            return {"error": str(er)}

    def get(self, query: str, desde: str = None, hasta: str = None,
            limit: int = 5000) -> dict:
        """
        Conveniencia: resuelve el mejor match de `query` y trae su serie en una
        sola llamada (search + series). Ideal para el MCP / un LLM.

        Args:
            query: Texto libre. Ej: 'TRM', 'bitcoin', 'IBR 3M'.
            desde / hasta / limit: igual que `series`.

        Returns:
            El resultado de `series` para el top match, con la clave extra
            "resolved" describiendo qué serie se eligió; o {"error": ...} si no
            hubo match.
        """
        matches = self.search(query, limit=1)
        if not matches or "error" in matches[0]:
            reason = matches[0]["error"] if matches else "sin resultados"
            return {"error": f"Sin match para '{query}': {reason}"}
        top = matches[0]
        out = self.series(top["table_name"], top.get("slice_value"),
                          desde, hasta, limit)
        if isinstance(out, dict):
            out["resolved"] = {
                "label": top.get("label"),
                "table_name": top.get("table_name"),
                "slice_value": top.get("slice_value"),
                "confidence": top.get("confidence"),
            }
        return out

    def catalog(self) -> list:
        """
        Catálogo completo de tablas disponibles vía `list_data_catalog_overview`
        (qué existe, con metadata: categoría, país, frescura, n de series).
        """
        try:
            res = self._conn.call_rpc("list_data_catalog_overview", {})
            return res or []
        except Exception as er:  # noqa: BLE001
            return [{"error": str(er)}]
