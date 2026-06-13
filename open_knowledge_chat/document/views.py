import mimetypes

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import TemplateView

from document.forms import DocumentUploadForm
from document.models import Document


class DocumentIndexView(LoginRequiredMixin, TemplateView):
    """Render the document knowledge base page with the upload form and document list."""

    template_name = 'document/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.request.user.documents.all()
        context.setdefault('form', DocumentUploadForm())
        return context


class DocumentUploadView(LoginRequiredMixin, View):
    """Handle a document upload and return the refreshed document section."""

    def post(self, request):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.name = document.file.name
            document.save()
            form = DocumentUploadForm()

        return render(request, 'document/index.html#document-section', {
            'documents': request.user.documents.all(),
            'form': form,
        })


class DocumentDeleteView(LoginRequiredMixin, View):
    """Delete an uploaded document and return the refreshed document section."""

    def delete(self, request, pk):
        document = get_object_or_404(Document, pk=pk, user=request.user)
        document.file.delete(save=False)
        document.delete()

        return render(request, 'document/index.html#document-section', {
            'documents': request.user.documents.all(),
            'form': DocumentUploadForm(),
        })


class DocumentPreviewView(LoginRequiredMixin, View):
    """Stream an uploaded document back for inline preview in the browser."""

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk, user=request.user)

        content_type, _ = mimetypes.guess_type(document.name)
        if content_type is None:
            content_type = 'text/plain' if document.extension in ('txt', 'md') else 'application/octet-stream'

        return FileResponse(document.file.open('rb'), filename=document.name, content_type=content_type)
