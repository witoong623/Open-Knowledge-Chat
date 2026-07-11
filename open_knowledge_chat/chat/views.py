from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError, Q
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.html import escape
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from chat.forms import ChatProfileForm
from chat.llm.registry import MODELS
from chat.models import ChatProfile, ConversationSession
from chat.services import build_chat_log, generate_reply_stream, get_message_history


def default_profile():
    """The profile new conversations fall back to: a global one, else any profile."""
    return ChatProfile.objects.filter(owner__isnull=True).first() or ChatProfile.objects.first()


def sse_event(name, data):
    """Format ``name``/``data`` as an SSE frame, splitting multi-line data across ``data:`` lines
    so embedded newlines survive and are reconstructed by the client.
    A raw '\n' in data would be read as an SSE line break, not content, and
    split the message early. Sending each line as its own `data:` field lets
    the client rejoin them with '\n' to recover the original text."""
    payload = ''.join(f'data: {line}\n' for line in data.split('\n'))
    return f'event: {name}\n{payload}\n'


@login_required
@require_http_methods(['GET'])
def chat_index(request):
    """Render the chat page for the user's active conversation session."""
    sessions = request.user.conversation_sessions.all()

    active_session = None
    requested = request.GET.get('session')
    if requested:
        active_session = sessions.filter(pk=requested).first()
    if active_session is None:
        active_session = sessions.first()
    if active_session is None:
        active_session = ConversationSession.objects.create(user=request.user, profile=default_profile())
        sessions = request.user.conversation_sessions.all()

    return render(request, 'chat/index.html', {
        'sessions': sessions,
        'active_session': active_session,
        'profiles': ChatProfile.objects.all(),
        'chat_messages': build_chat_log(
            get_message_history(active_session.profile, active_session.thread_id)
        ),
    })


@login_required
@require_http_methods(['GET'])
def message_log(request, pk):
    """Render the canonical message log for a session as an HTMX fragment.

    The SSE stream reloads this once a reply finishes so the optimistic
    streamed bubble is replaced by the same rendering used on page load.
    """
    session = get_object_or_404(ConversationSession, pk=pk, user=request.user)
    return render(request, 'chat/index.html#message-log', {
        'chat_messages': build_chat_log(get_message_history(session.profile, session.thread_id)),
    })


@login_required
@require_http_methods(['POST'])
def new_session(request):
    """Create a fresh conversation session and switch to it."""
    requested = request.POST.get('profile')
    profile = get_object_or_404(ChatProfile, pk=requested) if requested else default_profile()
    # Reuse an unused session only when it already runs the chosen profile,
    # since a session's profile is fixed once created.
    session = ConversationSession.objects.filter(user=request.user, used=False, profile=profile).first()
    if session is None:
        session = ConversationSession.objects.create(user=request.user, profile=profile)
    return redirect(f"{reverse('chat:index')}?session={session.pk}")


@login_required
@require_http_methods(['POST'])
def send_message(request, pk):
    """Handle a posted message and return a fragment that opens an SSE stream for the reply."""
    session = get_object_or_404(ConversationSession, pk=pk, user=request.user)
    message = request.POST.get('message', '').strip()
    if not message:
        return HttpResponse(status=204)

    # Name the session after its first message while it still has the default title.
    if session.title == 'New conversation':
        session.title = message[:50]
    session.used = True
    session.pending_message = message
    session.save()

    return render(request, 'chat/partials/stream_container.html', {
        'session': session,
        'message': message,
    })


@login_required
@require_http_methods(['GET'])
def message_stream(request, pk):
    """Stream the user message and AI reply to the client over SSE."""
    session = get_object_or_404(ConversationSession, pk=pk, user=request.user)
    message = session.pending_message
    if not message:
        return HttpResponse(status=204)

    session.pending_message = None
    session.save(update_fields=['pending_message', 'modified'])

    def event_stream():
        for event, data in generate_reply_stream(session.profile, message, session.thread_id, request.user.id):
            yield sse_event(event, escape(data))
        yield sse_event('done', '')

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


class ProfileListView(LoginRequiredMixin, ListView):
    """List all shared profiles; the template gates edit/delete to those the user owns."""

    model = ChatProfile
    template_name = 'chat/profiles/list.html'
    context_object_name = 'profiles'


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """Read-only view of a single profile."""

    model = ChatProfile
    template_name = 'chat/profiles/detail.html'
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
    template_name = 'chat/profiles/form.html'
    success_url = reverse_lazy('chat:profiles')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProfileUpdateView(ProfileFormContextMixin, OwnerEditableMixin, LoginRequiredMixin, UpdateView):
    """Edit a profile the user is allowed to edit."""

    form_class = ChatProfileForm
    template_name = 'chat/profiles/form.html'
    success_url = reverse_lazy('chat:profiles')


class ProfileDeleteView(OwnerEditableMixin, LoginRequiredMixin, DeleteView):
    """Delete a profile the user owns (PROTECT blocks deleting one still in use)."""

    template_name = 'chat/profiles/confirm_delete.html'
    success_url = reverse_lazy('chat:profiles')

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            return self.render_to_response(self.get_context_data(
                error='This profile is used by an existing conversation and cannot be deleted.',
            ))
