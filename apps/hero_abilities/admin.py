from django.contrib import admin

from .models import Ability


class AbilityAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Ability._meta.fields]


admin.site.register(Ability, AbilityAdmin)
