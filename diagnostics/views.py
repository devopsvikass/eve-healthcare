from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import DiagnosticCentre, DiagnosticTest, CentreTest
from .serializers import (
    DiagnosticCentreSerializer,
    DiagnosticTestSerializer,
    CentreTestSerializer,
)


class DiagnosticCentreListView(generics.ListAPIView):
    queryset = DiagnosticCentre.objects.all()
    serializer_class = DiagnosticCentreSerializer
    permission_classes = [IsAuthenticated]


class DiagnosticTestListView(generics.ListAPIView):
    queryset = DiagnosticTest.objects.all()
    serializer_class = DiagnosticTestSerializer
    permission_classes = [IsAuthenticated]


class CentreTestListView(generics.ListAPIView):
    queryset = CentreTest.objects.select_related(
        "centre",
        "test"
    ).all()
    serializer_class = CentreTestSerializer
    permission_classes = [IsAuthenticated]