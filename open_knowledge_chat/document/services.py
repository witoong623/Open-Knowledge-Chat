"""Document ingestion pipeline.

Reads an uploaded file, splits it into chunks, embeds the chunks with OpenAI,
and stores the embeddings in a pgvector-backed vector store.
"""

import logging

from django.conf import settings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from document.models import Document

logger = logging.getLogger(__name__)

# Plain-text formats handled by the current pipeline.
SUPPORTED_EXTENSIONS = ('txt', 'md')


def get_vector_store():
    """Return the pgvector store, creating the extension/tables on first use."""
    embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
    # TODO: should I maintain sqlalchemy's engine outside of PGVector?
    return PGVector(
        embeddings=embeddings,
        connection=settings.VECTOR_DB_URL,
        collection_name=settings.VECTOR_COLLECTION_NAME,
        use_jsonb=True,
    )


def _read_text(document):
    """Return the decoded text content of a plain-text document."""
    with document.file.open('r') as fh:
        return fh.read()


def ingest_file_document(document_id):
    """Ingest a document into the knowledge base, tracking status on the model.

    Marks the document as ``INGESTING`` while it runs, ``COMPLETED`` on success
    and ``FAILED`` if anything goes wrong.
    """
    document = Document.objects.get(pk=document_id)
    document.ingestion_status = Document.IngestionStatus.INGESTING
    document.save(update_fields=['ingestion_status', 'modified'])

    try:
        if document.extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(f'Unsupported file type for ingestion: {document.extension}')

        text = _read_text(document)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.create_documents(
            [text],
            metadatas=[{'document_id': document.id, 'name': document.name, 'user_id': document.user_id}],
        )

        if chunks:
            get_vector_store().add_documents(chunks)

        document.ingestion_status = Document.IngestionStatus.COMPLETED
    except Exception:
        logger.exception('Failed to ingest document %s', document_id)
        document.ingestion_status = Document.IngestionStatus.FAILED

    document.save(update_fields=['ingestion_status', 'modified'])
    return document.ingestion_status
