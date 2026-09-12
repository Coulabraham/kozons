import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('conversations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('statut', models.CharField(choices=[('envoye', 'Envoyé'), ('recu', 'Reçu'), ('lu', 'Lu')], default='envoye', max_length=6)),
                ('date_maj', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'statut_message',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.UUIDField(blank=True, null=True)),
                ('type', models.CharField(choices=[('texte', 'Texte'), ('note_vocale', 'Note vocale'), ('image', 'Image'), ('video', 'Vidéo')], max_length=12)),
                ('contenu', models.TextField(blank=True, null=True)),
                ('media_url', models.CharField(blank=True, max_length=2048, null=True)),
                ('duree', models.PositiveIntegerField(blank=True, help_text='Durée en secondes', null=True)),
                ('date_envoi', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('conversation', models.ForeignKey(db_column='id_conversation', on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='conversations.conversation')),
            ],
            options={
                'db_table': 'message',
            },
        ),
    ]
