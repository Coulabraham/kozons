import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.URLField(max_length=2048, unique=True)),
                ('p256dh', models.CharField(max_length=255)),
                ('auth', models.CharField(max_length=255)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('date_maj', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'push_subscription',
            },
        ),
    ]
