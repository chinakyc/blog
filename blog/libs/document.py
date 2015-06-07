"""
    Document.py
    ~~~~~~~~~~~
    custom Document
"""
from mongoengine import Document
from libs.pagination import Pagination
from mongoengine.queryset import QuerySet
from libs.concurrent import CustomThreadPoolExecutor


class BaseQuerySet(QuerySet):
    """
    A base queryset with handy extras
    """
    def paginate(self, page, per_page, error_out=True):
        return Pagination(self, page, per_page)


class Custom_Document(Document):
    _executor = CustomThreadPoolExecutor(10)

    meta = {"abstract": True,
            "queryset_class": BaseQuerySet}

    def save(self):
        "rewrite `save` return  a `future` object"
        future = self._executor.submit(super().save)
        return future

    @classmethod
    def asyncQuery(cls, *args, **kwargs):
        "lazy get objects in executor"

        # TODO
        # This is a shit , I am too young too naive, This shit can't not
        # real async.
        # I thought `cls.objects` dircet fetch documents from the database,
        # but the true is the QuerySet object iterated over to fetch documents
        # from the database.
        # If you know what you want, you can use
        # `.submit(list, minimalQueryset)`. consume QuerySet in executor
        custom_future = cls._executor.submit(lambda: cls.objects(*args,
                                                                 **kwargs))
        return custom_future
