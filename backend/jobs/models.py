import re

from django.core.exceptions import ValidationError
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


class Job(models.Model):
    """
    Lightweight job reference for v1.
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

    history = HistoricalRecords()

    class Meta:
        ordering = ['-job_number']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    def __str__(self):
        return f'{self.job_number} — {self.name}'
