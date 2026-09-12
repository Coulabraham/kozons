import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contacts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='utilisateur_contact',
            field=models.ForeignKey(db_column='id_utilisateur_contact', on_delete=django.db.models.deletion.CASCADE, related_name='present_dans_les_contacts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contact',
            name='utilisateur_proprietaire',
            field=models.ForeignKey(db_column='id_utilisateur_proprietaire', on_delete=django.db.models.deletion.CASCADE, related_name='contacts_possedes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='contact',
            constraint=models.UniqueConstraint(fields=('utilisateur_proprietaire', 'utilisateur_contact'), name='contact_proprietaire_contact_uniq'),
        ),
        migrations.AddConstraint(
            model_name='contact',
            constraint=models.CheckConstraint(condition=models.Q(('utilisateur_proprietaire', models.F('utilisateur_contact')), _negated=True), name='contact_pas_soi_meme'),
        ),
    ]
