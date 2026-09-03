"""Generic class-based views.

Flask equivalents of the generic views the dashboard is built on
(`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`) plus the
access-control and messaging mixins, so the view classes keep the same shape and
hook names they had before.
"""

from flask import abort, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user
from flask_wtf import FlaskForm
from sqlalchemy import select
from sqlalchemy.exc import StatementError

from . import messages, rules
from .exceptions import MissingObjectIdentifier
from .extensions import db
from .pagination import InvalidPage, Paginator, resolve_page_number


class EmptyForm(FlaskForm):
    """A form with nothing but a CSRF token (used for confirm-and-submit pages)."""


class ContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        kwargs.setdefault("view", self)
        if self.extra_context is not None:
            kwargs.update(self.extra_context)
        return kwargs


class TemplateResponseMixin:
    template_name = None

    def render_to_response(self, context):
        return render_template(self.template_name, **context)


class View(ContextMixin, TemplateResponseMixin, MethodView):
    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        return super().dispatch_request(**kwargs)


class LoginRequiredMixin:
    def dispatch_request(self, **kwargs):
        if not current_user.is_authenticated:
            return redirect(
                url_for("accounts.login", next=request.full_path.rstrip("?"))
            )
        return super().dispatch_request(**kwargs)


class PermissionRequiredMixin:
    permission_required = None

    def get_permission_required(self):
        if self.permission_required is None:
            raise RuntimeError(
                f"{type(self).__name__} is missing the permission_required attribute."
            )
        if isinstance(self.permission_required, str):
            return (self.permission_required,)
        return self.permission_required

    def get_permission_object(self, **kwargs):
        if hasattr(self, "get_object"):
            try:
                return self.get_object()
            except MissingObjectIdentifier:
                # Views that create objects check the permission without one.
                return None
        return getattr(self, "object", None)

    def has_permission(self):
        obj = self.get_permission_object()
        return all(
            rules.has_perm(perm, current_user, obj)
            for perm in self.get_permission_required()
        )

    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        if not self.has_permission():
            abort(403)
        return super().dispatch_request(**kwargs)


class SuccessMessageMixin:
    success_message = ""

    def get_success_message(self, cleaned_data):
        return self.success_message

    def form_valid(self, form):
        response = super().form_valid(form)
        success_message = self.get_success_message(form.data)
        if success_message:
            messages.success(success_message)
        return response


class SingleObjectMixin(ContextMixin):
    model = None
    pk_url_kwarg = "pk"
    context_object_name = None

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is None:
            # A create view has nothing to look up; this is distinct from a
            # lookup that found nothing, which must still 404.
            raise MissingObjectIdentifier(
                f"{type(self).__name__} was called without a {self.pk_url_kwarg}."
            )
        return get_object_or_404(self.model, pk)

    def get_context_object_name(self):
        if self.context_object_name is not None:
            return self.context_object_name
        if self.model is not None:
            return self.model.__name__.lower()
        return None

    def get_context_data(self, **kwargs):
        if getattr(self, "object", None) is not None:
            kwargs.setdefault("object", self.object)
            name = self.get_context_object_name()
            if name:
                kwargs.setdefault(name, self.object)
        return super().get_context_data(**kwargs)


class DetailView(SingleObjectMixin, TemplateResponseMixin, MethodView):
    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        return super().dispatch_request(**kwargs)

    def get(self, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        return self.render_to_response(context)


class MultipleObjectMixin(ContextMixin):
    model = None
    paginate_by = None
    context_object_name = None

    def get_queryset(self):
        return select(self.model)

    def get_context_object_name(self):
        if self.context_object_name is not None:
            return self.context_object_name
        return None

    def paginate_queryset(self, queryset, page_size):
        paginator = Paginator(queryset, page_size)
        page_number = resolve_page_number(paginator, request.args.get("page", 1))
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            abort(404)
        return paginator, page, page.object_list, page.paginator.num_pages > 1

    def get_context_data(self, **kwargs):
        queryset = self.get_queryset()
        page_size = self.paginate_by
        if page_size:
            paginator, page, object_list, is_paginated = self.paginate_queryset(
                queryset, page_size
            )
            kwargs.setdefault("paginator", paginator)
            kwargs.setdefault("page_obj", page)
            kwargs.setdefault("is_paginated", is_paginated)
        else:
            object_list = _resolve_queryset(queryset)
            kwargs.setdefault("paginator", None)
            kwargs.setdefault("page_obj", None)
            kwargs.setdefault("is_paginated", False)
        kwargs.setdefault("object_list", object_list)
        name = self.get_context_object_name()
        if name:
            kwargs.setdefault(name, object_list)
        return super().get_context_data(**kwargs)


class ListView(MultipleObjectMixin, TemplateResponseMixin, MethodView):
    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        return super().dispatch_request(**kwargs)

    def get(self, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)


class FormMixin(ContextMixin):
    form_class = None
    success_url = None

    def get_form_kwargs(self):
        return {}

    def get_form(self):
        return self.form_class(**self.get_form_kwargs())

    def get_success_url(self):
        if self.success_url is None:
            raise RuntimeError("No URL to redirect to.")
        return self.success_url

    def form_valid(self, form):
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        kwargs.setdefault("form", getattr(self, "form", None))
        return super().get_context_data(**kwargs)


class ModelFormMixin(FormMixin, SingleObjectMixin):
    def get_form_kwargs(self):
        return {"obj": self.object} if self.object is not None else {}

    def form_valid(self, form):
        self.object = form.save(self.object)
        return super().form_valid(form)


class CreateView(ModelFormMixin, TemplateResponseMixin, MethodView):
    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        self.object = None
        return super().dispatch_request(**kwargs)

    def get(self, **kwargs):
        self.form = self.get_form()
        return self.render_to_response(self.get_context_data(form=self.form))

    def post(self, **kwargs):
        self.form = self.get_form()
        if self.form.validate_on_submit():
            return self.form_valid(self.form)
        return self.form_invalid(self.form)


class UpdateView(ModelFormMixin, TemplateResponseMixin, MethodView):
    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        self.object = self.get_object()
        return super().dispatch_request(**kwargs)

    def get(self, **kwargs):
        self.form = self.get_form()
        return self.render_to_response(self.get_context_data(form=self.form))

    def post(self, **kwargs):
        self.form = self.get_form()
        if self.form.validate_on_submit():
            return self.form_valid(self.form)
        return self.form_invalid(self.form)


class DeleteView(ModelFormMixin, TemplateResponseMixin, MethodView):
    form_class = EmptyForm

    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        self.object = self.get_object()
        return super().dispatch_request(**kwargs)

    def get(self, **kwargs):
        self.form = self.get_form()
        return self.render_to_response(self.get_context_data(form=self.form))

    def post(self, **kwargs):
        self.form = self.get_form()
        if self.form.validate_on_submit():
            return self.form_valid(self.form)
        return self.form_invalid(self.form)

    def form_valid(self, form):
        db.session.delete(self.object)
        db.session.commit()
        return redirect(self.get_success_url())


def _resolve_queryset(queryset):
    if isinstance(queryset, (list, tuple)):
        return list(queryset)
    return list(db.session.execute(queryset).scalars())


def get_object_or_404(model, pk):
    """Look `model` up by primary key, aborting with a 404 when it is absent."""
    if pk is None:
        abort(404)
    try:
        obj = db.session.get(model, pk)
    except (ValueError, TypeError, StatementError):
        # A malformed primary key (e.g. an invalid UUID) is simply not found.
        db.session.rollback()
        obj = None
    if obj is None:
        abort(404)
    return obj
