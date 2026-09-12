import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("conversations", "0003_conversation_envoi_messages"),
        ("messaging", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="conversation_origine",
            field=models.ForeignKey(
                blank=True,
                db_column="id_conversation_origine",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="messages_transferes",
                to="conversations.conversation",
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="modifie_le",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="message",
            name="supprime_pour_tous_le",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="MessageHiddenFor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date_masquage", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("message", models.ForeignKey(db_column="id_message", on_delete=django.db.models.deletion.CASCADE, related_name="masquages", to="messaging.message")),
                ("utilisateur", models.ForeignKey(db_column="id_utilisateur", on_delete=django.db.models.deletion.CASCADE, related_name="messages_masques", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "message_masque_utilisateur"},
        ),
        migrations.CreateModel(
            name="MessageReaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("emoji", models.CharField(max_length=16)),
                ("date_creation", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("date_maj", models.DateTimeField(auto_now=True)),
                ("message", models.ForeignKey(db_column="id_message", on_delete=django.db.models.deletion.CASCADE, related_name="reactions", to="messaging.message")),
                ("utilisateur", models.ForeignKey(db_column="id_utilisateur", on_delete=django.db.models.deletion.CASCADE, related_name="reactions_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "reaction_message"},
        ),
        migrations.AddConstraint(
            model_name="messagehiddenfor",
            constraint=models.UniqueConstraint(fields=("message", "utilisateur"), name="message_masque_utilisateur_uniq"),
        ),
        migrations.AddConstraint(
            model_name="messagereaction",
            constraint=models.UniqueConstraint(fields=("message", "utilisateur"), name="reaction_message_utilisateur_uniq"),
        ),
        migrations.AddIndex(
            model_name="messagereaction",
            index=models.Index(fields=["message", "emoji"], name="reaction_message_emoji_idx"),
        ),
    ]
