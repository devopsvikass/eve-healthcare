from django.contrib import admin

from .models import DiagnosticCentre, DiagnosticTest, CentreTest


admin.site.register(DiagnosticCentre)
admin.site.register(DiagnosticTest)
admin.site.register(CentreTest)