
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking
from .serializers import BookingSerializer

class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related(
            "centre_test",
            "centre_test__centre",
            "centre_test__test",
        )

    def perform_create(self, serializer):
        centre_test = serializer.validated_data["centre_test"]

        serializer.save(
            user=self.request.user,
            amount=centre_test.price,
            status=Booking.Status.PENDING,
        )


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            booking = Booking.objects.get(
                id=pk,
                user=request.user
            )
        except Booking.DoesNotExist:
            return Response(
                {
                    "error": "Booking not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if booking.status != Booking.Status.PENDING:
            return Response(
                {
                    "error": "Only pending bookings can be cancelled."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = Booking.Status.CANCELLED
        booking.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        serializer = BookingSerializer(booking)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )