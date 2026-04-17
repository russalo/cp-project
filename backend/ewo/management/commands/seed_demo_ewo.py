"""
Seed a demo EWO so the dev frontend has navigable content.

Creates (idempotently):
  - A demo Job (or reuses one passed via --job-number)
  - One EWO in OPEN status
  - Two WorkDays under that EWO, with a handful of labor / equipment /
    material lines each

Safe to re-run: uses get_or_create keyed to stable natural keys on Job
and EWO description. Lines are not deduped — running multiple times adds
more lines. Use ``--reset`` to wipe prior demo rows first.

Usage:
    python manage.py seed_demo_ewo [--job-number 1886] [--reset]
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ewo.models import (
    EquipmentLine, ExtraWorkOrder, LaborLine, MaterialLine, WorkDay,
)
from ewo.services import create_ewo_from_job
from jobs.models import Job
from resources.models import Employee, EquipmentType, TradeClassification


DEMO_EWO_DESCRIPTION = 'DEMO — bypass line reroute at Sta 12+50'


class Command(BaseCommand):
    help = 'Create a demo Job + EWO + WorkDays + lines for UI development.'

    def add_arguments(self, parser):
        parser.add_argument('--job-number', default='1886',
                            help='Job number to attach the demo EWO to.')
        parser.add_argument('--reset', action='store_true',
                            help='Delete any prior DEMO EWO on that job before seeding.')

    @transaction.atomic
    def handle(self, *args, **opts):
        job_number = opts['job_number']
        reset = opts['reset']

        # Reuse or create the Job.
        job, job_created = Job.objects.get_or_create(
            job_number=job_number,
            defaults={'name': f'Demo Job {job_number}', 'location': 'Demo Site'},
        )
        self.stdout.write(
            f'Job: {"+" if job_created else "~"} {job}  '
            f'(OH&P {job.labor_ohp_pct}/{job.equip_mat_ohp_pct}, bond {job.bond_pct})'
        )

        # Admin user to attribute the EWO to (first superuser, else first user).
        user = (
            User.objects.filter(is_superuser=True).first()
            or User.objects.first()
        )
        if user is None:
            raise CommandError(
                'No User found. Create one first: '
                '`python manage.py createsuperuser`.'
            )

        if reset:
            stale = ExtraWorkOrder.objects.filter(
                job=job, description=DEMO_EWO_DESCRIPTION,
            )
            for e in stale:
                self.stdout.write(f'  - deleting existing demo EWO {e.ewo_number}')
                e.delete()

        # Minimum resources check.
        trade = TradeClassification.objects.filter(name='Operator').first()
        if trade is None:
            raise CommandError(
                'TradeClassification "Operator" not found. '
                'Run `python manage.py ingest_ewo_workbook scratch/EWOexample.xlsx` first.'
            )
        equip_type = (
            EquipmentType.objects.filter(rate_reg__gt=0).first()
        )
        if equip_type is None:
            raise CommandError(
                'No EquipmentType has rate_reg > 0. '
                'Populate one via admin or a Caltrans-link follow-up before seeding.'
            )

        # Create EWO via service so OH&P / bond / fuel % snapshot correctly.
        ewo = create_ewo_from_job(
            job=job,
            created_by=user,
            ewo_type=ExtraWorkOrder.EwoType.TM,
            description=DEMO_EWO_DESCRIPTION,
            bond_required=True,
            fuel_surcharge_pct=Decimal('0.0500'),  # 5%
        )
        self.stdout.write(f'EWO: + {ewo.ewo_number}')

        # Two WorkDays with a similar shape.
        start = date.today() - timedelta(days=1)
        for i, d in enumerate([start, start + timedelta(days=1)]):
            wd = WorkDay.objects.create(
                ewo=ewo,
                work_date=d,
                foreman_name='Larry Gregory',
                superintendent_name='Michael Blough',
                weather='Clear, 74°F',
                location=job.location,
                description=f'Day {i + 1} — demo activity',
            )
            self.stdout.write(f'  WorkDay: + {wd.work_date}')

            # Couple of labor lines.
            LaborLine.objects.create(
                work_day=wd,
                labor_type=LaborLine.LaborType.GENERIC,
                trade_classification=trade,
                reg_hours=Decimal('8.0'),
                ot_hours=Decimal('1.0') if i == 0 else Decimal('0.0'),
                dt_hours=Decimal('0.0'),
            )
            # Optional: one named employee if any exist
            emp = Employee.objects.filter(trade_classification=trade).first()
            if emp:
                LaborLine.objects.create(
                    work_day=wd,
                    labor_type=LaborLine.LaborType.NAMED,
                    employee=emp,
                    trade_classification=trade,
                    reg_hours=Decimal('8.0'),
                    ot_hours=Decimal('0.0'),
                    dt_hours=Decimal('0.0'),
                )

            # One equipment line, mixing reg + standby.
            EquipmentLine.objects.create(
                work_day=wd,
                equipment_type=equip_type,
                qty=2 if i == 0 else 1,
                reg_hours=Decimal('8.0'),
                ot_hours=Decimal('0.0'),
                standby_hours=Decimal('1.0') if i == 0 else Decimal('0.0'),
            )

            # One material line.
            MaterialLine.objects.create(
                work_day=wd,
                description='PVC Pipe 6" SDR-35',
                quantity=Decimal('120.000' if i == 0 else '80.000'),
                unit='LF',
                unit_cost=Decimal('12.50'),
                is_subcontractor=False,
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeded: EWO {ewo.ewo_number} under job {job.job_number} '
            f'with 2 WorkDays. Visit /ewos/{ewo.pk}/ in the UI.'
        ))
