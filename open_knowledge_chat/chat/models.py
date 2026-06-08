import uuid

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class ConversationSession(TimeStampedModel):
    """A single chat conversation belonging to a user.

    Messages are not persisted yet; this model is the per-user seam for adding
    stored messages later.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_sessions',
    )
    title = models.CharField(max_length=255, default='New conversation')
    thread_id = models.UUIDField(unique=True, default=uuid.uuid7, editable=False)

    class Meta:
        ordering = ['-modified']

    def __str__(self):
        return f'{self.title} ({self.user})'
