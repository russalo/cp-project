from rest_framework.routers import DefaultRouter

from .views import (
    EquipmentLineViewSet,
    ExtraWorkOrderViewSet,
    LaborLineViewSet,
    MaterialLineViewSet,
)

router = DefaultRouter()
router.register('ewos', ExtraWorkOrderViewSet, basename='ewo')
router.register('labor-lines', LaborLineViewSet, basename='labor-line')
router.register('equipment-lines', EquipmentLineViewSet, basename='equipment-line')
router.register('material-lines', MaterialLineViewSet, basename='material-line')

urlpatterns = router.urls
