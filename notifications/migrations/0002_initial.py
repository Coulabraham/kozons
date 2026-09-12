import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('notifications', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='pushsubscription',
            name='utilisateur',
            field=models.ForeignKey(db_column='id_utilisateur', on_delete=django.db.models.deletion.CASCADE, related_name='push_subscriptions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='pushsubscription',
            index=models.Index(fields=['utilisateur', 'actif'], name='push_user_active_idx'),
        ),
    ]
