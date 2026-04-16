from rest_framework import viewsets

from .models import Employee, EquipmentType
from .serializers import EmployeeSerializer, EquipmentTypeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class EquipmentTypeViewSet(viewsets.ModelViewSet):
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer
