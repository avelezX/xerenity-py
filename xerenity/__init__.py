"""
Xerenity python library
"""

__version__ = "0.4.0"
__author__ = 'Xerenity'

from xerenity.catalog import CATALOG
from xerenity.connection.db import Connection
from xerenity.search.series import Series
from xerenity.loans.loans import Loans
from xerenity.marks.marks import Marks
from xerenity.data.engine import DataEngine


class Xerenity:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.conn = Connection()
        self.conn.login(username=username, password=password)
        self.series: Series = Series(connection=self.conn)
        self.loans: Loans = Loans(connection=self.conn)
        self.marks: Marks = Marks(connection=self.conn)
        # Acceso canónico sobre el motor único (resolve_query / query_series).
        # Namespace nuevo, aditivo: no toca `series`/`marks` existentes.
        self.data: DataEngine = DataEngine(connection=self.conn)
