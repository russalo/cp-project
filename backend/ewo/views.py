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
from .services import (
    calculate_equipment_line,
    calculate_labor_line,
    calculate_material_line,
    rollup_ewo_totals,
)


logger = logging.getLogger(__name__)


_LINE_CALCULATORS = {
    LaborLine: calculate_labor_line,
    EquipmentLine: calculate_equipment_line,
    MaterialLine: calculate_material_line,
}


def _recompute_line_if_editable(line):
    """
    Re-snapshot rates + line_total for a single line. Dispatches by model.

    Skipped on locked EWOs. Rate-lookup failures are logged but not raised
    — matches ``_recalc_if_editable``'s tolerance so a missing LaborRate
    or unconfigured EquipmentType doesn't block the CRUD call. The line is
    saved with whatever the request supplied; line_total stays stale until
    rates are set and the next recalc succeeds.
    """
    ewo = line.work_day.ewo
    if getattr(ewo, 'is_locked', True):
        return
    try:
        _LINE_CALCULATORS[type(line)](line)
    except ValueError as exc:
        logger.warning(
            'line recompute skipped on EWO %s (%s): %s',
            ewo.ewo_number, type(line).__name__, exc,
        )


def _recalc_if_editable(ewo):
    """
    Roll up WorkDay + EWO totals whenever an editable EWO's line items
    change. Skipped on locked EWOs so frozen numbers stay frozen (DEC-031).

    Uses ``rollup_ewo_totals`` rather than ``calculate_ewo_totals`` so the
    per-line recompute pass doesn't re-save every sibling line (which
    would produce an audit-history row on each untouched line via
    django-simple-history). The line that actually changed is recomputed
    in the viewset's ``perform_create`` / ``perform_update`` before the
    rollup runs.

    Rate-lookup failures (missing LaborRate for a work_date, or an
    EquipmentType without rates configured) surface as ``ValueError`` from
    the services layer. They're logged but not re-raised — the CRUD call
    already succeeded with a 2xx; raising from a post-save hook would
    confuse the user. Totals remain at their previous value until the
    next successful recalc or submit.
    """
    if ewo is None or getattr(ewo, 'is_locked', True):
        return
    try:
        rollup_ewo_totals(ewo)
    except ValueError as exc:
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
        _recompute_line_if_editable(serializer.instance)
        _recalc_if_editable(serializer.instance.work_day.ewo)

    def perform_update(self, serializer):
        # Capture the original parent EWO before save so a cross-EWO move
        # (line reassigned to a WorkDay on a different EWO) refreshes both
        # sides — otherwise the source EWO's totals stay stale.
        old_ewo = serializer.instance.work_day.ewo
        serializer.save()
        _recompute_line_if_editable(serializer.instance)
        new_ewo = serializer.instance.work_day.ewo
        _recalc_if_editable(new_ewo)
        if old_ewo.pk != new_ewo.pk:
            _recalc_if_editable(old_ewo)

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
        # Capture the original parent EWO before save; reassigning a
        # WorkDay to a different EWO has to rollup the source side too,
        # not just the destination.
        old_ewo = serializer.instance.ewo
        serializer.save()
        new_ewo = serializer.instance.ewo
        _recalc_if_editable(new_ewo)
        if old_ewo.pk != new_ewo.pk:
            _recalc_if_editable(old_ewo)

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
