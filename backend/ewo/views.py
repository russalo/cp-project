from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import EquipmentLine, ExtraWorkOrder, LaborLine, MaterialLine
from .serializers import (
    EquipmentLineSerializer,
    ExtraWorkOrderSerializer,
    LaborLineSerializer,
    MaterialLineSerializer,
)


class EwoLockedDeleteMixin:
    def perform_destroy(self, instance):
        if getattr(instance, 'is_locked', False):
            from rest_framework.exceptions import ValidationError

            raise ValidationError('Locked EWOs cannot be deleted through CRUD endpoints.')
        super().perform_destroy(instance)


class ParentEwoLockedDeleteMixin:
    def perform_destroy(self, instance):
        if instance.ewo.is_locked:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                'Line items on locked EWOs cannot be deleted through CRUD endpoints.'
            )
        super().perform_destroy(instance)


class ExtraWorkOrderViewSet(EwoLockedDeleteMixin, viewsets.ModelViewSet):
    """
    CRUD-only EWO API. Lifecycle transitions stay out of this viewset so submit/
    approval behavior can be implemented explicitly later.
    """

    queryset = (
        ExtraWorkOrder.objects
        .select_related('job', 'created_by', 'parent_ewo')
        .order_by('-work_date', 'ewo_number')
    )
    serializer_class = ExtraWorkOrderSerializer
    permission_classes = [AllowAny]


class LaborLineViewSet(ParentEwoLockedDeleteMixin, viewsets.ModelViewSet):
    queryset = (
        LaborLine.objects
        .select_related('ewo', 'employee', 'employee_default_trade', 'trade_classification')
        .order_by('id')
    )
    serializer_class = LaborLineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        ewo_id = self.request.query_params.get('ewo')
        if ewo_id:
            queryset = queryset.filter(ewo_id=ewo_id)
        return queryset


class EquipmentLineViewSet(ParentEwoLockedDeleteMixin, viewsets.ModelViewSet):
    queryset = (
        EquipmentLine.objects
        .select_related('ewo', 'equipment_type', 'caltrans_rate_line')
        .order_by('id')
    )
    serializer_class = EquipmentLineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        ewo_id = self.request.query_params.get('ewo')
        if ewo_id:
            queryset = queryset.filter(ewo_id=ewo_id)
        return queryset


class MaterialLineViewSet(ParentEwoLockedDeleteMixin, viewsets.ModelViewSet):
    queryset = (
        MaterialLine.objects
        .select_related('ewo', 'catalog_item')
        .order_by('id')
    )
    serializer_class = MaterialLineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        ewo_id = self.request.query_params.get('ewo')
        if ewo_id:
            queryset = queryset.filter(ewo_id=ewo_id)
        return queryset
