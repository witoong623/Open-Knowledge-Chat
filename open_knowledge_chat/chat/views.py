from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.views import View

from chat.models import ConversationSession
from chat.services import generate_reply_stream, get_message_history


def sse_event(name, data):
    """Format ``name``/``data`` as an SSE frame, splitting multi-line data across ``data:`` lines."""
    payload = ''.join(f'data: {line}\n' for line in (data.splitlines() or ['']))
    return f'event: {name}\n{payload}\n'


class ChatIndexView(LoginRequiredMixin, View):
    """Render the chat page for the user's active conversation session."""

    def get(self, request):
        sessions = request.user.conversation_sessions.all()

        active_session = None
        requested = request.GET.get('session')
        if requested:
            active_session = sessions.filter(pk=requested).first()
        if active_session is None:
            active_session = sessions.first()
        if active_session is None:
            active_session = ConversationSession.objects.create(user=request.user)
            sessions = request.user.conversation_sessions.all()

        return render(request, 'chat/index.html', {
            'sessions': sessions,
            'active_session': active_session,
            'chat_messages': get_message_history(active_session.thread_id),
        })


class NewSessionView(LoginRequiredMixin, View):
    """Create a fresh conversation session and switch to it."""

    def post(self, request):
        session = ConversationSession.objects.filter(user=request.user, used=False).first()
        if session is None:
            session = ConversationSession.objects.create(user=request.user)
        return redirect(f"{reverse('chat:index')}?session={session.pk}")


class SendMessageView(LoginRequiredMixin, View):
    """Handle a posted message and return a fragment that opens an SSE stream for the reply."""

    def post(self, request, pk):
        session = get_object_or_404(ConversationSession, pk=pk, user=request.user)
        message = request.POST.get('message', '').strip()
        if not message:
            return HttpResponse(status=204)

        # Name the session after its first message while it still has the default title.
        if session.title == 'New conversation':
            session.title = message[:50]
        session.used = True
        session.save()

        return render(request, 'chat/partials/stream_container.html', {
            'session': session,
            'message': message,
        })


class MessageStreamView(LoginRequiredMixin, View):
    """Stream the user message and AI reply to the client over SSE."""

    def get(self, request, pk):
        session = get_object_or_404(ConversationSession, pk=pk, user=request.user)
        message = request.GET.get('message', '').strip()
        if not message:
            return HttpResponse(status=204)

        def event_stream():
            for chunk in generate_reply_stream(message, session.thread_id):
                yield sse_event('ai-chunk', escape(chunk))
            yield sse_event('done', '')

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
