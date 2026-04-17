from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'id', 'job_number', 'name', 'location', 'gc_name', 'active',
            # Phase 2 fields — snapshot onto each new EWO at creation (DEC-063).
            # Exposed so the detail page can show CP's current defaults.
            'cp_role',
            'labor_ohp_pct', 'equip_mat_ohp_pct', 'bond_pct',
        ]
