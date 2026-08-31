from typing import Annotated

from pydantic import BaseModel, ConfigDict, StrictInt

PaiseField = Annotated[StrictInt, ...]


class CanonicalModel(BaseModel):
    model_config = ConfigDict(strict=True)
