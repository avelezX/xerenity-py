"""
Marcas de mercado diarias — curvas de tasas por fecha.

Expone los datos almacenados en Supabase para cada sesión de mercado:
  - IBR: curva de tasas overnight colombiana (1d → 20y)
  - SOFR: curva OIS en USD (1m → 50y)
  - NDF: puntos forward COP/USD por tenor
  - TES: curva de rendimientos de TES soberanos colombianos

Uso:
    x = Xerenity(username, password)
    mark = x.marks.all("2026-02-27")
    ibr  = x.marks.ibr("2026-02-27")

Cada método devuelve un dict (o lista de dicts) listo para usar con pandas:
    import pandas as pd
    df = pd.DataFrame(x.marks.sofr("2026-02-27"))
"""

from supabase import create_client, Client
from supabase.client import ClientOptions


_SUPABASE_URL = "https://tvpehjbqxpiswkqszwwv.supabase.co"
_SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR2cGVoamJxeHBpc3drcXN6d3d2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTY0NTEzODksImV4cCI6MjAxMjAyNzM4OX0.LZW0i9HU81lCdyjAdqjwwF4hkuSVtsJsSDQh7blzozw"


class Marks:
    """
    Acceso a marcas diarias de mercado (curvas de tasas por fecha).

    Instanciado automáticamente por la clase Xerenity — no crear directamente.
    """

    def __init__(self, connection):
        self._conn = connection
        # Cliente adicional con schema=trading para TES
        self._trading = create_client(
            _SUPABASE_URL,
            _SUPABASE_ANON_KEY,
            options=ClientOptions(
                auto_refresh_token=False,
                postgrest_client_timeout=40,
                schema="trading",
            ),
        )

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
        return res.data

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
            # Fallback: query directa a trading.tes_operation si el RPC no existe
            res = (
                self._trading
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
