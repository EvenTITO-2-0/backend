from app.schemas.events.configuration_general import ConfigurationGeneralEventSchema
from app.schemas.events.event_status import EventStatusSchema
from app.schemas.events.review_skeleton.review_skeleton import ReviewSkeletonResponseSchema
from app.schemas.events.schemas import DynamicEventSchema, StaticEventSchema


class EventConfigurationSchema(
    ConfigurationGeneralEventSchema,
    DynamicEventSchema,
    StaticEventSchema,
    ReviewSkeletonResponseSchema,
    EventStatusSchema,
):
    pass
