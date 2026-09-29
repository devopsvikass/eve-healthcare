import uuid

from django.db import transaction
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from bookings.models import Booking
from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentWebhookSerializer,
)



class PaymentCreateView(generics.CreateAPIView):

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        booking_id = request.data.get("booking")

        if not booking_id:
            return Response(
                {"error": "booking is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking = Booking.objects.get(
                id=booking_id,
                user=request.user
            )
        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if booking.status != Booking.Status.PENDING:
            return Response(
                {
                    "error": "Payment can only be made for a pending booking."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Simulate a successful payment
        payment_status = Payment.Status.SUCCESS

        with transaction.atomic():

            payment = Payment.objects.create(
                booking=booking,
                event_id=str(uuid.uuid4()),
                amount=booking.amount,
                status=payment_status,
            )

            booking.status = Booking.Status.CONFIRMED
            booking.save(update_fields=["status", "updated_at"])

        serializer = self.get_serializer(payment)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class PaymentWebhookView(generics.GenericAPIView):

    serializer_class = PaymentWebhookSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_id = serializer.validated_data["event_id"]
        booking_id = serializer.validated_data["booking"]
        webhook_amount = serializer.validated_data["amount"]
        webhook_status = serializer.validated_data["status"]

        with transaction.atomic():

            # Check whether this event was already processed
            existing_payment = (
                Payment.objects
                .select_for_update()
                .filter(event_id=event_id)
                .first()
            )

            if existing_payment:

                return Response(
                    {
                        "message": "Webhook already processed.",
                        "payment_id": existing_payment.id,
                        "status": existing_payment.status,
                    },
                    status=status.HTTP_200_OK
                )

            # Lock the booking while processing the webhook
            try:
                booking = (
                    Booking.objects
                    .select_for_update()
                    .get(id=booking_id)
                )

            except Booking.DoesNotExist:

                return Response(
                    {
                        "error": "Booking not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verify that webhook amount matches booking amount
            if webhook_amount != booking.amount:

                return Response(
                    {
                        "error": "Payment amount does not match booking amount."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prevent processing a new payment event
            # for a booking that is no longer pending
            if booking.status != Booking.Status.PENDING:

                return Response(
                    {
                        "error": "Booking is no longer pending."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create payment record
            payment = Payment.objects.create(
                booking=booking,
                event_id=event_id,
                amount=webhook_amount,
                status=webhook_status,
            )

            # Update booking according to payment result
            if webhook_status == Payment.Status.SUCCESS:

                booking.status = Booking.Status.CONFIRMED

            elif webhook_status == Payment.Status.FAILED:

                booking.status = Booking.Status.FAILED

            booking.save(
                update_fields=[
                    "status",
                    "updated_at"
                ]
            )

        return Response(
            {
                "message": "Webhook processed successfully.",
                "payment_id": payment.id,
                "booking_id": booking.id,
                "booking_status": booking.status,
            },
            status=status.HTTP_200_OK
        )


    