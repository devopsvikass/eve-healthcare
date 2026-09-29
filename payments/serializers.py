from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "event_id",
            "amount",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "event_id",
            "amount",
            "status",
            "created_at",
        ]


class PaymentWebhookSerializer(serializers.Serializer):

    event_id = serializers.CharField(max_length=255)

    booking = serializers.IntegerField()

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = serializers.ChoiceField(
        choices=Payment.Status.choices
    )