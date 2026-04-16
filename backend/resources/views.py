from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Employee, EquipmentType
from .serializers import EmployeeSerializer, EquipmentTypeSerializer


class EmployeeListView(ListAPIView):
    """
    GET /api/resources/employees/
    Returns active employees with today's live labor rates.
    Pass ?active=false to include inactive employees.
    Auth deferred to M4 (DEC-007).
    """
    serializer_class = EmployeeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Employee.objects.select_related('trade_classification').order_by('full_name')
        if self.request.query_params.get('active') == 'false':
            return qs
        return qs.filter(active=True)


class EquipmentTypeListView(ListAPIView):
    """
    GET /api/resources/equipment/
    Returns active equipment types with today's live Caltrans rates.
    Pass ?active=false to include inactive types.
    Auth deferred to M4 (DEC-007).
    """
    serializer_class = EquipmentTypeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = EquipmentType.objects.select_related(
            'caltrans_rate_line__schedule',
        ).order_by('name')
        if self.request.query_params.get('active') == 'false':
            return qs
        return qs.filter(active=True)
