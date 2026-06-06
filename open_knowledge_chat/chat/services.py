"""AI response generation.

This is the single seam for the chat's AI backend. For now it returns a stub
reply; swap the body of ``generate_reply`` to call a real LLM later.
"""


def generate_reply(message: str) -> str:
    """Return the AI's reply to a user ``message``."""
    return f'You said: "{message}". (This is a stub AI response.)'
