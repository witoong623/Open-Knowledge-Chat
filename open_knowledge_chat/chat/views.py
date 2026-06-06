from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View
from django_htmx.http import HttpResponseClientRedirect

from chat.models import ConversationSession
from chat.services import generate_reply


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
        })


class NewSessionView(LoginRequiredMixin, View):
    """Create a fresh conversation session and switch to it."""

    def post(self, request):
        session = ConversationSession.objects.create(user=request.user)
        url = f"{reverse('chat:index')}?session={session.pk}"
        return HttpResponseClientRedirect(url)


class SendMessageView(LoginRequiredMixin, View):
    """Handle a posted message and return the user + AI message bubbles."""

    def post(self, request, pk):
        session = get_object_or_404(ConversationSession, pk=pk, user=request.user)
        message = request.POST.get('message', '').strip()
        if not message:
            return HttpResponse(status=204)

        reply = generate_reply(message)

        # Name the session after its first message while it still has the default title.
        if session.title == 'New conversation':
            session.title = message[:50]
        session.save()

        return render(request, 'chat/partials/messages.html', {
            'user_message': message,
            'ai_reply': reply,
        })
