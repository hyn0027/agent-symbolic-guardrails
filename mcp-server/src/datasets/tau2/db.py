# Modified from TAU2 bench code.

from typing import Any
from pydantic import BaseModel, ConfigDict
from utils import load_json, dump_json


class DB(BaseModel):
    """Domain database.

    This is a base class for all domain databases.
    """

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def load(cls, path: str) -> "DB":
        """Load the database from a structured file like JSON, YAML, or TOML."""
        data = load_json(path)
        return cls.model_validate(data)

    def dump(self, path: str) -> None:
        """Dump the database to a structured file like JSON, YAML, or TOML."""
        dumped = self.model_dump()
        dump_json(dumped, path)

    def get_statistics(self) -> dict[str, Any]:
        """Get the statistics of the database."""
        return {}
