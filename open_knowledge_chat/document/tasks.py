from celery import shared_task

from document.services import ingest_file_document


@shared_task
def ingest_document(document_id):
    """Background task that ingests an uploaded document into the knowledge base."""
    return ingest_file_document(document_id)
