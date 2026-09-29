from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from diagnostics.models import DiagnosticCentre, DiagnosticTest, CentreTest
from bookings.models import Booking
from payments.models import Payment


class PaymentAPITestCase(APITestCase):

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="paymentuser",
            password="Paymentuser@123"
        )

        # Create diagnostic centre
        self.centre = DiagnosticCentre.objects.create(
            name="Payment Test Diagnostics",
            location="Delhi"
        )

        # Create diagnostic test
        self.test = DiagnosticTest.objects.create(
            name="Blood Test",
            description="Payment test"
        )

        # Create centre-test with price
        self.centre_test = CentreTest.objects.create(
            centre=self.centre,
            test=self.test,
            price="500.00"
        )

        # Authenticate test client
        self.client.force_authenticate(user=self.user)

        # Create pending booking
        self.booking = Booking.objects.create(
            user=self.user,
            centre_test=self.centre_test,
            appointment_datetime=timezone.now() + timedelta(days=2),
            amount="500.00",
            status=Booking.Status.PENDING,
        )

    def test_successful_payment(self):
        response = self.client.post(
            "/api/payments/",
            {
                "booking": self.booking.id
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["status"],
            Payment.Status.SUCCESS
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.CONFIRMED
        )

        self.assertEqual(
            Payment.objects.count(),
            1
        )

    def test_successful_webhook(self):
        response = self.client.post(
            "/api/payments/webhook/",
            {
                "event_id": "webhook-success-001",
                "booking": self.booking.id,
                "amount": "500.00",
                "status": "SUCCESS",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.CONFIRMED
        )

        self.assertEqual(
            Payment.objects.count(),
            1
        )

        payment = Payment.objects.get(
            event_id="webhook-success-001"
        )

        self.assertEqual(
            payment.status,
            Payment.Status.SUCCESS
        )


    def test_duplicate_webhook_is_idempotent(self):
        webhook_data = {
            "event_id": "duplicate-webhook-001",
            "booking": self.booking.id,
            "amount": "500.00",
            "status": "SUCCESS",
        }

        # First webhook
        first_response = self.client.post(
            "/api/payments/webhook/",
            webhook_data,
            format="json"
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            Payment.objects.count(),
            1
        )

        # Same webhook again
        second_response = self.client.post(
            "/api/payments/webhook/",
            webhook_data,
            format="json"
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            second_response.data["message"],
            "Webhook already processed."
        )

        # Still only one payment
        self.assertEqual(
            Payment.objects.count(),
            1
        )


    def test_failed_webhook(self):
        response = self.client.post(
            "/api/payments/webhook/",
            {
                "event_id": "webhook-failed-001",
                "booking": self.booking.id,
                "amount": "500.00",
                "status": "FAILED",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.FAILED
        )

        self.assertEqual(
            Payment.objects.count(),
            1
        )

        payment = Payment.objects.get(
            event_id="webhook-failed-001"
        )

        self.assertEqual(
            payment.status,
            Payment.Status.FAILED
        )



    def test_webhook_with_invalid_booking(self):
        response = self.client.post(
            "/api/payments/webhook/",
            {
                "event_id": "invalid-booking-001",
                "booking": 99999,
                "amount": "500.00",
                "status": "SUCCESS",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.assertEqual(
            response.data["error"],
            "Booking not found."
        )

        self.assertEqual(
            Payment.objects.count(),
            0
        )


    def test_webhook_amount_mismatch(self):
        response = self.client.post(
            "/api/payments/webhook/",
            {
                "event_id": "amount-mismatch-001",
                "booking": self.booking.id,
                "amount": "800.00",
                "status": "SUCCESS",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error"],
            "Payment amount does not match booking amount."
        )

        self.assertEqual(
            Payment.objects.count(),
            0
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.PENDING
        )


    def test_user_cannot_pay_for_another_users_booking(self):
        other_user = User.objects.create_user(
            username="anotheruser",
            password="Anotheruser@123"
        )

        self.client.force_authenticate(user=other_user)

        response = self.client.post(
            "/api/payments/",
            {
                "booking": self.booking.id
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.assertEqual(
            response.data["error"],
            "Booking not found."
        )

        self.assertEqual(
            Payment.objects.count(),
            0
        )

    def test_payment_not_allowed_for_confirmed_booking(self):
        # First payment
        first_response = self.client.post(
            "/api/payments/",
            {
                "booking": self.booking.id
            },
            format="json"
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.CONFIRMED
        )

        # Try to pay again
        second_response = self.client.post(
            "/api/payments/",
            {
                "booking": self.booking.id
            },
            format="json"
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            second_response.data["error"],
            "Payment can only be made for a pending booking."
        )

        # Only one payment should exist
        self.assertEqual(
            Payment.objects.count(),
            1
        )

    def test_webhook_not_allowed_for_confirmed_booking(self):
        # First confirm the booking
        self.client.post(
            "/api/payments/",
            {
                "booking": self.booking.id
            },
            format="json"
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.CONFIRMED
        )

        # Try to process another webhook for the same booking
        response = self.client.post(
            "/api/payments/webhook/",
            {
                "event_id": "confirmed-booking-webhook-001",
                "booking": self.booking.id,
                "amount": "500.00",
                "status": "SUCCESS",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error"],
            "Booking is no longer pending."
        )

        # Still only one payment
        self.assertEqual(
            Payment.objects.count(),
            1
        )