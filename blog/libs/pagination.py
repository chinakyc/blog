"""
    pagination
    ~~~~~~~~~~
    from https://github.com/MongoEngine/flask-mongoengine
"""
import math
from mongoengine.queryset import QuerySet
from tornado.web import HTTPError

__all__ = ("Pagination")


class Pagination(object):
    def __init__(self, iterable, page, per_page):
        if page < 1:
            raise HTTPError(404)

        if not iterable:
            raise HTTPError(404)

        self.iterable = iterable
        self.page = page
        self.per_page = per_page

        if isinstance(iterable, QuerySet):
            self.total = iterable.count()
        else:
            self.total = len(iterable)

        start_index = (page - 1) * per_page
        end_index = page * per_page

        self.items = iterable[start_index:end_index]
        if isinstance(self.items, QuerySet):
            self.items = self.items.select_related()
        if not self.items and page != 1:
            raise HTTPError(404)

    @property
    def pages(self):
        """The total number of pages"""
        return int(math.ceil(self.total / float(self.per_page)))

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.iterable is not None, ("an object is required "
                                           "for this method to work")
        iterable = self.iterable
        if isinstance(iterable, QuerySet):
            iterable._skip = None
            iterable._limit = None
            iterable = iterable.clone()
        return self.__class__(iterable, self.page - 1, self.per_page)

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.iterable is not None, ("an object is required "
                                           "for this method to work")
        iterable = self.iterable
        if isinstance(iterable, QuerySet):
            iterable._skip = None
            iterable._limit = None
            iterable = iterable.clone()
        return self.__class__(iterable, self.page + 1, self.per_page)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
                    (num > self.page - left_current - 1 and
                     num > self.page + right_current) or \
                    num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
