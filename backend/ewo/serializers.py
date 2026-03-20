from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import EquipmentLine, ExtraWorkOrder, LaborLine, MaterialLine


class ExtraWorkOrderSerializer(serializers.ModelSerializer):
    job_number = serializers.CharField(source='job.job_number', read_only=True)
    line_counts = serializers.SerializerMethodField()

    class Meta:
        model = ExtraWorkOrder
        fields = [
            'id',
            'ewo_number',
            'ewo_sequence',
            'job',
            'job_number',
            'created_by',
            'parent_ewo',
            'revision',
            'ewo_type',
            'work_date',
            'description',
            'status',
            'gc_ack_name',
            'gc_ack_date',
            'gc_ack_method',
            'rfi_reference',
            'addendum_ref',
            'plan_revision',
            'labor_ohp_pct',
            'equip_mat_ohp_pct',
            'bond_pct',
            'bond_required',
            'labor_subtotal',
            'labor_ohp_amount',
            'equip_mat_subtotal',
            'equip_mat_ohp_amount',
            'bond_amount',
            'total',
            'submitted_at',
            'line_counts',
        ]
        read_only_fields = [
            'ewo_number',
            'ewo_sequence',
            'parent_ewo',
            'revision',
            'status',
            'labor_subtotal',
            'labor_ohp_amount',
            'equip_mat_subtotal',
            'equip_mat_ohp_amount',
            'bond_amount',
            'total',
            'submitted_at',
            'line_counts',
        ]

    def get_line_counts(self, obj):
        labor_count = getattr(obj, 'labor_count', None)
        if labor_count is None:
            labor_count = obj.labor_lines.count()

        equipment_count = getattr(obj, 'equipment_count', None)
        if equipment_count is None:
            equipment_count = obj.equipment_lines.count()

        materials_count = getattr(obj, 'materials_count', None)
        if materials_count is None:
            materials_count = obj.material_lines.count()

        return {
            'labor': labor_count,
            'equipment': equipment_count,
            'materials': materials_count,
        }

    def validate(self, attrs):
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError(
                'Locked EWOs cannot be edited through CRUD endpoints.'
            )
        return attrs


class EwoLockedModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for line items. CRUD is allowed only while the parent EWO
    remains editable (`open` or `rejected`).
    """

    def validate(self, attrs):
        attrs = super().validate(attrs)
        ewo = attrs.get('ewo') or getattr(self.instance, 'ewo', None)
        if ewo and ewo.is_locked:
            raise serializers.ValidationError(
                'Line items on locked EWOs cannot be edited through CRUD endpoints.'
            )
        return attrs

    def _run_model_validation(self, attrs):
        if self.instance is None:
            instance = self.Meta.model(**attrs)
        else:
            instance = self.instance
            for field, value in attrs.items():
                setattr(instance, field, value)

        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict or exc.messages) from exc

    def create(self, validated_data):
        self._run_model_validation(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._run_model_validation(validated_data)
        return super().update(instance, validated_data)


class LaborLineSerializer(EwoLockedModelSerializer):
    ewo_number = serializers.CharField(source='ewo.ewo_number', read_only=True)

    class Meta:
        model = LaborLine
        fields = [
            'id',
            'ewo',
            'ewo_number',
            'labor_type',
            'employee',
            'employee_default_trade',
            'trade_classification',
            'trade_override_reason',
            'reg_hours',
            'ot_hours',
            'dt_hours',
            'rate_reg_snapshot',
            'rate_ot_snapshot',
            'rate_dt_snapshot',
            'line_total',
        ]
        read_only_fields = [
            'employee_default_trade',
            'rate_reg_snapshot',
            'rate_ot_snapshot',
            'rate_dt_snapshot',
            'line_total',
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        labor_type = attrs.get('labor_type', getattr(self.instance, 'labor_type', None))
        employee = attrs.get('employee', getattr(self.instance, 'employee', None))
        if labor_type == LaborLine.LaborType.NAMED and employee is None:
            raise serializers.ValidationError({
                'employee': 'Named labor lines require an employee.'
            })
        if labor_type == LaborLine.LaborType.GENERIC and employee is not None:
            raise serializers.ValidationError({
                'employee': 'Generic labor lines cannot reference a specific employee.'
            })
        return attrs


class EquipmentLineSerializer(EwoLockedModelSerializer):
    ewo_number = serializers.CharField(source='ewo.ewo_number', read_only=True)

    class Meta:
        model = EquipmentLine
        fields = [
            'id',
            'ewo',
            'ewo_number',
            'equipment_type',
            'caltrans_rate_line',
            'usage_type',
            'hours',
            'unit',
            'rental_rate_snapshot',
            'rw_delay_rate_snapshot',
            'ot_rate_snapshot',
            'line_total',
        ]
        read_only_fields = [
            'caltrans_rate_line',
            'rental_rate_snapshot',
            'rw_delay_rate_snapshot',
            'ot_rate_snapshot',
            'line_total',
        ]


class MaterialLineSerializer(EwoLockedModelSerializer):
    ewo_number = serializers.CharField(source='ewo.ewo_number', read_only=True)

    class Meta:
        model = MaterialLine
        fields = [
            'id',
            'ewo',
            'ewo_number',
            'catalog_item',
            'description',
            'quantity',
            'unit',
            'unit_cost',
            'line_total',
            'is_subcontractor',
            'reference_number',
        ]
        read_only_fields = ['line_total']
