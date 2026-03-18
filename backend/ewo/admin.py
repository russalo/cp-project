from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import EquipmentLine, ExtraWorkOrder, LaborLine, MaterialLine


class LaborLineInline(TabularInline):
    model = LaborLine
    extra = 0
    fields = (
        'labor_type', 'employee', 'trade_classification',
        'reg_hours', 'ot_hours', 'dt_hours',
        'trade_override_reason', 'line_total',
    )
    readonly_fields = ('line_total',)
    show_change_link = True


class EquipmentLineInline(TabularInline):
    model = EquipmentLine
    extra = 0
    fields = ('equipment_type', 'usage_type', 'hours', 'unit', 'line_total')
    readonly_fields = ('line_total',)
    show_change_link = True


class MaterialLineInline(TabularInline):
    model = MaterialLine
    extra = 0
    fields = ('description', 'quantity', 'unit', 'unit_cost', 'line_total', 'is_subcontractor', 'reference_number')
    readonly_fields = ('line_total',)
    show_change_link = True


@admin.register(ExtraWorkOrder)
class ExtraWorkOrderAdmin(ModelAdmin):
    list_display = ('ewo_number', 'job', 'ewo_type', 'work_date', 'status', 'total', 'created_by')
    list_filter = ('status', 'ewo_type', 'work_date')
    search_fields = ('ewo_number', 'job__job_number', 'job__name', 'description')
    readonly_fields = (
        'ewo_number', 'ewo_sequence', 'revision',
        'labor_subtotal', 'labor_ohp_amount',
        'equip_mat_subtotal', 'equip_mat_ohp_amount',
        'bond_amount', 'total', 'submitted_at',
    )
    inlines = [LaborLineInline, EquipmentLineInline, MaterialLineInline]
    fieldsets = (
        ('EWO Identity', {
            'fields': (
                'ewo_number', 'job', 'created_by', 'ewo_type',
                'work_date', 'status', 'parent_ewo', 'revision',
            )
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('GC Acknowledgment', {
            'fields': ('gc_ack_name', 'gc_ack_date', 'gc_ack_method'),
        }),
        ('Cross References', {
            'fields': ('rfi_reference', 'addendum_ref', 'plan_revision'),
            'classes': ('collapse',),
        }),
        ('Markup', {
            'fields': ('labor_ohp_pct', 'equip_mat_ohp_pct', 'bond_pct', 'bond_required'),
        }),
        ('Totals (computed at submission)', {
            'fields': (
                'labor_subtotal', 'labor_ohp_amount',
                'equip_mat_subtotal', 'equip_mat_ohp_amount',
                'bond_amount', 'total', 'submitted_at',
            ),
        }),
    )


@admin.register(LaborLine)
class LaborLineAdmin(ModelAdmin):
    list_display = ('ewo', 'labor_type', 'employee', 'trade_classification', 'reg_hours', 'ot_hours', 'dt_hours', 'line_total')
    list_filter = ('labor_type', 'trade_classification')
    search_fields = ('ewo__ewo_number', 'employee__full_name', 'employee__code')
    readonly_fields = ('line_total', 'rate_reg_snapshot', 'rate_ot_snapshot', 'rate_dt_snapshot')


@admin.register(EquipmentLine)
class EquipmentLineAdmin(ModelAdmin):
    list_display = ('ewo', 'equipment_type', 'usage_type', 'hours', 'unit', 'line_total')
    list_filter = ('usage_type', 'equipment_type')
    search_fields = ('ewo__ewo_number', 'equipment_type__name')
    readonly_fields = ('line_total', 'rental_rate_snapshot', 'rw_delay_rate_snapshot', 'ot_rate_snapshot')


@admin.register(MaterialLine)
class MaterialLineAdmin(ModelAdmin):
    list_display = ('ewo', 'description', 'quantity', 'unit', 'unit_cost', 'line_total', 'is_subcontractor')
    list_filter = ('is_subcontractor',)
    search_fields = ('ewo__ewo_number', 'description', 'reference_number')
    readonly_fields = ('line_total',)
