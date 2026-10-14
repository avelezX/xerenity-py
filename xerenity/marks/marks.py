"""
Marcas de mercado diarias — curvas de tasas por fecha.

Expone los datos almacenados en Supabase para cada sesión de mercado:
  - IBR: curva de tasas overnight colombiana (1d → 20y)
  - SOFR: curva OIS en USD (1m → 50y)
  - NDF: forwards USD/COP indicativos de FXEmpire por tenor (tabla
    cop_fwd_points; sin datos entre el 2026-03-13 y el 2026-10-13)
  - TES: curva de rendimientos de TES soberanos colombianos

Uso:
    x = Xerenity(username, password)
    mark = x.marks.all("2026-02-27")
    ibr  = x.marks.ibr("2026-02-27")

Cada método devuelve un dict (o lista de dicts) listo para usar con pandas:
    import pandas as pd
    df = pd.DataFrame(x.marks.sofr("2026-02-27"))
"""

class Marks:
    """
    Acceso a marcas diarias de mercado (curvas de tasas por fecha).

    Instanciado automáticamente por la clase Xerenity — no crear directamente.
    """

    def __init__(self, connection):
        self._conn = connection

    # ── IBR ──────────────────────────────────────────────────────────────────

    def ibr(self, fecha: str) -> dict | None:
        """
        Curva IBR para una fecha dada.

        Args:
            fecha: Fecha en formato 'YYYY-MM-DD'

        Returns:
            Dict con los nodos de la curva (ibr_1d, ibr_1m, …, ibr_20y)
            o None si no hay datos para esa fecha.

        Example:
            >>> mark = x.marks.ibr("2026-02-27")
            >>> mark["ibr_1d"]   # 9.636
            >>> mark["ibr_5y"]   # 11.67
        """
        res = (
            self._conn.supabase
            .from_("ibr_quotes_curve")
            .select("*")
            .like("fecha", f"{fecha}%")
            .limit(1)
            .maybe_single()
            .execute()
        )
        # supabase-py 2.x devuelve None (no un objeto con .data=None) cuando
        # maybe_single() no encuentra fila: pasa en fines de semana, festivos
        # o antes de que BanRep publique el IBR del día. Sin esto, ibr() y
        # all() lanzaban AttributeError en vez de devolver None.
        return res.data if res is not None else None

    # ── SOFR ─────────────────────────────────────────────────────────────────

    def sofr(self, fecha: str) -> list[dict]:
        """
        Curva SOFR OIS para una fecha dada.

        Args:
            fecha: Fecha en formato 'YYYY-MM-DD'

        Returns:
            Lista de dicts [{tenor_months: int, swap_rate: float}, …]
            ordenados por tenor.

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame(x.marks.sofr("2026-02-27"))
            >>> df.set_index("tenor_months")["swap_rate"]
        """
        res = (
            self._conn.supabase
            .from_("sofr_swap_curve")
            .select("tenor_months, swap_rate")
            .eq("fecha", fecha)
            .order("tenor_months")
            .execute()
        )
        return res.data or []

    # ── NDF ──────────────────────────────────────────────────────────────────

    def ndf(self, fecha: str) -> list[dict]:
        """
        Puntos forward COP/USD (NDF) para una fecha dada.

        Args:
            fecha: Fecha en formato 'YYYY-MM-DD'

        Returns:
            Lista de dicts [{tenor, tenor_months, fwd_points, mid}, …]
            ordenados por tenor_months.

        Example:
            >>> df = pd.DataFrame(x.marks.ndf("2026-02-27"))
        """
        res = (
            self._conn.supabase
            .from_("cop_fwd_points")
            .select("tenor, tenor_months, fwd_points, mid")
            .eq("fecha", fecha)
            .order("tenor_months")
            .execute()
        )
        return res.data or []

    # ── TES ──────────────────────────────────────────────────────────────────

    def tes(self, fecha: str) -> list[dict]:
        """
        Curva de rendimientos TES (bonos soberanos colombianos) para una fecha.

        Args:
            fecha: Fecha en formato 'YYYY-MM-DD'

        Returns:
            Lista de dicts [{maturity_date, yield, duration}, …]
            ordenados por vencimiento.

        Example:
            >>> df = pd.DataFrame(x.marks.tes("2026-02-27"))
        """
        try:
            res = self._conn.supabase.rpc(
                "get_tes_yield_curve_for_date",
                {"p_money": "COLTES-COP", "p_fecha": fecha},
            ).execute()
            return res.data or []
        except Exception:
            # Fallback: query directa a tes_operation si el RPC falla. La tabla
            # vive en el schema xerenity (la sesion del usuario), no en
            # "trading": hasta oct-2026 este fallback usaba un cliente anonimo
            # aparte con schema=trading y siempre fallaba.
            res = (
                self._conn.supabase
                .from_("tes_operation")
                .select("date, tes, yield, volume")
                .like("date", f"{fecha}%")
                .order("yield")
                .execute()
            )
            return res.data or []

    # ── All ───────────────────────────────────────────────────────────────────

    def all(self, fecha: str) -> dict:
        """
        Todas las curvas de mercado para una fecha.

        Args:
            fecha: Fecha en formato 'YYYY-MM-DD'

        Returns:
            {
              "fecha": "YYYY-MM-DD",
              "ibr":  dict | None,
              "sofr": list[dict],
              "ndf":  list[dict],
              "tes":  list[dict],
            }

        Example:
            >>> mark = x.marks.all("2026-02-27")
            >>> mark["ibr"]["ibr_1d"]     # 9.636
            >>> len(mark["sofr"])          # 22 nodos SOFR
        """
        ibr_data  = self.ibr(fecha)
        sofr_data = self.sofr(fecha)
        ndf_data  = self.ndf(fecha)
        tes_data  = self.tes(fecha)

        return {
            "fecha": fecha,
            "ibr":   ibr_data,
            "sofr":  sofr_data,
            "ndf":   ndf_data,
            "tes":   tes_data,
            "has_ibr":  ibr_data is not None,
            "has_sofr": len(sofr_data) > 0,
            "has_ndf":  len(ndf_data) > 0,
            "has_tes":  len(tes_data) > 0,
        }
