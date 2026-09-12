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
            name='MediaAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('image', 'Image'), ('video', 'Vidéo'), ('note_vocale', 'Note vocale')], max_length=12)),
                ('statut', models.CharField(choices=[('en_attente', 'En attente d’upload'), ('uploade', 'Uploadé'), ('traitement', 'En traitement'), ('pret', 'Prêt'), ('echec', 'Échec')], default='en_attente', max_length=12)),
                ('source_object_key', models.CharField(max_length=1024, unique=True)),
                ('output_object_key', models.CharField(blank=True, max_length=1024, null=True)),
                ('thumbnail_object_key', models.CharField(blank=True, max_length=1024, null=True)),
                ('content_type', models.CharField(max_length=100)),
                ('taille_octets', models.PositiveBigIntegerField()),
                ('duree', models.PositiveIntegerField(blank=True, null=True)),
                ('erreur', models.TextField(blank=True, null=True)),
                ('date_creation', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('date_maj', models.DateTimeField(auto_now=True)),
                ('conversation', models.ForeignKey(blank=True, db_column='id_conversation', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='medias', to='conversations.conversation')),
            ],
            options={
                'db_table': 'media_asset',
            },
        ),
    ]
