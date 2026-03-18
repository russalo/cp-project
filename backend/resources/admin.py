from django.contrib import admin
from import_export.admin import ImportExportMixin
from unfold.admin import ModelAdmin, TabularInline

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
    list_display = ('code', 'full_name', 'trade_classification', 'active')
    list_filter = ('trade_classification', 'active')
    search_fields = ('code', 'full_name')


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
    list_display = ('name', 'caltrans_rate_line', 'active')
    list_filter = ('active',)
    search_fields = ('name',)
    inlines = [EquipmentUnitInline]


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
