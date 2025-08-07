# Generated migration to remove ChatbotSettings model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_newslettersubscription_alter_knowledgebase_options_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ChatbotSettings',
        ),
    ]