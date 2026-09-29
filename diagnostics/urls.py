from django.urls import path

from .views import (
    DiagnosticCentreListView,
    DiagnosticTestListView,
    CentreTestListView,
)


urlpatterns = [
    path("centres/", DiagnosticCentreListView.as_view()),
    path("tests/", DiagnosticTestListView.as_view()),
    path("centre-tests/", CentreTestListView.as_view()),
]
