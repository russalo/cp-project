from django.contrib import admin
from import_export.admin import ImportExportMixin
from unfold.admin import ModelAdmin, TabularInline
import datetime
from ewo.services import get_labor_rate

from .models import (
    CaltransRateLine,
    CaltransSchedule,
    Employee,
    EquipmentType,
    EquipmentUnit,
    LaborRate,
    MaterialCatalog,
    MaterialCategory,
    TradeClassification,
)

EMPLOYEE_MODEL_CODES = {'Employee', 'TradeClassification', 'LaborRate'}
EQUIPMENT_MODEL_CODES = {'EquipmentType', 'EquipmentUnit', 'CaltransSchedule', 'CaltransRateLine'}
MATERIAL_MODEL_CODES = {'MaterialCategory', 'MaterialCatalog'}


@admin.register(TradeClassification)
class TradeClassificationAdmin(ModelAdmin):
    list_display = ('name', 'union_abbrev', 'union_name', 'active')
    list_filter = ('union_abbrev', 'active')
    search_fields = ('name', 'union_name', 'union_abbrev')


class LaborRateInline(TabularInline):
    model = LaborRate
    extra = 0
    fields = ('effective_date', 'expiry_date', 'rate_reg', 'rate_ot', 'rate_dt', 'notes')
    ordering = ('-effective_date',)


@admin.register(LaborRate)
class LaborRateAdmin(ModelAdmin):
    list_display = ('trade_classification', 'effective_date', 'expiry_date', 'rate_reg', 'rate_ot', 'rate_dt')
    list_filter = ('trade_classification',)
    ordering = ('trade_classification', '-effective_date')


@admin.register(Employee)
class EmployeeAdmin(ImportExportMixin, ModelAdmin):
    list_display = ('code', 'full_name', 'trade_classification', 'current_rates_display', 'active')
    list_filter = ('trade_classification', 'active')
    search_fields = ('code', 'full_name')

    @admin.display(description='Current Rates (Reg / OT / DT)')
    def current_rates_display(self, obj):
        """
        Display the current labor rates for the employee's trade classification.

        Results are memoized per-request on the admin instance by trade_classification_id
        to avoid repeated lookups (and database queries) for employees sharing the same
        trade classification on the changelist.
        """
        # Initialize the per-request cache lazily.
        if not hasattr(self, '_current_rate_cache'):
            self._current_rate_cache = {}

        trade_classification_id = obj.trade_classification_id

        # Return cached result if available.
        if trade_classification_id in self._current_rate_cache:
            rate = self._current_rate_cache[trade_classification_id]
        else:
            try:
                rate = get_labor_rate(obj.trade_classification, datetime.date.today())
            except ValueError:
                # Cache the absence of a rate as None to avoid repeated failed lookups.
                self._current_rate_cache[trade_classification_id] = None
                return '— no rate on file —'
            else:
                self._current_rate_cache[trade_classification_id] = rate

        if rate is None:
            return '— no rate on file —'

        return f'${rate.rate_reg} / ${rate.rate_ot} / ${rate.rate_dt}'


class CaltransRateLineInline(TabularInline):
    model = CaltransRateLine
    extra = 0
    fields = ('class_code', 'make_code', 'model_code', 'rental_rate', 'rw_delay_factor', 'ot_factor', 'unit')
    show_change_link = True


@admin.register(CaltransSchedule)
class CaltransScheduleAdmin(ModelAdmin):
    list_display = ('schedule_year', 'effective_date', 'expiry_date', 'source_file')
    inlines = [CaltransRateLineInline]


@admin.register(CaltransRateLine)
class CaltransRateLineAdmin(ImportExportMixin, ModelAdmin):
    list_display = ('class_code', 'make_code', 'model_code', 'rental_rate', 'rw_delay_factor', 'ot_factor', 'unit', 'schedule')
    list_filter = ('schedule', 'class_code', 'unit')
    search_fields = ('class_code', 'class_desc', 'make_code', 'make_desc', 'model_code', 'model_desc')


class EquipmentUnitInline(TabularInline):
    model = EquipmentUnit
    extra = 0
    fields = ('internal_code', 'description', 'ownership', 'active')


