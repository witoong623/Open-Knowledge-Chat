from django.db import migrations

# Global (owner=null) profiles seeded so the app is usable with zero setup.
# Keyed by name; reversing the migration removes exactly these.
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


def create_default_profiles(apps, schema_editor):
    ChatProfile = apps.get_model('chat', 'ChatProfile')
    for profile in DEFAULT_PROFILES:
        ChatProfile.objects.get_or_create(name=profile['name'], owner=None, defaults=profile)


def remove_default_profiles(apps, schema_editor):
    ChatProfile = apps.get_model('chat', 'ChatProfile')
    names = [profile['name'] for profile in DEFAULT_PROFILES]
    ChatProfile.objects.filter(owner=None, name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_chatprofile_conversationsession_profile'),
    ]

    operations = [
        migrations.RunPython(create_default_profiles, remove_default_profiles),
    ]
