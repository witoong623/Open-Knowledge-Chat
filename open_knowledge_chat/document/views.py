from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DocumentIndexView(LoginRequiredMixin, TemplateView):
    """Render the (currently empty) document knowledge base page."""

    template_name = 'document/index.html'
