from django.urls import path

from . import views

urlpatterns = [
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('equipment/', views.EquipmentTypeListView.as_view(), name='equipment-list'),
]
