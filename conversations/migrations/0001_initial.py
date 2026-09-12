import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('individuel', 'Individuel'), ('groupe', 'Groupe')], max_length=12)),
                ('nom', models.CharField(blank=True, max_length=150, null=True)),
                ('avatar_url', models.URLField(blank=True, max_length=2048, null=True)),
                ('individual_key', models.CharField(blank=True, max_length=64, null=True, unique=True)),
                ('date_creation', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'db_table': 'conversation',
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Administrateur'), ('membre', 'Membre')], default='membre', max_length=10)),
                ('date_ajout', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'db_table': 'membre_conversation',
            },
        ),
    ]
