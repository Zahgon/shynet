"""Pagination.

`Paginator`/`Page` keep the same public surface the templates and the
`pagination` template tag were written against (`page.number`,
`page.has_next`, `page.paginator.page_range`, ...), but slice SQLAlchemy
selects instead of querysets.
"""

import math

from sqlalchemy import func, select
from sqlalchemy.sql import Select

from .extensions import db


class InvalidPage(Exception):
    """The requested page number does not exist."""


class PageNotAnInteger(InvalidPage):
    pass


class EmptyPage(InvalidPage):
    pass


class Paginator:
    def __init__(self, object_list, per_page, allow_empty_first_page=True):
        self.object_list = object_list
        self.per_page = int(per_page)
        self.allow_empty_first_page = allow_empty_first_page
        self._count = None

    @property
    def count(self):
        if self._count is None:
            if isinstance(self.object_list, Select):
                subquery = self.object_list.order_by(None).subquery()
                self._count = (
                    db.session.execute(
                        select(func.count()).select_from(subquery)
                    ).scalar()
                    or 0
                )
            else:
                self._count = len(self.object_list)
        return self._count

    @property
    def num_pages(self):
        if self.count == 0 and not self.allow_empty_first_page:
            return 0
        return max(1, int(math.ceil(self.count / self.per_page)))

    @property
    def page_range(self):
        return range(1, self.num_pages + 1)

    def validate_number(self, number):
        """Return `number` as a valid page number, or raise `InvalidPage`."""
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger("That page number is not an integer")
        if number < 1:
            raise EmptyPage("That page number is less than 1")
        if number > self.num_pages:
            raise EmptyPage("That page contains no results")
        return number

    def page(self, number):
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        if isinstance(self.object_list, Select):
            statement = self.object_list.offset(bottom).limit(self.per_page)
            object_list = list(db.session.execute(statement).scalars())
        else:
            object_list = list(self.object_list[bottom : bottom + self.per_page])
        return Page(object_list, number, self)


class Page:
    def __init__(self, object_list, number, paginator):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __iter__(self):
        return iter(self.object_list)

    def __len__(self):
        return len(self.object_list)

    @property
    def has_previous(self):
        return self.number > 1

    @property
    def has_next(self):
        return self.number < self.paginator.num_pages

    @property
    def has_other_pages(self):
        return self.has_previous or self.has_next

    @property
    def previous_page_number(self):
        return self.number - 1

    @property
    def next_page_number(self):
        return self.number + 1

    @property
    def start_index(self):
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1

    @property
    def end_index(self):
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page


def paginate(object_list, per_page, page_number=None):
    """Paginate `object_list`, reading `?page=` from the request by default."""
    from flask import request

    paginator = Paginator(object_list, per_page)
    if page_number is None:
        page_number = request.args.get("page", 1)
    return paginator.page(page_number)


def resolve_page_number(paginator, page):
    """Turn a raw `?page=` value into a page number, 404-ing when it is invalid."""
    from flask import abort

    try:
        return int(page)
    except (TypeError, ValueError):
        if page == "last":
            return paginator.num_pages
        abort(404)
