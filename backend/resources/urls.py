from django.urls import path

from . import views

urlpatterns = [
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('equipment/', views.EquipmentTypeListView.as_view(), name='equipment-list'),
    path('trades/', views.TradeClassificationListView.as_view(), name='trade-list'),
    path('materials/', views.MaterialCatalogListView.as_view(), name='material-list'),
]
