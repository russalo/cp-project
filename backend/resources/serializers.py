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
    """EquipmentType owns its own rates (DEC-060). Caltrans fields are provenance."""
    ct_class_code = serializers.SerializerMethodField()
    ct_class_desc = serializers.SerializerMethodField()
    ct_make_desc = serializers.SerializerMethodField()
    ct_model_desc = serializers.SerializerMethodField()
    ct_schedule_year = serializers.SerializerMethodField()

    class Meta:
        model = EquipmentType
        fields = [
            'id', 'name', 'active',
            'rate_reg', 'rate_ot', 'rate_standby',
            'fuel_surcharge_eligible',
            'ct_match_quality',
            'ct_class_code', 'ct_class_desc', 'ct_make_desc', 'ct_model_desc',
            'ct_schedule_year',
            'notes',
        ]

    def get_ct_class_code(self, obj):
        return obj.caltrans_rate_line.class_code if obj.caltrans_rate_line_id else None

    def get_ct_class_desc(self, obj):
        return obj.caltrans_rate_line.class_desc if obj.caltrans_rate_line_id else None

    def get_ct_make_desc(self, obj):
        return obj.caltrans_rate_line.make_desc if obj.caltrans_rate_line_id else None

    def get_ct_model_desc(self, obj):
        return obj.caltrans_rate_line.model_desc if obj.caltrans_rate_line_id else None

    def get_ct_schedule_year(self, obj):
        return obj.caltrans_rate_line.schedule.schedule_year if obj.caltrans_rate_line_id else None
