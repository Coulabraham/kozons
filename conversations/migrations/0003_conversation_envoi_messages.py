from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("conversations", "0002_initial")]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="envoi_messages",
            field=models.CharField(
                choices=[("tous", "Tous les membres"), ("admins", "Administrateurs uniquement")],
                default="tous",
                max_length=8,
            ),
        ),
        migrations.AddConstraint(
            model_name="conversation",
            constraint=models.CheckConstraint(
                condition=models.Q(("envoi_messages__in", ["tous", "admins"])),
                name="conversation_envoi_messages_valide",
            ),
        ),
    ]
