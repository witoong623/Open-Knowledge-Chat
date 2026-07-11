"""Capabilities layer for chat profiles.

The set of LLM models and tools a profile may compose is fixed in code: each
model is tied to an installed langchain provider package, and each tool is a
Python implementation. Profiles (stored in the database) merely *select* from
these registries, so this module is the single source of truth for what the
backend can actually support.
"""

from collections.abc import Callable
from dataclasses import dataclass

from document.services import search_knowledge_base


@dataclass(frozen=True)
class ModelSpec:
    """A supported LLM, keyed in ``MODELS`` by an arbitrary registry slug.

    ``model_id`` is the langchain ``provider:model`` identifier passed to
    ``init_chat_model``.

    The capability flags drive form validation and which knobs the profile UI
    exposes — e.g. reasoning models typically reject a ``temperature``.
    """
    model_id: str
    label: str
    supports_temperature: bool = False
    supports_reasoning: bool = False


# Supported models, keyed by an arbitrary registry slug (stored as a profile's
# ``model_key``). Each entry's ``model_id`` is the langchain ``provider:model``
# identifier; its provider package must be installed (see pyproject.toml).
MODELS: dict[str, ModelSpec] = {
    'gpt-5.4-mini': ModelSpec(
        model_id='openai:gpt-5.4-mini', label='GPT-5.4 Mini', supports_temperature=True,
    ),
    'gpt-5.4': ModelSpec(
        model_id='openai:gpt-5.4', label='GPT-5.4', supports_temperature=True,
    ),
    # The same model_id can back a reasoning variant. Reasoning models reject a
    # temperature; enable use_reasoning instead.
    'gpt-5.4-reasoning': ModelSpec(
        model_id='openai:gpt-5.4', label='GPT-5.4 (Reasoning)', supports_reasoning=True,
    ),
}


@dataclass(frozen=True)
class ToolSpec:
    """A tool a profile may enable, keyed in ``TOOL_REGISTRY`` by its tool key."""
    callable: Callable
    running_label: str  # present tense, shown while the tool runs
    done_label: str     # past tense, shown on the collapsed pill afterwards


# Implemented tools, keyed by the langchain tool name (``tool.name``), so a
# profile's ``enabled_tools`` list resolves straight to callables and the chat
# stream can look up progress labels by the name langchain reports.
TOOL_REGISTRY: dict[str, ToolSpec] = {
    'search_knowledge_base': ToolSpec(
        callable=search_knowledge_base,
        running_label='Searching knowledge base…',
        done_label='Searched knowledge base',
    ),
}


def model_choices() -> list[tuple[str, str]]:
    """``(value, label)`` pairs for a model ``choices`` field."""
    return [(key, spec.label) for key, spec in MODELS.items()]


def tool_choices() -> list[tuple[str, str]]:
    """``(value, label)`` pairs for rendering the per-profile tool checkboxes."""
    return [(key, spec.done_label) for key, spec in TOOL_REGISTRY.items()]
