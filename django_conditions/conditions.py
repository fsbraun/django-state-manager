import typing

from django.conf import settings

from .exceptions import ConditionFailed


class Conditions(list):
    def __add__(self, other: list) -> "Conditions":
        return Conditions(super().__add__(other))

    def __get__(self, instance: object, cls) -> typing.Union["Conditions", "BoundConditions"]:
        if instance:
            return BoundConditions(self, instance)
        return self

    def __call__(self, instance: object, user: settings.AUTH_USER_MODEL) -> None:
        for func in self:
            func(instance, user)

    def as_bool(self, instance: object, user: settings.AUTH_USER_MODEL) -> bool:
        try:
            self(instance, user)
        except ConditionFailed:
            return False
        return True


class BoundConditions:
    def __init__(self, conditions: Conditions, instance: object) -> None:
        self.conditions = conditions
        self.instance = instance

    def __call__(self, user) -> None:
        self.conditions(self.instance, user)

    def as_bool(self, user) -> bool:
        return self.conditions.as_bool(self.instance, user)
