import mimetypes

from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from document.forms import DocumentUploadForm, WebsiteURLForm
from document.models import Document
from document.tasks import ingest_document


@login_required
@require_http_methods(['GET'])
def index(request):
    """Render the document knowledge base page with the upload form and document list."""
    return render(request, 'document/index.html', {
        'documents': request.user.documents.all(),
        'form': DocumentUploadForm(),
        'website_form': WebsiteURLForm(),
    })


@login_required
@require_http_methods(['POST'])
def upload(request):
    """Handle a document upload and return the refreshed document section."""
    form = DocumentUploadForm(request.POST, request.FILES)
    if form.is_valid():
        document = form.save(commit=False)
        document.user = request.user
        document.name = document.file.name
        document.ingestion_status = Document.IngestionStatus.INGESTING
        document.save()
        ingest_document.delay_on_commit(document.id)
        form = DocumentUploadForm()

    return render(request, 'document/index.html#document-section', {
        'documents': request.user.documents.all(),
        'form': form,
        'website_form': WebsiteURLForm(),
    })


@login_required
@require_http_methods(['POST'])
def upload_website(request):
    """Handle a website URL submission and return the refreshed document section."""
    website_form = WebsiteURLForm(request.POST)
    if website_form.is_valid():
        document = website_form.save(commit=False)
        document.user = request.user
        document.source_type = Document.SourceType.WEBSITE
        document.name = document.url
        document.ingestion_status = Document.IngestionStatus.INGESTING
        document.save()
        ingest_document.delay_on_commit(document.id)
        website_form = WebsiteURLForm()

    return render(request, 'document/index.html#document-section', {
        'documents': request.user.documents.all(),
        'form': DocumentUploadForm(),
        'website_form': website_form,
    })


@login_required
@require_http_methods(['DELETE'])
def delete(request, pk):
    """Delete an uploaded document and return the refreshed document section."""
    document = get_object_or_404(Document, pk=pk, user=request.user)
    document.file.delete(save=False)
    document.delete()

    return render(request, 'document/index.html#document-section', {
        'documents': request.user.documents.all(),
        'form': DocumentUploadForm(),
        'website_form': WebsiteURLForm(),
    })


@login_required
@require_http_methods(['GET'])
def status(request, pk):
    """Return the ingestion status badge for a document (polled while ingesting)."""
    document = get_object_or_404(Document, pk=pk, user=request.user)
    return render(request, 'document/index.html#document-status', {'document': document})


@login_required
@require_http_methods(['GET'])
def preview(request, pk):
    """Stream an uploaded document back for inline preview in the browser."""
    document = get_object_or_404(Document, pk=pk, user=request.user)

    content_type, _ = mimetypes.guess_type(document.name)
    if content_type is None:
        content_type = 'text/plain' if document.extension in ('txt', 'md') else 'application/octet-stream'

    return FileResponse(document.file.open('rb'), filename=document.name, content_type=content_type)
