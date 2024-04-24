from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase
from django.test.utils import override_settings

from django_state_manager.fsm import FSMField, transition, has_transition_perm


class ObjectPermissionTestModel(models.Model):
    state = FSMField(default="new")

    @transition(
        field=state,
        source="new",
        target="published",
        on_error="failed",
        permission="testapp.can_publish_objectpermissiontestmodel",
    )
    def publish(self):
        pass

    class Meta:
        app_label = "testapp"

        permissions = [
            (
                "can_publish_objectpermissiontestmodel",
                "Can publish ObjectPermissionTestModel",
            ),
        ]
