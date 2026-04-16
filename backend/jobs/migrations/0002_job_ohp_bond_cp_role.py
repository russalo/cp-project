"""
Job defaults for OH&P, bond, and CP contract role (DEC-063, DEC-068).
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


_MARKUP_VALIDATORS = [MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))]


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='cp_role',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='job',
            name='labor_ohp_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.1500'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Labor OH&P %',
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='equip_mat_ohp_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.1500'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Equipment & Materials OH&P %',
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='bond_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.0150'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Bond %',
            ),
        ),
        migrations.AddField(
            model_name='historicaljob',
            name='cp_role',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='historicaljob',
            name='labor_ohp_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.1500'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Labor OH&P %',
            ),
        ),
        migrations.AddField(
            model_name='historicaljob',
            name='equip_mat_ohp_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.1500'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Equipment & Materials OH&P %',
            ),
        ),
        migrations.AddField(
            model_name='historicaljob',
            name='bond_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.0150'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Bond %',
            ),
        ),
    ]
