from rest_framework.pagination import CursorPagination


class MessageCursorPagination(CursorPagination):
    page_size = 50
    max_page_size = 100
    page_size_query_param = "page_size"
    ordering = ("-date_envoi", "-id")
    cursor_query_param = "cursor"
