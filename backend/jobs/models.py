import re
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

# DEC-019: two valid job number formats
_JOB_NUMBER_REGULAR = re.compile(r'^\d+$')        # plain integer: 1886, 42
_JOB_NUMBER_SMALL = re.compile(r'^\d{2}[A-Z]+$')  # year + letters: 26A, 26AA


def validate_job_number(value):
    if not (_JOB_NUMBER_REGULAR.match(value) or _JOB_NUMBER_SMALL.match(value)):
        raise ValidationError(
            'Job number must be a plain integer (e.g. 1886) '
            'or a 2-digit year followed by letters (e.g. 26A, 26AA).'
        )


# Shared validators for per-job markup percentages (0.0000–1.0000)
_MARKUP_VALIDATORS = [MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))]


class Job(models.Model):
    """
    Lightweight job reference for v1.

    Job carries contract-driven billing defaults (DEC-063) that snapshot
    onto every new EWO for this job. A Contract model will eventually own
    these (see DEC-045 / DEC-068); until then, Job is the interim home.

    Full Customer / JobSite / Location hierarchy is deferred to a future
    milestone per DEC-011. This model will expand then.
    """
    job_number = models.CharField(
        max_length=20, unique=True, validators=[validate_job_number]
    )
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    gc_name = models.CharField(max_length=200, blank=True, verbose_name='General Contractor')
    active = models.BooleanField(default=True)

    # CP's contract-chain role on this job — interim placement until a
    # dedicated Contract model lands (DEC-068). Choices will be filled in
    # when the user supplies the 5 configurations from CLAUDE.md; until
    # then, stored as free-text to unblock.
    cp_role = models.CharField(max_length=30, blank=True)

    # Contractor OH&P and bond defaults — snapshotted to EWO at creation (DEC-063).
    # 0.15 / 0.15 / 0.015 are CP's standing defaults; editable per-job.
    labor_ohp_pct = models.DecimalField(
        max_digits=5, decimal_places=4,
        default=Decimal('0.1500'),
        validators=_MARKUP_VALIDATORS,
        verbose_name='Labor OH&P %',
    )
    equip_mat_ohp_pct = models.DecimalField(
        max_digits=5, decimal_places=4,
        default=Decimal('0.1500'),
        validators=_MARKUP_VALIDATORS,
        verbose_name='Equipment & Materials OH&P %',
    )
    bond_pct = models.DecimalField(
        max_digits=5, decimal_places=4,
        default=Decimal('0.0150'),
        validators=_MARKUP_VALIDATORS,
        verbose_name='Bond %',
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ['-job_number']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    def __str__(self):
        return f'{self.job_number} — {self.name}'
