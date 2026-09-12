import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('media', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaasset',
            name='utilisateur',
            field=models.ForeignKey(db_column='id_utilisateur', on_delete=django.db.models.deletion.PROTECT, related_name='medias', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='mediaasset',
            constraint=models.CheckConstraint(condition=models.Q(('type__in', ['image', 'video', 'note_vocale'])), name='media_type_valide'),
        ),
        migrations.AddConstraint(
            model_name='mediaasset',
            constraint=models.CheckConstraint(condition=models.Q(('statut__in', ['en_attente', 'uploade', 'traitement', 'pret', 'echec'])), name='media_statut_valide'),
        ),
        migrations.AddConstraint(
            model_name='mediaasset',
            constraint=models.CheckConstraint(condition=models.Q(('taille_octets__gt', 0)), name='media_taille_positive'),
        ),
    ]
