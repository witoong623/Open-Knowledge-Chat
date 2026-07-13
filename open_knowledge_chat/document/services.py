"""Document ingestion pipeline.

Reads an uploaded file, splits it into chunks, embeds the chunks with OpenAI,
and stores the embeddings in a pgvector-backed vector store.
"""

import atexit
import logging

from django.conf import settings
from langchain.chat_models import init_chat_model
from langchain_core.documents import Document as LangchainDocument
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from sqlalchemy import create_engine

from document.models import Document


logger = logging.getLogger(__name__)

# File types handled by the current pipeline.
SUPPORTED_EXTENSIONS = ('txt', 'md', 'pdf')

SQLALCHEMY_ENGINE = create_engine(settings.VECTOR_DB_URL)


def get_vector_store():
    """Return the pgvector store, creating the extension/tables on first use."""
    embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
    # TODO: should I maintain sqlalchemy's engine outside of PGVector?
    return PGVector(
        embeddings=embeddings,
        connection=SQLALCHEMY_ENGINE,
        collection_name=settings.VECTOR_COLLECTION_NAME,
        use_jsonb=True,
    )


def _read_text(document):
    """Return the decoded text content of a plain-text document."""
    with document.file.open('r') as fh:
        return fh.read()


def _load_documents(document):
    """Return the content of a document as a list of langchain ``Document`` objects."""
    if document.extension == 'pdf':
        loader = OpenDataLoaderPDFLoader(file_path=document.file.path, format='markdown')
        return loader.load()

    return [LangchainDocument(page_content=_read_text(document))]


class _ExtractedTitle(BaseModel):
    """Structured result of extracting a title from a document's opening text."""

    title: str = Field(
        description=(
            "The document's title if one is clearly present in the text (e.g. a book "
            "or paper title, or a top-level heading). Empty string if no clear title "
            'is present.'
        ),
    )


def _extract_title(text):
    """Use an LLM to extract a document title from its opening text.

    Returns the extracted title, or ``None`` when no clear title can be found
    (e.g. a plain notes file). The caller falls back to the filename in that case.
    """
    model = init_chat_model(settings.TITLE_EXTRACTION_MODEL).with_structured_output(_ExtractedTitle)
    result = model.invoke(
        'You are given the opening text of a document. Extract its title if one is clearly '
        'present. If there is no clear title, respond with an empty string — do not invent or '
        f'guess a title.\n\nOpening text:\n{text}'
    )
    return result.title.strip() or None


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

        docs = _load_documents(document)
        for doc in docs:
            doc.metadata.update({'document_id': document.id, 'name': document.name, 'user_id': document.user_id})

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        if chunks:
            # Extract a title from the first chunk; leave blank so display falls
            # back to the filename when the document has no clear title.
            title = _extract_title(chunks[0].page_content)
            if title:
                document.title = title
            get_vector_store().add_documents(chunks)

        document.ingestion_status = Document.IngestionStatus.COMPLETED
    except Exception:
        logger.exception('Failed to ingest document %s', document_id)
        document.ingestion_status = Document.IngestionStatus.FAILED

    document.save(update_fields=['title', 'ingestion_status', 'modified'])
    return document.ingestion_status


@tool
def search_knowledge_base(query: str, config: RunnableConfig) -> str:
    """Search the user's uploaded documents for content relevant to the query.

    Use this to find information from documents the user has uploaded before answering
    questions about their knowledge base.
    """
    user_id = config['configurable']['user_id']
    results = get_vector_store().similarity_search(query, k=3, filter={'user_id': user_id})

    if not results:
        return 'No relevant documents found.'

    return '\n\n'.join(f'Source: {doc.metadata.get("name", "unknown")}\n{doc.page_content}' for doc in results)


atexit.register(SQLALCHEMY_ENGINE.dispose)
