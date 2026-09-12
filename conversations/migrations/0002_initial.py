import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('conversations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='utilisateur_createur',
            field=models.ForeignKey(db_column='id_utilisateur_createur', on_delete=django.db.models.deletion.PROTECT, related_name='conversations_creees', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='membership',
            name='conversation',
            field=models.ForeignKey(db_column='id_conversation', on_delete=django.db.models.deletion.CASCADE, related_name='membres', to='conversations.conversation'),
        ),
        migrations.AddField(
            model_name='membership',
            name='utilisateur',
            field=models.ForeignKey(db_column='id_utilisateur', on_delete=django.db.models.deletion.PROTECT, related_name='participations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conversation',
            name='participants',
            field=models.ManyToManyField(related_name='conversations', through='conversations.Membership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='membership',
            constraint=models.UniqueConstraint(fields=('conversation', 'utilisateur'), name='membre_conversation_utilisateur_uniq'),
        ),
        migrations.AddConstraint(
            model_name='membership',
            constraint=models.CheckConstraint(condition=models.Q(('role__in', ['admin', 'membre'])), name='membre_role_valide'),
        ),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.CheckConstraint(condition=models.Q(('type__in', ['individuel', 'groupe'])), name='conversation_type_valide'),
        ),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.CheckConstraint(condition=models.Q(('type', 'individuel'), models.Q(('nom__isnull', False), models.Q(('nom', ''), _negated=True)), _connector='OR'), name='conversation_groupe_nom_requis'),
        ),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('type', 'individuel'), ('individual_key__isnull', False)), models.Q(('type', 'groupe'), ('individual_key__isnull', True)), _connector='OR'), name='conversation_cle_individuelle_valide'),
        ),
    ]
