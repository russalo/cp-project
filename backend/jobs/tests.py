from datetime import date

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from ewo.models import ExtraWorkOrder

from .models import Job


class JobApiTests(APITestCase):
    def test_list_returns_only_active_jobs_by_default(self):
        active_job = Job.objects.create(job_number='1886', name='Mainline Sewer', active=True)
        Job.objects.create(job_number='26AA', name='Small Repair', active=False)

        response = self.client.get('/api/jobs/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [
            {
                'id': active_job.id,
                'job_number': '1886',
                'name': 'Mainline Sewer',
                'location': '',
                'gc_name': '',
                'active': True,
            }
        ])

    def test_list_can_include_inactive_jobs(self):
        Job.objects.create(job_number='1886', name='Mainline Sewer', active=True)
        Job.objects.create(job_number='26AA', name='Small Repair', active=False)

        response = self.client.get('/api/jobs/?active=false')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_create_job(self):
        payload = {
            'job_number': '1886',
            'name': 'Mainline Sewer',
            'location': 'Downtown',
            'gc_name': 'Prime GC',
            'active': True,
        }

        response = self.client.post('/api/jobs/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Job.objects.filter(job_number='1886', name='Mainline Sewer').exists())

    def test_retrieve_job(self):
        job = Job.objects.create(job_number='1886', name='Mainline Sewer')

        response = self.client.get(f'/api/jobs/{job.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['job_number'], '1886')

    def test_patch_job(self):
        job = Job.objects.create(job_number='1886', name='Mainline Sewer')

        response = self.client.patch(
            f'/api/jobs/{job.pk}/',
            {'location': 'North Yard', 'gc_name': 'Prime GC'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job.refresh_from_db()
        self.assertEqual(job.location, 'North Yard')
        self.assertEqual(job.gc_name, 'Prime GC')

    def test_delete_job(self):
        job = Job.objects.create(job_number='1886', name='Mainline Sewer')

        response = self.client.delete(f'/api/jobs/{job.pk}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Job.objects.filter(pk=job.pk).exists())

    def test_delete_job_with_ewo_returns_validation_error(self):
        job = Job.objects.create(job_number='1886', name='Mainline Sewer')
        user = User.objects.create_user(username='job-delete-user')
        ExtraWorkOrder.objects.create(
            job=job,
            created_by=user,
            ewo_type=ExtraWorkOrder.EwoType.TM,
            work_date=date(2025, 6, 15),
            description='Existing work',
        )

        response = self.client.delete(f'/api/jobs/{job.pk}/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Job cannot be deleted', str(response.json()))

    def test_create_rejects_invalid_job_number(self):
        response = self.client.post(
            '/api/jobs/',
            {'job_number': 'ABC-123', 'name': 'Bad Job'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('job_number', response.json())
