import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('messaging', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='utilisateur_expediteur',
            field=models.ForeignKey(db_column='id_utilisateur_expediteur', on_delete=django.db.models.deletion.PROTECT, related_name='messages_envoyes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='messagereceipt',
            name='message',
            field=models.ForeignKey(db_column='id_message', on_delete=django.db.models.deletion.CASCADE, related_name='statuts', to='messaging.message'),
        ),
        migrations.AddField(
            model_name='messagereceipt',
            name='utilisateur',
            field=models.ForeignKey(db_column='id_utilisateur', on_delete=django.db.models.deletion.PROTECT, related_name='statuts_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['conversation', '-date_envoi', '-id'], name='message_conv_date_id_idx'),
        ),
        migrations.AddConstraint(
            model_name='message',
            constraint=models.UniqueConstraint(condition=models.Q(('client_id__isnull', False)), fields=('conversation', 'utilisateur_expediteur', 'client_id'), name='message_client_id_uniq'),
        ),
        migrations.AddConstraint(
            model_name='message',
            constraint=models.CheckConstraint(condition=models.Q(('type__in', ['texte', 'note_vocale', 'image', 'video'])), name='message_type_valide'),
        ),
        migrations.AddConstraint(
            model_name='message',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('type', 'texte'), ('contenu__isnull', False), models.Q(('contenu', ''), _negated=True)), models.Q(('type__in', ['note_vocale', 'image', 'video']), ('media_url__isnull', False), models.Q(('media_url', ''), _negated=True)), _connector='OR'), name='message_charge_utile_valide'),
        ),
        migrations.AddConstraint(
            model_name='message',
            constraint=models.CheckConstraint(condition=models.Q(('duree__isnull', True), ('duree__gt', 0), _connector='OR'), name='message_duree_positive'),
        ),
        migrations.AddConstraint(
            model_name='message',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('type', 'note_vocale'), _negated=True), ('duree__gt', 0), _connector='OR'), name='message_vocal_duree_requise'),
        ),
        migrations.AddIndex(
            model_name='messagereceipt',
            index=models.Index(fields=['utilisateur', 'statut', '-date_maj'], name='statut_user_state_date_idx'),
        ),
        migrations.AddConstraint(
            model_name='messagereceipt',
            constraint=models.UniqueConstraint(fields=('message', 'utilisateur'), name='statut_message_utilisateur_uniq'),
        ),
        migrations.AddConstraint(
            model_name='messagereceipt',
            constraint=models.CheckConstraint(condition=models.Q(('statut__in', ['envoye', 'recu', 'lu'])), name='statut_message_valide'),
        ),
    ]
