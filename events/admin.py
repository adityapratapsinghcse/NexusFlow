from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Event , Venue, EventRegistration

@admin.register(Venue)
class VenueAdmin(ImportExportModelAdmin):
    list_display = ('name','capacity','location','is_active')

admin.site.register(EventRegistration)

admin.site.register(Event)