from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import EquipmentLine, ExtraWorkOrder, LaborLine, MaterialLine, WorkDay


class ExtraWorkOrderSerializer(serializers.ModelSerializer):
    job_number = serializers.CharField(source='job.job_number', read_only=True)
    line_counts = serializers.SerializerMethodField()
    workday_count = serializers.SerializerMethodField()

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
            'fuel_surcharge_pct',
            'labor_subtotal',
            'labor_ohp_amount',
            'equip_mat_subtotal',
            'equip_mat_ohp_amount',
            'fuel_subtotal',
            'bond_amount',
            'total',
            'submitted_at',
            'workday_count',
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
            'fuel_subtotal',
            'bond_amount',
            'total',
            'submitted_at',
            'workday_count',
            'line_counts',
        ]

    def get_workday_count(self, obj):
        return obj.work_days.count()

    def get_line_counts(self, obj):
        """Rolled-up counts across all WorkDays for this EWO."""
        labor = LaborLine.objects.filter(work_day__ewo=obj).count()
        equipment = EquipmentLine.objects.filter(work_day__ewo=obj).count()
        materials = MaterialLine.objects.filter(work_day__ewo=obj).count()
        return {
            'labor': labor,
            'equipment': equipment,
            'materials': materials,
        }

    def validate(self, attrs):
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError(
                'Locked EWOs cannot be edited through CRUD endpoints.'
            )
        if (
            self.instance
            and 'job' in attrs
            and attrs['job'] != self.instance.job
            and self.instance.ewo_number
        ):
            raise serializers.ValidationError({
                'job': 'Job cannot be changed after an EWO number is assigned.'
            })
        return attrs


class WorkDaySerializer(serializers.ModelSerializer):
    ewo_number = serializers.CharField(source='ewo.ewo_number', read_only=True)

    class Meta:
        model = WorkDay
        fields = [
            'id',
            'ewo',
            'ewo_number',
            'work_date',
            'location',
            'weather',
            'description',
            'foreman_name',
            'superintendent_name',
            'labor_subtotal',
            'equip_subtotal',
            'material_subtotal',
            'fuel_amount',
            'labor_ohp_amount',
            'equip_mat_ohp_amount',
            'bond_amount',
            'day_total',
        ]
        read_only_fields = [
            'labor_subtotal',
            'equip_subtotal',
            'material_subtotal',
            'fuel_amount',
            'labor_ohp_amount',
            'equip_mat_ohp_amount',
            'bond_amount',
            'day_total',
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        source_ewo = getattr(self.instance, 'ewo', None)
        target_ewo = attrs.get('ewo') or source_ewo
        if source_ewo and source_ewo.is_locked:
            raise serializers.ValidationError(
                'WorkDays on locked EWOs cannot be edited through CRUD endpoints.'
            )
        if target_ewo and target_ewo.is_locked:
            raise serializers.ValidationError(
                'WorkDays on locked EWOs cannot be edited through CRUD endpoints.'
            )
        return attrs


class LineLockedModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for line items hanging off a WorkDay. CRUD is allowed
    only while the owning EWO remains editable (open or rejected).
    """

    def validate(self, attrs):
        attrs = super().validate(attrs)
        source_work_day = getattr(self.instance, 'work_day', None)
        target_work_day = attrs.get('work_day') or source_work_day

        def _check(wd):
            if wd is not None and wd.ewo_id and wd.ewo.is_locked:
                raise serializers.ValidationError(
                    'Line items on locked EWOs cannot be edited through CRUD endpoints.'
                )

        _check(source_work_day)
        _check(target_work_day)
        return attrs

    def _run_model_validation(self, attrs):
        if self.instance is None:
            instance = self.Meta.model(**attrs)
        else:
            instance = self.instance
            for field, value in attrs.items():
                setattr(instance, field, value)

        if isinstance(instance, LaborLine):
            labor_type = attrs.get('labor_type', getattr(instance, 'labor_type', None))
            employee = attrs.get('employee', getattr(instance, 'employee', None))
            if (
                labor_type == LaborLine.LaborType.NAMED
                and employee is not None
                and not getattr(instance, 'employee_default_trade_id', None)
            ):
                instance.employee_default_trade = employee.trade_classification

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


class LaborLineSerializer(LineLockedModelSerializer):
    ewo_number = serializers.CharField(source='work_day.ewo.ewo_number', read_only=True)
    work_date = serializers.DateField(source='work_day.work_date', read_only=True)

    class Meta:
        model = LaborLine
        fields = [
            'id',
            'work_day',
            'ewo_number',
            'work_date',
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


class EquipmentLineSerializer(LineLockedModelSerializer):
    ewo_number = serializers.CharField(source='work_day.ewo.ewo_number', read_only=True)
    work_date = serializers.DateField(source='work_day.work_date', read_only=True)

    class Meta:
        model = EquipmentLine
        fields = [
            'id',
            'work_day',
            'ewo_number',
            'work_date',
            'equipment_type',
            'caltrans_rate_line',
            'qty',
            'reg_hours',
            'ot_hours',
            'standby_hours',
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


class MaterialLineSerializer(LineLockedModelSerializer):
    ewo_number = serializers.CharField(source='work_day.ewo.ewo_number', read_only=True)
    work_date = serializers.DateField(source='work_day.work_date', read_only=True)

    class Meta:
        model = MaterialLine
        fields = [
            'id',
            'work_day',
            'ewo_number',
            'work_date',
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
