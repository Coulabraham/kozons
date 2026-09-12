import uuid

from django.core.management.base import BaseCommand
from django.db import transaction

from contacts.models import Contact
from conversations.models import Conversation, Membership
from conversations.services import _individual_key
from messaging.models import Message, MessageReceipt
from users.models import User


class Command(BaseCommand):
    help = "Charge un jeu de données Kozons idempotent réservé au développement."

    @transaction.atomic
    def handle(self, *args, **options):
        password = "KozonsTest2026!"
        specs = [
            ("+221770000001", "amina.seed@example.test", "Amina Diop"),
            ("+221770000002", None, "Brice Fall"),
            (None, "chloe.seed@example.test", "Chloé Mensah"),
            ("+2250700000004", "david.seed@example.test", "David Kouassi"),
        ]
        users = []
        for telephone, email, name in specs:
            lookup = {"telephone": telephone} if telephone else {"email": email}
            user, _ = User.objects.get_or_create(
                **lookup,
                defaults={"email": email, "telephone": telephone, "nom_affichage": name},
            )
            user.email = email
            user.telephone = telephone
            user.nom_affichage = name
            user.is_active = True
            user.statut = User.Statut.ACTIF
            user.set_password(password)
            user.save()
            users.append(user)

        for owner, contact in [
            (users[0], users[1]),
            (users[1], users[0]),
            (users[0], users[2]),
            (users[2], users[3]),
        ]:
            Contact.objects.get_or_create(
                utilisateur_proprietaire=owner,
                utilisateur_contact=contact,
            )

        direct_specs = [(users[0], users[1]), (users[2], users[3])]
        conversations = []
        for creator, peer in direct_specs:
            conversation, _ = Conversation.objects.get_or_create(
                individual_key=_individual_key({creator.id, peer.id}),
                defaults={"type": Conversation.Type.INDIVIDUEL, "utilisateur_createur": creator},
            )
            Membership.objects.get_or_create(
                conversation=conversation,
                utilisateur=creator,
                defaults={"role": Membership.Role.ADMIN},
            )
            Membership.objects.get_or_create(
                conversation=conversation,
                utilisateur=peer,
                defaults={"role": Membership.Role.MEMBRE},
            )
            conversations.append(conversation)

        group, _ = Conversation.objects.get_or_create(
            type=Conversation.Type.GROUPE,
            nom="Équipe Kozons",
            utilisateur_createur=users[0],
        )
        for index, user in enumerate(users):
            Membership.objects.get_or_create(
                conversation=group,
                utilisateur=user,
                defaults={"role": Membership.Role.ADMIN if index == 0 else Membership.Role.MEMBRE},
            )
        conversations.append(group)

        message_specs = [
            (conversations[0], users[0], "texte", "Salut Brice, prêt pour un test ?", None, None),
            (
                conversations[0],
                users[1],
                "note_vocale",
                None,
                "s3://kozons-dev/processed/dev/conversations/demo/note_vocale/voice.ogg",
                18,
            ),
            (
                conversations[1],
                users[2],
                "image",
                "Voici la maquette.",
                "s3://kozons-dev/uploads/dev/conversations/demo/image/mockup.webp",
                None,
            ),
            (group, users[0], "texte", "Bienvenue dans le groupe de test !", None, None),
            (
                group,
                users[3],
                "video",
                "Démonstration vidéo.",
                "s3://kozons-dev/processed/dev/conversations/demo/video/demo.mp4",
                42,
            ),
        ]
        namespace = uuid.UUID("8de9b880-7db0-4c49-933d-9ec9b761bd77")
        for index, (conversation, sender, kind, content, media_url, duration) in enumerate(message_specs):
            client_id = uuid.uuid5(namespace, f"seed-message-{index}")
            message, _ = Message.objects.get_or_create(
                conversation=conversation,
                utilisateur_expediteur=sender,
                client_id=client_id,
                defaults={
                    "type": kind,
                    "contenu": content,
                    "media_url": media_url,
                    "duree": duration,
                },
            )
            for membership in conversation.membres.exclude(utilisateur=sender):
                MessageReceipt.objects.get_or_create(
                    message=message,
                    utilisateur=membership.utilisateur,
                    defaults={"statut": MessageReceipt.Status.ENVOYE},
                )

        self.stdout.write(self.style.SUCCESS("Seed Kozons chargé. Mot de passe : KozonsTest2026!"))
