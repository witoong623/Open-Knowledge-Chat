import django.db.models.deletion
from django.db import migrations, models

# The default global profile existing sessions are attached to during backfill.
BACKFILL_PROFILE_NAME = 'Knowledge Base Q&A'


def backfill_session_profiles(apps, schema_editor):
    ChatProfile = apps.get_model('chat', 'ChatProfile')
    ConversationSession = apps.get_model('chat', 'ConversationSession')
    profile = ChatProfile.objects.filter(owner=None, name=BACKFILL_PROFILE_NAME).first()
    if profile is None:
        profile = ChatProfile.objects.filter(owner=None).first()
    if profile is not None:
        ConversationSession.objects.filter(profile__isnull=True).update(profile=profile)


def noop_reverse(apps, schema_editor):
    # Re-widening the column (0005 reverse) is enough; leave the data in place.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_seed_default_profiles'),
    ]

    operations = [
        migrations.RunPython(backfill_session_profiles, noop_reverse),
        migrations.AlterField(
            model_name='conversationsession',
            name='profile',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='conversation_sessions',
                to='chat.chatprofile',
            ),
        ),
    ]
