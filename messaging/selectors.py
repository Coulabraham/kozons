from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import connection
from rest_framework.exceptions import PermissionDenied

from conversations.models import Membership

from .models import Message


def messages_for_user(*, user, conversation_id):
    if not Membership.objects.filter(
        conversation_id=conversation_id,
        utilisateur=user,
    ).exists():
        raise PermissionDenied("Vous n’êtes pas membre de cette conversation.")
    return (
        Message.objects.filter(conversation_id=conversation_id)
        .exclude(masquages__utilisateur=user)
        .select_related("utilisateur_expediteur")
        .prefetch_related("statuts", "reactions")
        .order_by("-date_envoi", "-id")
    )


def search_messages_for_user(*, user, conversation_id, query):
    queryset = messages_for_user(user=user, conversation_id=conversation_id).filter(
        supprime_pour_tous_le__isnull=True,
        type=Message.Type.TEXTE,
    )
    if connection.vendor == "postgresql":
        vector = SearchVector("contenu", config="french")
        search_query = SearchQuery(query, config="french", search_type="websearch")
        return (
            queryset.annotate(rank=SearchRank(vector, search_query))
            .filter(rank__gte=0.05)
            .order_by("-rank", "-date_envoi", "-id")[:100]
        )
    return queryset.filter(contenu__icontains=query).order_by("-date_envoi", "-id")[:100]
