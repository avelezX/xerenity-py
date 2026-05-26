import os
import uuid
from pathlib import Path

from supabase import create_client, Client
from supabase.client import ClientOptions


CLIENT_ID_HEADER = "x-xerenity-client-id"


def _get_or_create_client_id() -> str:
    """Return a stable per-install client UUID for SDK telemetry / rate-limit.

    Resolution order:
      1. ``XERENITY_CLIENT_ID`` env var (CI/test override).
      2. ``~/.xerenity/client_id`` file (persisted across runs).
      3. Newly generated UUID, persisted to step 2 if writable, otherwise
         used in-memory for this session only.

    The client_id is sent on every request as the ``x-xerenity-client-id``
    header. The Xerenity engine (xerenity-db) uses it as the bucket key for
    the ``sdk_public`` rate-limit (see DESIGN_DATA_ACCESS.md §3.8). For
    authenticated users it serves as SDK install telemetry — anonymising
    the user across sessions while still distinguishing distinct installs.
    """
    env_override = os.environ.get("XERENITY_CLIENT_ID")
    if env_override:
        return env_override.strip()

    config_dir = Path.home() / ".xerenity"
    client_id_file = config_dir / "client_id"

    try:
        if client_id_file.exists():
            existing = client_id_file.read_text().strip()
            if existing:
                return existing
    except OSError:
        # Fall through to generation if we can't read for any reason.
        pass

    new_id = str(uuid.uuid4())
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        client_id_file.write_text(new_id)
    except OSError:
        # Read-only filesystem (some containers/CI) — use the UUID for this
        # session only, it just won't survive process restarts.
        pass
    return new_id


class Connection:

    def __init__(self):
        url: str = "https://tvpehjbqxpiswkqszwwv.supabase.co"
        key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR2cGVoamJxeHBpc3drcXN6d3d2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTY0NTEzODksImV4cCI6MjAxMjAyNzM4OX0.LZW0i9HU81lCdyjAdqjwwF4hkuSVtsJsSDQh7blzozw"
        self.client_id: str = _get_or_create_client_id()
        self.supabase: Client = create_client(
            url, key,
            options=ClientOptions(
                auto_refresh_token=False,
                postgrest_client_timeout=40,
                storage_client_timeout=40,
                schema="xerenity",
                headers={CLIENT_ID_HEADER: self.client_id},
            ))

    def login(self, username, password):
        """

        Inicia sesion con el servidor de xerenity

        :param username: Usuario
        :param password: contrasena
        :return:
        """
        try:
            data = self.supabase.auth.sign_in_with_password(
                {
                    "email": username,
                    "password": password}
            )
            return data

        except Exception as er:
            return str(er)

    def get_all_series(self):
        """

        :return:
        """
        try:
            data = self.supabase.from_('search_mv').select(
                'source_name,grupo,sub_group,description,display_name,ticker').execute().data
            return data
        except Exception as er:
            return str(er)

    def read_serie(self, ticker: str):
        """

        Funcion que retorna los valores de la serie deseada, si la serie no es encontrada
        se retorna un contenedor vacio

        :param ticker: Identificador unico de la serie a leer
        :return:
        """
        try:
            data = self.supabase.rpc('search', {"ticket": ticker}).execute().data
            if 'data' in data:
                return data['data']
            return data
        except Exception as er:
            return str(er)

    def call_rpc(self, rpc_name, rpc_body: dict):
        return self.supabase.rpc(rpc_name, rpc_body).execute().data

    def list_loans(self, bank_names: list = None):
        """
        Lee la lista entera de creditos en xerenity
        :return:
        """
        try:

            loans_list = self.call_rpc('get_loans', {
                "bank_name_filter": bank_names
            })

            return loans_list

        except Exception as er:
            return str(er)

    def create_loan(self,
                    start_date: str,
                    bank: str,
                    number_of_payments: int,
                    original_balance: float,
                    periodicity: str,
                    interest_rate: float,
                    type: str,
                    days_count: str = None,
                    grace_type: str = None,
                    grace_period: int = None,
                    min_period_rate: float = None,
                    loan_identifier: str = None,
                    ):

        try:

            return self.supabase.rpc('create_credit', {
                "start_date": start_date,
                "bank": bank,
                "number_of_payments": number_of_payments,
                "original_balance": original_balance,
                "periodicity": periodicity,
                "interest_rate": interest_rate,
                "type": type,
                "days_count": days_count,
                "grace_type": grace_type,
                "grace_period": grace_period,
                "min_period_rate": min_period_rate,
                "loan_identifier": loan_identifier,
            }).execute().data

        except Exception as er:
            return str(er)
