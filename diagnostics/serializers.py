from rest_framework import serializers

from .models import DiagnosticCentre, DiagnosticTest, CentreTest


class DiagnosticCentreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticCentre
        fields = [
            "id",
            "name",
            "location",
        ]


class DiagnosticTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticTest
        fields = [
            "id",
            "name",
            "description",
        ]


class CentreTestSerializer(serializers.ModelSerializer):
    centre_name = serializers.CharField(
        source="centre.name",
        read_only=True
    )

    test_name = serializers.CharField(
        source="test.name",
        read_only=True
    )

    class Meta:
        model = CentreTest
        fields = [
            "id",
            "centre",
            "centre_name",
            "test",
            "test_name",
            "price",
        ]


