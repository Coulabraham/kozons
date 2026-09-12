import django.db.models.deletion
import django.utils.timezone
import users.managers
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('password', models.CharField(db_column='mot_de_passe_hash', max_length=128)),
                ('telephone', models.CharField(blank=True, max_length=32, null=True, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ('nom_affichage', models.CharField(max_length=150)),
                ('avatar_url', models.URLField(blank=True, max_length=2048, null=True)),
                ('statut', models.CharField(choices=[('actif', 'Actif'), ('inactif', 'Inactif'), ('suspendu', 'Suspendu')], default='inactif', max_length=20)),
                ('last_login', models.DateTimeField(blank=True, db_column='derniere_connexion', null=True)),
                ('en_ligne', models.BooleanField(default=False)),
                ('date_creation', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('is_active', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'utilisateur',
            },
            managers=[
                ('objects', users.managers.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='OTPVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('sms', 'SMS'), ('email', 'Email')], max_length=8)),
                ('purpose', models.CharField(choices=[('registration', 'Inscription'), ('login', 'Connexion')], max_length=16)),
                ('code_hash', models.CharField(max_length=128)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('expires_at', models.DateTimeField()),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otps', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'otp_verification',
            },
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('telephone__isnull', False), models.Q(('telephone', ''), _negated=True)), models.Q(('email__isnull', False), models.Q(('email', ''), _negated=True)), _connector='OR'), name='utilisateur_contact_requis'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(condition=models.Q(('statut__in', ['actif', 'inactif', 'suspendu'])), name='utilisateur_statut_valide'),
        ),
        migrations.AddIndex(
            model_name='otpverification',
            index=models.Index(fields=['user', 'purpose', '-created_at'], name='otp_user_purpose_created_idx'),
        ),
    ]
