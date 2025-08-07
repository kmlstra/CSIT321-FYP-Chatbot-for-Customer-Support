# Generated migration to remove KnowledgeBase model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_remove_chatbot_settings'),
    ]

    operations = [
        migrations.DeleteModel(
            name='KnowledgeBase',
        ),
    ]