"""
EWO calculation services — the single boundary for all currency arithmetic.

All money math lives here. Never perform currency calculations in views,
serializers, or models. Use decimal.ROUND_UP at every calculation step
per DEC-023. See DEC-003 and DEC-031 for the calculation timing policy.
"""
