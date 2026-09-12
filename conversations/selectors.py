from django.db.models import Prefetch, Q

from contacts.models import Contact

from .models import Conversation, Membership


def conversations_for_user(user):
    memberships = Membership.objects.select_related("utilisateur").order_by("date_ajout")
    return (
        Conversation.objects.filter(membres__utilisateur=user)
        .select_related("utilisateur_createur")
        .prefetch_related(Prefetch("membres", queryset=memberships))
        .order_by("-date_creation", "-id")
    )


def search_conversations_and_contacts(*, user, query):
    conversations = conversations_for_user(user).filter(
        Q(nom__icontains=query)
        | Q(membres__utilisateur__nom_affichage__icontains=query)
    ).distinct()[:50]
    contacts = (
        Contact.objects.filter(
            utilisateur_proprietaire=user,
            utilisateur_contact__nom_affichage__icontains=query,
        )
        .select_related("utilisateur_contact")
        .order_by("utilisateur_contact__nom_affichage")[:50]
    )
    return conversations, [contact.utilisateur_contact for contact in contacts]
