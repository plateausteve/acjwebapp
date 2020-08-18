from django.contrib import admin
from .models import Script, Comparison, Set
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class ComparisonResource(resources.ModelResource):
    class Meta:
        model = Comparison

class ComparisonAdmin(ImportExportModelAdmin):
    resource_class = ComparisonResource

admin.site.register(Comparison, ComparisonAdmin)
admin.site.register(Script)
admin.site.register(Set)
