from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("users", "0002_user_statut_personnalise")]
    operations = [
        migrations.AddField(
            model_name="user",
            name="tokens_valid_after",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="token_version",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="SecurityAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.CharField(max_length=64)),
                ("success", models.BooleanField(default=True)),
                ("ip_hash", models.CharField(blank=True, max_length=64)),
                ("subject_hash", models.CharField(blank=True, max_length=64)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="security_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "security_audit_event"},
        ),
        migrations.AddIndex(
            model_name="securityauditevent",
            index=models.Index(fields=["event", "-created_at"], name="security_event_date_idx"),
        ),
    ]
