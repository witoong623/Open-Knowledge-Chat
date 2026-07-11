from django.db import migrations

# The registry key stored in ``model_key`` used to be the langchain
# ``provider:model`` identifier itself. It is now an arbitrary slug decoupled
# from that identifier, so remap any rows written under the old scheme.
KEY_MAP = {
    'openai:gpt-5.4-mini': 'gpt-5.4-mini',
    'openai:gpt-5.4': 'gpt-5.4',
}


def remap_forward(apps, schema_editor):
    ChatProfile = apps.get_model('profiles', 'ChatProfile')
    for old, new in KEY_MAP.items():
        ChatProfile.objects.filter(model_key=old).update(model_key=new)


def remap_backward(apps, schema_editor):
    ChatProfile = apps.get_model('profiles', 'ChatProfile')
    for old, new in KEY_MAP.items():
        ChatProfile.objects.filter(model_key=new).update(model_key=old)


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remap_forward, remap_backward),
    ]
