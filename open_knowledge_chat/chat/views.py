from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.http import require_http_methods

from chat.models import ConversationSession
from chat.services import build_chat_log, generate_reply_stream, get_message_history
from profiles.models import ChatProfile


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
