from django.db import migrations


def create_search_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS message_contenu_fts_idx
        ON message
        USING GIN (to_tsvector('french', coalesce(contenu, '')))
        WHERE supprime_pour_tous_le IS NULL AND type = 'texte'
        """
    )


def drop_search_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        "DROP INDEX CONCURRENTLY IF EXISTS message_contenu_fts_idx"
    )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("messaging", "0003_message_actions_and_reactions"),
    ]

    operations = [
        migrations.RunPython(create_search_index, drop_search_index),
    ]
