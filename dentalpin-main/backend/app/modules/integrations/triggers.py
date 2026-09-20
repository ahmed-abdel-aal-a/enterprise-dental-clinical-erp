"""Event types and API token scopes this module actually supports.

Phase 1 ships two working triggers end-to-end (issue #65). Almost
every other event issue #65 §3 wants already exists on the bus
(``core/events/types.py``) — adding it here means only "declare a new
transactional handler in handlers.py", no new bus infra. Keeping this
list separate from ``EventType`` (which has ~60 events, most
irrelevant to webhooks) is what lets ``WebhookSubscriptionCreate``
reject a subscription for an event nobody will ever deliver, instead
of silently accepting one that never fires.

``SUPPORTED_TOKEN_SCOPES`` is the same idea for API tokens: no
consumer endpoint checks scopes yet (the public data-read API is
follow-up scope), but validating against a closed catalog now means
we never have to migrate free-text scopes later once one exists.
"""

from app.core.events import EventType

SUPPORTED_EVENT_TYPES: frozenset[str] = frozenset(
    {EventType.PATIENT_CREATED, EventType.APPOINTMENT_COMPLETED}
)

SUPPORTED_TOKEN_SCOPES: frozenset[str] = frozenset({"patients:read"})
