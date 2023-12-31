from django.contrib import admin
from .models import Script, Comparison, Set, Student
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class ComparisonResource(resources.ModelResource):
    class Meta:
        model = Comparison

class ScriptResource(resources.ModelResource):
    class Meta:
        model = Script
        
class StudentResource(resources.ModelResource):
    class Meta:
        model = Student

class ComparisonAdmin(ImportExportModelAdmin):
    resource_class = ComparisonResource

class ScriptAdmin(ImportExportModelAdmin):
    resource_class = ScriptResource

class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource

admin.site.register(Comparison, ComparisonAdmin)
admin.site.register(Script, ScriptAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Set)

