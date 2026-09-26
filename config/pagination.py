from rest_framework.pagination import CursorPagination, LimitOffsetPagination, PageNumberPagination

class StandardPagination(PageNumberPagination):   # ?page=2
    page_size=10
    page_size_query_param = "page_size"       # client may ask ?page_size=25
    max_page_size=100

class StandardLimitOffsetPagination(LimitOffsetPagination):  # ?limit=10&offset=20 (for the exercise)
    default_limit=10
    max_limit=100

class OrderCursorPagination(CursorPagination):   # ?cursor=...
    page_size=10
    ordering= "-created_at"   # cursor needs a fixed order: newest first