from typing import Annotated

from pydantic import StringConstraints

UID = Annotated[str, StringConstraints(min_length=28, max_length=128, pattern=r"^[A-Za-z0-9]+$")]
