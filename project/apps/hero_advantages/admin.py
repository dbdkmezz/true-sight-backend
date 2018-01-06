from django.contrib import admin

from .models import Hero, Advantage


class HeroAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Hero._meta.fields]


class AdvantageAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Advantage._meta.fields]


admin.site.register(Hero, HeroAdmin)
admin.site.register(Advantage, AdvantageAdmin)
