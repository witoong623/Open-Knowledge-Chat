"""AI response generation.

This is the single seam for the chat's AI backend.
"""

import atexit

from django.conf import settings
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from document.services import search_knowledge_base

# A pooled connection lets the checkpointer be shared safely across concurrent requests.
_pool = ConnectionPool(
    conninfo=settings.LANGCHAIN_DB_URI,
    kwargs={'autocommit': True, 'prepare_threshold': 0, 'row_factory': dict_row},
    open=True,
)
checkpointer = PostgresSaver(_pool)
agent = create_agent('openai:gpt-5.4-mini', tools=[search_knowledge_base], checkpointer=checkpointer)

# Human-friendly progress labels shown while a tool runs, keyed by tool name.
TOOL_LABELS = {
    'search_knowledge_base': 'Searching knowledge base…',
}

# Past-tense labels for the collapsed tool pill once the call has finished.
TOOL_RESULT_LABELS = {
    'search_knowledge_base': 'Searched knowledge base',
}


def get_message_history(thread_id):
    """Return the messages exchanged so far on ``thread_id``, oldest first."""
    config = {'configurable': {'thread_id': str(thread_id)}}
    return agent.get_state(config).values.get('messages', [])


def build_chat_log(messages):
    """Transform raw LangChain messages into ordered view models for rendering.

    Produces user/assistant bubbles, and folds each tool call together with its
    result into a single collapsible ``tool`` group, so raw tool output and the
    empty tool-call AI messages never render as chat bubbles.
    """
    log = []
    calls_by_id = {}
    for message in messages:
        if message.type == 'human':
            log.append({'role': 'user', 'content': message.content})
        elif message.type == 'tool':
            entry = calls_by_id.get(message.tool_call_id)
            if entry is not None:
                entry['result'] = message.content
        elif message.type == 'ai':
            tool_calls = getattr(message, 'tool_calls', None)
            if tool_calls:
                calls = []
                for call in tool_calls:
                    entry = {
                        'label': TOOL_RESULT_LABELS.get(call['name'], call['name']),
                        'query': call.get('args', {}).get('query', ''),
                        'result': '',
                    }
                    calls.append(entry)
                    calls_by_id[call['id']] = entry
                log.append({'role': 'tool', 'calls': calls})
            if message.content:
                log.append({'role': 'assistant', 'content': message.content})
    return log


def generate_reply_stream(message, thread_id, user_id):
    """Yield ``(event, data)`` pairs for the AI's reply as it's produced.

    Emits ``ai-chunk`` events for assistant text and ``tool`` events announcing
    a tool invocation. Raw tool output is never streamed to the chat; it's
    available on reload inside the collapsible tool group built by
    ``build_chat_log``.
    """
    config = {'configurable': {'thread_id': str(thread_id), 'user_id': user_id}}
    announced_tools = set()
    for chunk, _metadata in agent.stream(
        {'messages': [HumanMessage(message)]},
        config=config,
        stream_mode='messages',
    ):
        if chunk.type == 'tool':
            continue
        for call in getattr(chunk, 'tool_call_chunks', None) or []:
            name = call.get('name')
            # Only announce each tool once per reply, even if it produces multiple chunks.
            if name and name not in announced_tools:
                announced_tools.add(name)
                yield 'tool', TOOL_LABELS.get(name, f'Using {name}…')
        if chunk.content:
            yield 'ai-chunk', chunk.content


# Close the pool on normal interpreter shutdown (e.g. Ctrl+C / SIGINT) so that
# ConnectionPool.__del__ doesn't try to join its worker threads during finalization,
# which raises PythonFinalizationError on Python 3.13+.
atexit.register(_pool.close)
