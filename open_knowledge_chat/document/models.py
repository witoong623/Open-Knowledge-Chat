from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from core.models import TimeStampedModel

ALLOWED_EXTENSIONS = ['txt', 'md', 'pdf']


def document_upload_path(instance, filename):
    return f'documents/{instance.user_id}/{filename}'


class Document(TimeStampedModel):
    """An uploaded file that can be ingested into the knowledge base."""

    class IngestionStatus(models.TextChoices):
        NOT_INGESTED = 'not_ingested', 'Not ingested'
        INGESTING = 'ingesting', 'Ingesting'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, help_text='Document title')
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)],
    )
    ingestion_status = models.CharField(
        max_length=20,
        choices=IngestionStatus.choices,
        default=IngestionStatus.NOT_INGESTED,
    )

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name

    @property
    def extension(self):
        return self.name.rsplit('.', 1)[-1].lower()

    @property
    def display_title(self):
        """Title to show in the UI, falling back to the filename when unset."""
        return self.title or self.name
