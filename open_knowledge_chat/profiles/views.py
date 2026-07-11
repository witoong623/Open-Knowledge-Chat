from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from chat.llm.registry import MODELS
from profiles.forms import ChatProfileForm
from profiles.models import ChatProfile


class ProfileListView(LoginRequiredMixin, ListView):
    """List all shared profiles; the template gates edit/delete to those the user owns."""

    model = ChatProfile
    template_name = 'profiles/list.html'
    context_object_name = 'profiles'


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """Read-only view of a single profile."""

    model = ChatProfile
    template_name = 'profiles/detail.html'
    context_object_name = 'profile'


class OwnerEditableMixin:
    """Restrict edit/delete to a profile's owner; staff may also edit global ones."""

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ChatProfile.objects.filter(Q(owner=user) | Q(owner__isnull=True))
        return ChatProfile.objects.filter(owner=user)


class ProfileFormContextMixin:
    """Expose each model's capability flags so the form can show/hide knobs client-side."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_specs'] = {
            key: {'temperature': spec.supports_temperature, 'reasoning': spec.supports_reasoning}
            for key, spec in MODELS.items()
        }
        return context


class ProfileCreateView(ProfileFormContextMixin, LoginRequiredMixin, CreateView):
    """Create a profile owned by the current user."""

    model = ChatProfile
    form_class = ChatProfileForm
    template_name = 'profiles/form.html'
    success_url = reverse_lazy('profiles:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProfileUpdateView(ProfileFormContextMixin, OwnerEditableMixin, LoginRequiredMixin, UpdateView):
    """Edit a profile the user is allowed to edit."""

    form_class = ChatProfileForm
    template_name = 'profiles/form.html'
    success_url = reverse_lazy('profiles:list')


class ProfileDeleteView(OwnerEditableMixin, LoginRequiredMixin, DeleteView):
    """Delete a profile the user owns (PROTECT blocks deleting one still in use)."""

    template_name = 'profiles/confirm_delete.html'
    success_url = reverse_lazy('profiles:list')

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            return self.render_to_response(self.get_context_data(
                error='This profile is used by an existing conversation and cannot be deleted.',
            ))
