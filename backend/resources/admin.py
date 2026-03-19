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
    fields = ('class_code', 'make_code', 'model_code', 'rental_rate', 'rw_delay_rate', 'overtime_rate', 'unit')
    show_change_link = True


@admin.register(CaltransSchedule)
class CaltransScheduleAdmin(ModelAdmin):
    list_display = ('schedule_year', 'effective_date', 'expiry_date', 'source_file')
    inlines = [CaltransRateLineInline]


@admin.register(CaltransRateLine)
class CaltransRateLineAdmin(ImportExportMixin, ModelAdmin):
    list_display = ('class_code', 'make_code', 'model_code', 'rental_rate', 'rw_delay_rate', 'overtime_rate', 'unit', 'schedule')
    list_filter = ('schedule', 'class_code', 'unit')
    search_fields = ('class_code', 'class_desc', 'make_code', 'make_desc', 'model_code', 'model_desc')


class EquipmentUnitInline(TabularInline):
    model = EquipmentUnit
    extra = 0
    fields = ('internal_code', 'description', 'ownership', 'active')


@admin.register(EquipmentType)
class EquipmentTypeAdmin(ModelAdmin):
    list_display = ('name', 'current_rates_display', 'active')
    list_filter = ('active',)
    search_fields = ('name',)
    inlines = [EquipmentUnitInline]

    @admin.display(description='Oper / Stby / OT Rates')
    def current_rates_display(self, obj):
        import datetime
        from ewo.services import get_equipment_rates
        try:
            rl = get_equipment_rates(obj, datetime.date.today())
            return f'${rl.rental_rate} / ${rl.rw_delay_rate} + ${rl.overtime_rate} OT ({rl.unit})'
        except ValueError:
            return '— no Caltrans rate linked —'


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
