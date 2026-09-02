"""
Shared Kernel Package
Contains base classes for CQRS pattern and event-driven architecture.
"""
from .bus import CommandBus, EventBus, Mediator, QueryBus
from .commands import Command, CommandHandler
from .events import DomainEvent, EventHandler
from .handlers import HandlerRegistry
from .queries import Query, QueryHandler

__all__ = [
    "Command",
    "CommandHandler",
    "DomainEvent",
    "EventHandler",
    "Query",
    "QueryHandler",
    "Mediator",
    "CommandBus",
    "QueryBus",
    "EventBus",
    "HandlerRegistry",
]
