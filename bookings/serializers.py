from django.utils import timezone
from rest_framework import serializers

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = [
            "id",
            "centre_test",
            "appointment_datetime",
            "amount",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "amount",
            "status",
            "created_at",
        ]

    def validate_appointment_datetime(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Appointment must be in the future."
            )

        return value