@admin.register(EquipmentType)
class EquipmentTypeAdmin(ImportExportMixin, ModelAdmin):
    list_display = (
        'name', 'description', 'category', 'current_rates_display',
        'fuel_surcharge_eligible', 'ct_match_quality', 'active',
    )
    list_filter = ('active', 'category', 'ct_match_quality', 'fuel_surcharge_eligible')
    search_fields = ('name', 'description', 'category', 'caltrans_rate_line__class_code')
    inlines = [EquipmentUnitInline]
    fields = (
        'name', 'description', 'category', 'active',
        'rate_reg', 'rate_ot', 'rate_standby',
        'fuel_surcharge_eligible',
        'ct_match_quality', 'caltrans_rate_line',
        'notes',
    )
    autocomplete_fields = ('caltrans_rate_line',)

    @admin.display(description='Rates (Reg / OT / Stby)')
    def current_rates_display(self, obj):
        return f'${obj.rate_reg} / ${obj.rate_ot} / ${obj.rate_standby}'


@admin.register(EquipmentUnit)
class EquipmentUnitAdmin(ModelAdmin):
    list_display = ('internal_code', 'description', 'equipment_type', 'ownership', 'active')
    list_filter = ('equipment_type', 'ownership', 'active')
    search_fields = ('internal_code', 'description')


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(ModelAdmin):
    list_display = ('name', 'active')
    list_filter = ('active',)


@admin.register(MaterialCatalog)
class MaterialCatalogAdmin(ModelAdmin):
    list_display = ('description', 'category', 'default_unit', 'last_unit_cost', 'last_cost_date', 'use_count', 'is_boilerplate', 'active')
    list_filter = ('category', 'is_boilerplate', 'active')
    search_fields = ('description',)


# ==============================================================================
# Override the Admin Site index page to organize resources into groups
# ==============================================================================
def custom_get_app_list(self, request, app_label=None):
    """
    Groups the models in the 'resources' app into 'Employee', 'Equipment',
    and 'Materials' sections on the Django Admin index page (dashboard).
    """
    app_dict = self._build_app_dict(request, app_label)

    # Standard ordering by verbose_name
    app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

    for app in app_list:
        app['models'].sort(key=lambda x: x['name'])

    new_app_list = []
    for app in app_list:
        if app['app_label'] == 'resources':
            employee_models = []
            equipment_models = []
            material_models = []

            for m in app['models']:
                group = _resource_group_for_model(m)
                if group == 'employee':
                    employee_models.append(m)
                elif group == 'equipment':
                    equipment_models.append(m)
                else:
                    material_models.append(m)

            # Add them as distinct pseudo-apps
            if employee_models:
                new_app_list.append({
                    'name': 'Employee',
                    'app_label': 'resources_employee',
                    'app_url': '',
                    'has_module_perms': True,
                    'models': employee_models,
                })
            if equipment_models:
                new_app_list.append({
                    'name': 'Equipment',
                    'app_label': 'resources_equipment',
                    'app_url': '',
                    'has_module_perms': True,
                    'models': equipment_models,
                })
            if material_models:
                new_app_list.append({
                    'name': 'Materials',
                    'app_label': 'resources_materials',
                    'app_url': '',
                    'has_module_perms': True,
                    'models': material_models,
                })
        else:
            new_app_list.append(app)

    return new_app_list

# Monkey-patch the bound method onto the admin.site instance
admin.site.get_app_list = custom_get_app_list.__get__(admin.site)
def _resource_group_for_model(model_dict):
    code = model_dict.get('object_name', '')
    admin_url = model_dict.get('admin_url', '')

    if code in EMPLOYEE_MODEL_CODES:
        return 'employee'
    if code in EQUIPMENT_MODEL_CODES:
        return 'equipment'
    if code in MATERIAL_MODEL_CODES:
        return 'material'

    if not code:
        if any(token in admin_url for token in ('tradeclassification', 'employee', 'laborrate')):
            return 'employee'
        if any(token in admin_url for token in ('equipment', 'caltrans')):
            return 'equipment'
        if 'material' in admin_url:
            return 'material'

    raise ValueError(f'Unhandled resources admin model grouping for: {model_dict!r}')
