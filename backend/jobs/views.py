from django.db.models import ProtectedError
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny

from .models import Job
from .serializers import JobSerializer


class JobListCreateView(ListCreateAPIView):
    """
    GET /api/jobs/
    POST /api/jobs/

    Returns active jobs by default. Pass ?active=false to include inactive jobs.
    Auth deferred to M4 (DEC-007).
    """

    serializer_class = JobSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Job.objects.order_by('-job_number')
        if self.request.query_params.get('active') == 'false':
            return qs
        return qs.filter(active=True)


class JobDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET/PATCH/DELETE /api/jobs/<pk>/

    Auth deferred to M4 (DEC-007).
    """

    queryset = Job.objects.all().order_by('-job_number')
    serializer_class = JobSerializer
    permission_classes = [AllowAny]

    def perform_destroy(self, instance):
        try:
            super().perform_destroy(instance)
        except ProtectedError as exc:
            raise ValidationError(
                'Job cannot be deleted while protected records still reference it.'
            ) from exc
