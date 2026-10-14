from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Immutable, and strict about keys: an unknown field is a mistake, not noise."""

    model_config = ConfigDict(frozen=True, extra="forbid")
