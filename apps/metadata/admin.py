from django.contrib import admin

from .models import AdvantagesUpdate


class AdvantagesUpdateAdmin(admin.ModelAdmin):
    list_display = [f.name for f in AdvantagesUpdate._meta.fields]


admin.site.register(AdvantagesUpdate, AdvantagesUpdateAdmin)
