from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from diagnostics.models import DiagnosticCentre, DiagnosticTest, CentreTest
from bookings.models import Booking


class BookingAPITestCase(APITestCase):

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            password="Testuser@123"
        )

        # Create diagnostic centre
        self.centre = DiagnosticCentre.objects.create(
            name="Test Diagnostics",
            location="Delhi"
        )

        # Create diagnostic test
        self.test = DiagnosticTest.objects.create(
            name="CBC",
            description="Complete Blood Count"
        )

        # Connect centre + test + price
        self.centre_test = CentreTest.objects.create(
            centre=self.centre,
            test=self.test,
            price="600.00"
        )

        # Login
        self.client.force_authenticate(user=self.user)

    def test_create_booking(self):
        appointment_time = timezone.now() + timedelta(days=2)

        response = self.client.post(
            "/api/bookings/",
            {
                "centre_test": self.centre_test.id,
                "appointment_datetime": appointment_time.isoformat()
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["amount"],
            "600.00"
        )

        self.assertEqual(
            response.data["status"],
            "PENDING"
        )

        self.assertEqual(
            Booking.objects.count(),
            1
        )

    def test_create_booking_with_past_appointment(self):
        appointment_time = timezone.now() - timedelta(days=1)

        response = self.client.post(
            "/api/bookings/",
            {
                "centre_test": self.centre_test.id,
                "appointment_datetime": appointment_time.isoformat()
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "Appointment must be in the future.",
            str(response.data)
        )

    def test_cancel_pending_booking(self):
        appointment_time = timezone.now() + timedelta(days=2)

        booking = Booking.objects.create(
            user=self.user,
            centre_test=self.centre_test,
            appointment_datetime=appointment_time,
            amount="600.00",
            status=Booking.Status.PENDING,
        )

        response = self.client.post(
            f"/api/bookings/{booking.id}/cancel/",
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.CANCELLED
        )

    def test_cannot_cancel_confirmed_booking(self):
        appointment_time = timezone.now() + timedelta(days=2)

        booking = Booking.objects.create(
            user=self.user,
            centre_test=self.centre_test,
            appointment_datetime=appointment_time,
            amount="600.00",
            status=Booking.Status.CONFIRMED,
        )

        response = self.client.post(
            f"/api/bookings/{booking.id}/cancel/",
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error"],
            "Only pending bookings can be cancelled."
        )

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.CONFIRMED
        )

    def test_user_cannot_cancel_another_users_booking(self):
        booking = Booking.objects.create(
            user=self.user,
            centre_test=self.centre_test,
            appointment_datetime=timezone.now() + timedelta(days=2),
            amount="600.00",
            status=Booking.Status.PENDING,
        )

        other_user = User.objects.create_user(
            username="anotherbookinguser",
            password="Anotheruser@123"
        )

        self.client.force_authenticate(user=other_user)

        response = self.client.post(
            f"/api/bookings/{booking.id}/cancel/",
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

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.PENDING
        )