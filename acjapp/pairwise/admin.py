from django.contrib import admin
from .models import Script, Comparison, Set, Student, Test
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class TestResource(resources.ModelResource):
    class Meta:
        model = Test

class SetResource(resources.ModelResource):
    class Meta:
        model = Set

class ComparisonResource(resources.ModelResource):
    class Meta:
        model = Comparison

class ScriptResource(resources.ModelResource):
    class Meta:
        model = Script

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student

class TestAdmin(ImportExportModelAdmin):
    resource_class = TestResource
    list_display = ['name']

class SetAdmin(ImportExportModelAdmin):
    resource_class = SetResource
    filter_horizontal = ('judges',)
    list_display = ['id','owner','test']

class ComparisonAdmin(ImportExportModelAdmin):
    resource_class = ComparisonResource
    list_display = ['id','set','judge','scripti','scriptj','wini','decision_start']
    list_filter = ['set','judge','decision_start']

class ScriptAdmin(ImportExportModelAdmin):
    resource_class = ScriptResource
    filter_horizontal = ('sets',)
    list_display = ['id','idcode','student','date']
    list_filter = ['sets','date']

class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ['__str__','first_name','last_name','birth_date','user']
    list_filter = ['user']

admin.site.register(Comparison, ComparisonAdmin)
admin.site.register(Script, ScriptAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(Test, TestAdmin)
