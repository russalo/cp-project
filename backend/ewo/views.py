import logging

from django.db.models import Count

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny

from .models import EquipmentLine, ExtraWorkOrder, LaborLine, MaterialLine, WorkDay
from .serializers import (
    EquipmentLineSerializer,
    ExtraWorkOrderSerializer,
    LaborLineSerializer,
    MaterialLineSerializer,
    WorkDaySerializer,
)
from .services import calculate_ewo_totals


logger = logging.getLogger(__name__)


def _recalc_if_editable(ewo):
    """
    Recompute WorkDay + EWO totals whenever an editable EWO's line items
    change. Skipped on locked EWOs so frozen numbers stay frozen (DEC-031).

    Rate-lookup failures (e.g. missing LaborRate for a work_date, or an
    EquipmentType without any rates configured) are logged but do not
    surface to the caller — the CRUD call already succeeded with a 2xx;
    raising from a post-save hook would confuse the user. Totals remain
    at their previous value until the next successful recalc or submit.
    """
    if ewo is None or getattr(ewo, 'is_locked', True):
        return
    try:
        calculate_ewo_totals(ewo)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            'recalc skipped for EWO %s: %s: %s',
            ewo.ewo_number, type(exc).__name__, exc,
        )


class EwoLockedDeleteMixin:
    def perform_destroy(self, instance):
        if getattr(instance, 'is_locked', False):
            raise ValidationError('Locked EWOs cannot be deleted through CRUD endpoints.')
        super().perform_destroy(instance)


class ParentEwoLockedDeleteMixin:
    """Guard + recalc trigger for line-item viewsets under a WorkDay."""
    def perform_create(self, serializer):
        serializer.save()
        _recalc_if_editable(serializer.instance.work_day.ewo)

    def perform_update(self, serializer):
        serializer.save()
        _recalc_if_editable(serializer.instance.work_day.ewo)

    def perform_destroy(self, instance):
        if instance.work_day.ewo.is_locked:
            raise ValidationError(
                'Line items on locked EWOs cannot be deleted through CRUD endpoints.'
            )
        ewo = instance.work_day.ewo
        super().perform_destroy(instance)
        _recalc_if_editable(ewo)


class WorkDayLockedDeleteMixin:
    def perform_create(self, serializer):
        serializer.save()
        _recalc_if_editable(serializer.instance.ewo)

    def perform_update(self, serializer):
        serializer.save()
        _recalc_if_editable(serializer.instance.ewo)

    def perform_destroy(self, instance):
        if instance.ewo.is_locked:
            raise ValidationError(
                'WorkDays on locked EWOs cannot be deleted through CRUD endpoints.'
            )
        ewo = instance.ewo
        super().perform_destroy(instance)
        _recalc_if_editable(ewo)


class ExtraWorkOrderViewSet(EwoLockedDeleteMixin, viewsets.ModelViewSet):
    """
    CRUD-only EWO API. Lifecycle transitions stay out of this viewset so submit/
    approval behavior can be implemented explicitly later.

    Supported filters:
        ?job=<id>      — only EWOs on that job
        ?status=<s>    — filter by status (open, submitted, approved, …)
    """

    queryset = (
        ExtraWorkOrder.objects
        .select_related('job', 'created_by', 'parent_ewo')
        # Annotate counts so the serializer doesn't fire 4 queries per row.
        .annotate(
            workday_count=Count('work_days', distinct=True),
            labor_count=Count('work_days__labor_lines', distinct=True),
            equipment_count=Count('work_days__equipment_lines', distinct=True),
            materials_count=Count('work_days__material_lines', distinct=True),
        )
        .order_by('-ewo_sequence', 'ewo_number')
    )
    serializer_class = ExtraWorkOrderSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        job_id = self.request.query_params.get('job')
        status_ = self.request.query_params.get('status')
        # Validate job id is numeric so a malformed query doesn't produce a
        # 500 (Django would raise ValueError coercing the string to int).
        if job_id and job_id.isdigit():
            qs = qs.filter(job_id=int(job_id))
        if status_:
            qs = qs.filter(status=status_)
        return qs

    def perform_update(self, serializer):
        # Changing fuel %, OH&P, bond, or bond_required on an open EWO should
        # refresh the totals immediately so the UI stays in sync.
        serializer.save()
        _recalc_if_editable(serializer.instance)


class WorkDayViewSet(WorkDayLockedDeleteMixin, viewsets.ModelViewSet):
    queryset = (
        WorkDay.objects
        .select_related('ewo', 'ewo__job')
        .order_by('ewo', 'work_date')
    )
    serializer_class = WorkDaySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        ewo_id = self.request.query_params.get('ewo')
        if ewo_id:
            queryset = queryset.filter(ewo_id=ewo_id)
        return queryset


class LaborLineViewSet(ParentEwoLockedDeleteMixin, viewsets.ModelViewSet):
    queryset = (
        LaborLine.objects
        .select_related(
            'work_day', 'work_day__ewo',
            'employee', 'employee_default_trade', 'trade_classification',
        )
        .order_by('id')
    )
    serializer_class = LaborLineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        work_day_id = self.request.query_params.get('work_day')
        ewo_id = self.request.query_params.get('ewo')
        if work_day_id:
            queryset = queryset.filter(work_day_id=work_day_id)
        elif ewo_id:
            queryset = queryset.filter(work_day__ewo_id=ewo_id)
        return queryset


class EquipmentLineViewSet(ParentEwoLockedDeleteMixin, viewsets.ModelViewSet):
    queryset = (
        EquipmentLine.objects
        .select_related(
            'work_day', 'work_day__ewo',
            'equipment_type', 'caltrans_rate_line',
        )
        .order_by('id')
    )
    serializer_class = EquipmentLineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        work_day_id = self.request.query_params.get('work_day')
        ewo_id = self.request.query_params.get('ewo')
        if work_day_id:
            queryset = queryset.filter(work_day_id=work_day_id)
        elif ewo_id:
            queryset = queryset.filter(work_day__ewo_id=ewo_id)
        return queryset


class MaterialLineViewSet(ParentEwoLockedDeleteMixin, viewsets.ModelViewSet):
    queryset = (
        MaterialLine.objects
        .select_related('work_day', 'work_day__ewo', 'catalog_item')
        .order_by('id')
    )
    serializer_class = MaterialLineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        work_day_id = self.request.query_params.get('work_day')
        ewo_id = self.request.query_params.get('ewo')
        if work_day_id:
            queryset = queryset.filter(work_day_id=work_day_id)
        elif ewo_id:
            queryset = queryset.filter(work_day__ewo_id=ewo_id)
        return queryset
