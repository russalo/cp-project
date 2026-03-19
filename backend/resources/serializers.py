import datetime

from rest_framework import serializers

from .models import Employee, EquipmentType


def _labor_rate_for(trade_classification, context):
    """Return LaborRate for trade on today's date, cached by trade pk in serializer context."""
    cache = context.setdefault('_lr_cache', {})
    tc_id = trade_classification.pk
    if tc_id not in cache:
        try:
            from ewo.services import get_labor_rate
            cache[tc_id] = get_labor_rate(trade_classification, datetime.date.today())
        except ValueError:
            cache[tc_id] = None
    return cache[tc_id]


def _equipment_rate_for(equipment_type, context):
    """Return CaltransRateLine for equipment type on today's date, cached by type pk in context."""
    cache = context.setdefault('_er_cache', {})
    et_id = equipment_type.pk
    if et_id not in cache:
        try:
            from ewo.services import get_equipment_rates
            cache[et_id] = get_equipment_rates(equipment_type, datetime.date.today())
        except ValueError:
            cache[et_id] = None
    return cache[et_id]


class EmployeeSerializer(serializers.ModelSerializer):
    trade_name = serializers.SerializerMethodField()
    union_abbrev = serializers.SerializerMethodField()
    rate_reg = serializers.SerializerMethodField()
    rate_ot = serializers.SerializerMethodField()
    rate_dt = serializers.SerializerMethodField()
    rate_effective_date = serializers.SerializerMethodField()
    rate_available = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'code', 'full_name', 'active',
            'trade_name', 'union_abbrev',
            'rate_reg', 'rate_ot', 'rate_dt',
            'rate_effective_date', 'rate_available',
        ]

    def get_trade_name(self, obj):
        return obj.trade_classification.name

    def get_union_abbrev(self, obj):
        return obj.trade_classification.union_abbrev

    def get_rate_reg(self, obj):
        rate = _labor_rate_for(obj.trade_classification, self.context)
        return str(rate.rate_reg) if rate else None

    def get_rate_ot(self, obj):
        rate = _labor_rate_for(obj.trade_classification, self.context)
        return str(rate.rate_ot) if rate else None

    def get_rate_dt(self, obj):
        rate = _labor_rate_for(obj.trade_classification, self.context)
        return str(rate.rate_dt) if rate else None

    def get_rate_effective_date(self, obj):
        rate = _labor_rate_for(obj.trade_classification, self.context)
        return str(rate.effective_date) if rate else None

    def get_rate_available(self, obj):
        return _labor_rate_for(obj.trade_classification, self.context) is not None


class EquipmentTypeSerializer(serializers.ModelSerializer):
    class_code = serializers.SerializerMethodField()
    class_desc = serializers.SerializerMethodField()
    make_desc = serializers.SerializerMethodField()
    model_desc = serializers.SerializerMethodField()
    rental_rate = serializers.SerializerMethodField()
    rw_delay_rate = serializers.SerializerMethodField()
    overtime_rate = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    rate_available = serializers.SerializerMethodField()

    class Meta:
        model = EquipmentType
        fields = [
            'id', 'name', 'active',
            'class_code', 'class_desc', 'make_desc', 'model_desc',
            'rental_rate', 'rw_delay_rate', 'overtime_rate', 'unit',
            'rate_available',
        ]

    def get_class_code(self, obj):
        rl = _equipment_rate_for(obj, self.context)
        return rl.class_code if rl else None

    def get_class_desc(self, obj):
        rl = _equipment_rate_for(obj, self.context)
        return rl.class_desc if rl else None

    def get_make_desc(self, obj):
        rl = _equipment_rate_for(obj, self.context)
        return rl.make_desc if rl else None

    def get_model_desc(self, obj):
        rl = _equipment_rate_for(obj, self.context)
        return rl.model_desc if rl else None

    def get_rental_rate(self, obj):
        rl = _equipment_rate_for(obj, self.context)
        return str(rl.rental_rate) if rl else None

    def get_rw_delay_rate(self, obj):
        rl = _equipment_rate_for(obj, self.context)
        return str(rl.rw_delay_rate) if rl else None

    def get_overtime_rate(self, obj):
        rl = _equipment_rate_for(obj, self.context)
        return str(rl.overtime_rate) if rl else None

    def get_unit(self, obj):
        rl = _equipment_rate_for(obj, self.context)
        return rl.unit if rl else None

    def get_rate_available(self, obj):
        return _equipment_rate_for(obj, self.context) is not None
