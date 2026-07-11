import uuid

from django.conf import settings
from django.db import models

from chat.llm.registry import model_choices
from core.models import TimeStampedModel


class ChatProfile(TimeStampedModel):
    """A reusable bundle of LLM settings a conversation runs under.

    A profile *selects* from the capabilities defined in code
    (``chat.llm.registry``): a supported model, optional temperature/reasoning
    knobs, a system prompt, and which implemented tools the LLM may use.

    Profiles are shared — every user can see and use any profile — but only the
    owner may edit or delete one. A ``null`` owner marks a global, code-seeded
    profile editable by staff.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_profiles',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    model_key = models.CharField(max_length=255, choices=model_choices)
    temperature = models.FloatField(null=True, blank=True)
    use_reasoning = models.BooleanField(default=False)
    system_prompt = models.TextField(blank=True)
    enabled_tools = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


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
    # Chosen when the conversation is created and immutable afterwards, so the
    # stored message history always reflects a single, consistent configuration.
    profile = models.ForeignKey(
        ChatProfile,
        on_delete=models.PROTECT,
        related_name='conversation_sessions',
    )
    title = models.CharField(max_length=255, default='New conversation')
    thread_id = models.UUIDField(unique=True, default=uuid.uuid7, editable=False)
    used = models.BooleanField(default=False)
    pending_message = models.TextField(null=True, default=None)

    class Meta:
        ordering = ['-modified']

    def __str__(self):
        return f'{self.title} ({self.user})'
