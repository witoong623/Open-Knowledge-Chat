"""AI response generation.

This is the single seam for the chat's AI backend.
"""

import signal

from django.conf import settings
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# A pooled connection lets the checkpointer be shared safely across concurrent requests.
_pool = ConnectionPool(
    conninfo=settings.LANGCHAIN_DB_URI,
    kwargs={'autocommit': True, 'prepare_threshold': 0, 'row_factory': dict_row},
    open=True,
)
checkpointer = PostgresSaver(_pool)
agent = create_agent('openai:gpt-5.4-mini', tools=[], checkpointer=checkpointer)


def generate_reply_stream(message, thread_id):
    """Yield the AI's reply to a user ``message`` in chunks as they're produced."""
    config = {'configurable': {'thread_id': str(thread_id)}}
    for chunk, _metadata in agent.stream(
        {'messages': [HumanMessage(message)]},
        config=config,
        stream_mode='messages',
    ):
        if chunk.content:
            yield chunk.content


def close_pool_on_sigterm(*args):
    """Close the connection pool on SIGTERM so that the process can exit gracefully."""
    _pool.close()


# Register the SIGTERM handler to close the pool gracefully.
signal.signal(signal.SIGTERM, close_pool_on_sigterm)
