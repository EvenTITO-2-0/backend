from pydantic import BaseModel
from datetime import datetime

class AssignWorksParametersSchema(BaseModel):
    """
    Schema for parameters to assign works to slots in an event.
    """
    time_per_work: int
    reset_previous_assignments: bool

    class Config:
        # Allows creating the schema from ORM models or dicts
        from_attributes = True