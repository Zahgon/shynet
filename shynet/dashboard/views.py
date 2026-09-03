from flask import redirect, url_for
from flask_login import current_user
from sqlalchemy import func, or_, select

from analytics.models import Session, Hit
from core.models import Service, _default_api_token, RESULTS_LIMIT
from shynet import settings
from shynet.cache import cache
from shynet.extensions import db
from shynet.views import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    UpdateView,
    View,
    get_object_or_404,
)

from .forms import ServiceForm
from .mixins import DateRangeMixin


class DashboardView(LoginRequiredMixin, DateRangeMixin, ListView):
    model = Service
    template_name = "dashboard/pages/dashboard.html"
    paginate_by = settings.DASHBOARD_PAGE_SIZE

    def get_queryset(self):
        return (
            select(Service)
            .where(
                or_(
                    Service.owner_id == current_user.id,
                    Service.collaborators.any(id=current_user.id),
                )
            )
            .order_by(*Service.default_order())
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        for service in data["object_list"]:
            service.stats = service.get_core_stats(
                self.get_start_date(), self.get_end_date()
            )

        return data


class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/pages/service_create.html"
    permission_required = "core.create_service"

    def form_valid(self, form):
        self.object = form.save(None, commit=False)
        self.object.owner = current_user._get_current_object()
        db.session.add(self.object)
        db.session.commit()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return url_for("dashboard.service", pk=self.object.uuid)


class ServiceView(
    LoginRequiredMixin, PermissionRequiredMixin, DateRangeMixin, DetailView
):
    model = Service
    template_name = "dashboard/pages/service.html"
    permission_required = "core.view_service"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["script_protocol"] = "https://" if settings.SCRIPT_USE_HTTPS else "http://"
        data["stats"] = self.object.get_core_stats(data["start_date"], data["end_date"])
        data["RESULTS_LIMIT"] = RESULTS_LIMIT
        data["object_list"] = list(
            db.session.execute(
                select(Session)
                .where(
                    Session.service_id == self.get_object().uuid,
                    Session.start_time < self.get_end_date(),
                    Session.start_time > self.get_start_date(),
                )
                .order_by(Session.start_time.desc())
                .limit(10)
            ).scalars()
        )
        return data


class ServiceUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/pages/service_update.html"
    permission_required = "core.change_service"
    success_message = "Your changes were saved successfully."

    def get_success_url(self):
        return url_for("dashboard.service", pk=self.object.uuid)

    def form_valid(self, *args, **kwargs):
        resp = super().form_valid(*args, **kwargs)
        cache.set(
            f"service_origins_{self.object.uuid}", self.object.origins, timeout=3600
        )
        cache.set(
            f"script_inject_{self.object.uuid}", self.object.script_inject, timeout=3600
        )
        return resp

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data["script_protocol"] = "https://" if settings.SCRIPT_USE_HTTPS else "http://"
        return data


class ServiceDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/pages/service_delete.html"
    permission_required = "core.delete_service"
    success_message = "The service was deleted successfully."

    def get_success_url(self):
        return url_for("dashboard.dashboard")


class ServiceSessionsListView(
    LoginRequiredMixin, PermissionRequiredMixin, DateRangeMixin, ListView
):
    model = Session
    template_name = "dashboard/pages/service_session_list.html"
    paginate_by = 20
    permission_required = "core.view_service"

    def get_object(self):
        return get_object_or_404(Service, self.kwargs.get("pk"))

    def get_queryset(self):
        return (
            select(Session)
            .where(
                Session.service_id == self.get_object().uuid,
                Session.start_time < self.get_end_date(),
                Session.start_time > self.get_start_date(),
            )
            .order_by(Session.start_time.desc())
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"] = self.get_object()
        return data


class ServiceLocationsListView(
    LoginRequiredMixin, PermissionRequiredMixin, DateRangeMixin, ListView
):
    model = Hit
    template_name = "dashboard/pages/service_location_list.html"
    paginate_by = RESULTS_LIMIT
    permission_required = "core.view_service"

    def get_object(self):
        return get_object_or_404(Service, self.kwargs.get("pk"))

    def get_queryset(self):
        hit_filters = (
            Hit.service_id == self.get_object().uuid,
            Hit.start_time < self.get_end_date(),
            Hit.start_time > self.get_start_date(),
        )
        self.hit_count = db.session.scalar(
            select(func.count()).select_from(Hit).where(*hit_filters)
        )

        count = func.count(Hit.location).label("count")
        rows = db.session.execute(
            select(Hit.location, count)
            .where(*hit_filters)
            .group_by(Hit.location)
            .order_by(count.desc())
        )
        return [{"location": row[0], "count": row[1]} for row in rows]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"] = self.get_object()
        data["hit_count"] = self.hit_count
        return data


class ServiceSessionView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Session
    template_name = "dashboard/pages/service_session.html"
    pk_url_kwarg = "session_pk"
    context_object_name = "session"
    permission_required = "core.view_service"

    def get_permission_object(self, **kwargs):
        return self.get_object().service

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"] = get_object_or_404(Service, self.kwargs.get("pk"))
        return data


class RefreshApiTokenView(LoginRequiredMixin, View):
    def post(self, **kwargs):
        current_user.api_token = _default_api_token()
        db.session.add(current_user._get_current_object())
        db.session.commit()
        return redirect(url_for("accounts.change_password"))
