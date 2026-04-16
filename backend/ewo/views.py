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


class EwoLockedDeleteMixin:
    def perform_destroy(self, instance):
        if getattr(instance, 'is_locked', False):
            raise ValidationError('Locked EWOs cannot be deleted through CRUD endpoints.')
        super().perform_destroy(instance)


class ParentEwoLockedDeleteMixin:
    """Guard for line-item viewsets whose parent is a WorkDay under an EWO."""
    def perform_destroy(self, instance):
        if instance.work_day.ewo.is_locked:
            raise ValidationError(
                'Line items on locked EWOs cannot be deleted through CRUD endpoints.'
            )
        super().perform_destroy(instance)


class WorkDayLockedDeleteMixin:
    def perform_destroy(self, instance):
        if instance.ewo.is_locked:
            raise ValidationError(
                'WorkDays on locked EWOs cannot be deleted through CRUD endpoints.'
            )
        super().perform_destroy(instance)


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
        if job_id:
            qs = qs.filter(job_id=job_id)
        if status_:
            qs = qs.filter(status=status_)
        return qs


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
