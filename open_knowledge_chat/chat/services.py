"""AI response generation.

This is the single seam for the chat's AI backend. For now it yields a stub
reply in chunks; swap the body of ``generate_reply_stream`` to stream from a
real LLM later.
"""


def generate_reply_stream(message: str):
    """Yield the AI's reply to a user ``message`` in chunks as they're produced."""
    reply = f'You said: "{message}". (This is a stub AI response.)'
    for word in reply.split(' '):
        yield f'{word} '
