from django.contrib import admin
from .models import Script, Comparison, Set

admin.site.register(Comparison)
admin.site.register(Script)
admin.site.register(Set)
# Register your models here.
