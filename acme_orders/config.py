from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./acme_orders.db"
    app_name: str = "AcmeOrders"


def get_settings() -> Settings:
    return Settings(database_url=os.getenv("ACME_DATABASE_URL", Settings.database_url))
