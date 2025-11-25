
from pydantic import BaseModel


class AssignWorksParametersWeights(BaseModel):
    """
    Schema for weights used in assigning works to slots.
    """

    same_day_tracks: int
    same_room_tracks: int

    class Config:
        # Allows creating the schema from ORM models or dicts
        from_attributes = True


class AssignWorksParametersSchema(BaseModel):
    """
    Schema for parameters to assign works to slots in an event.
    """

    time_per_work: int
    reset_previous_assignments: bool
    weights: AssignWorksParametersWeights

    class Config:
        # Allows creating the schema from ORM models or dicts
        from_attributes = True
