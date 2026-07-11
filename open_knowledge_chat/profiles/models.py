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
        # Retain the original table (this model previously lived in the ``chat``
        # app) so moving it here needs no data migration.
        db_table = 'chat_chatprofile'

    def __str__(self):
        return self.name
