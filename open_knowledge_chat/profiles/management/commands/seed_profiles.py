from django.core.management.base import BaseCommand

from profiles.models import ChatProfile

# Global (owner=null) profiles seeded so the app is usable with zero setup.
# Kept out of migrations on purpose: run ``manage.py seed_profiles`` after a
# fresh ``migrate`` (or DB reset) instead of baking the data into a migration.
# Keyed by name, so re-running only creates what is missing.
DEFAULT_PROFILES = [
    {
        'name': 'Knowledge Base Q&A',
        'model_key': 'openai:gpt-5.4-mini',
        'temperature': None,
        'use_reasoning': False,
        'system_prompt': (
            'You are a helpful assistant. Answer questions using the knowledge base. '
            'Search it when a question may be covered by ingested documents, and ground '
            'your answers in what you find.'
        ),
        'enabled_tools': ['search_knowledge_base'],
    },
    {
        'name': 'Plain Chat',
        'model_key': 'openai:gpt-5.4-mini',
        'temperature': None,
        'use_reasoning': False,
        'system_prompt': 'You are a helpful assistant.',
        'enabled_tools': [],
    },
]


class Command(BaseCommand):
    help = 'Seed the default global chat profiles. Idempotent — safe to re-run.'

    def handle(self, *args, **options):
        created = 0
        for profile in DEFAULT_PROFILES:
            _, was_created = ChatProfile.objects.get_or_create(
                name=profile['name'], owner=None, defaults=profile,
            )
            created += was_created
        existing = len(DEFAULT_PROFILES) - created
        self.stdout.write(self.style.SUCCESS(
            f'Seeded default profiles ({created} created, {existing} already present).'
        ))
