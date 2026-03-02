from xerenity.catalog import CATALOG


class Series:

    def __init__(self, connection):
        self.sup = connection

    def portfolio(self):
        """
        Retorna el portafolio completo de series disponibles en Xerenity.

        :return: [{'source_name': str, 'grupo': str, 'sub_group': str,
                   'description': str, 'display_name': str, 'ticker': str}]
        """
        return self.sup.get_all_series()

    def search(self, ticker: str) -> list:
        """
        Dado el ticker de una serie, retorna sus valores históricos.
        Para obtener el ticker usa find(), el CATALOG, o la función portfolio().

        :param ticker: Identificador único (MD5) de la serie
        :return: [{"time": "YYYY-MM-DD", "value": float}]
        """
        return self.sup.read_serie(ticker=ticker)

    def find(self, query: str) -> list[dict]:
        """
        Busca series por nombre parcial en el catálogo estático (sin llamada API).

        :param query: Texto parcial a buscar en el nombre de la serie
        :return: [{"display_name": str, "ticker": str, "grupo": str, "sub_group": str}]

        Ejemplo:
            resultados = x.series.find("PIB")
            resultados = x.series.find("IBR")
            resultados = x.series.find("Consumo final")
        """
        q = query.lower()
        return [
            {"display_name": name, "ticker": ticker, "grupo": grupo, "sub_group": sub}
            for grupo, subgroups in CATALOG.items()
            for sub, series in subgroups.items()
            for name, ticker in series.items()
            if q in name.lower()
        ]

    def get(self, display_name: str) -> list:
        """
        Trae los datos de una serie por su nombre exacto (resuelve el ticker internamente).
        Equivalente a search(CATALOG[grupo][sub_group][display_name]).

        :param display_name: Nombre exacto de la serie (ver CATALOG o find())
        :return: [{"time": "YYYY-MM-DD", "value": float}]

        Ejemplo:
            data = x.series.get("Consumo final, nominal")
            data = x.series.get("Tasa de política monetaria")
        """
        ticker = self._ticker_for(display_name)
        if not ticker:
            return []
        return self.search(ticker)

    def _ticker_for(self, display_name: str) -> str | None:
        """Busca el ticker en el catálogo estático por nombre exacto."""
        for subgroups in CATALOG.values():
            for series in subgroups.values():
                if display_name in series:
                    return series[display_name]
        return None
