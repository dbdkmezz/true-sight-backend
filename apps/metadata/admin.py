from django.contrib import admin

from .models import AdvantagesUpdate, User, DailyUse, ResponderUse


class AdvantagesUpdateAdmin(admin.ModelAdmin):
    list_display = [f.name for f in AdvantagesUpdate._meta.fields]


class UserAdmin(admin.ModelAdmin):
    list_display = [f.name for f in User._meta.fields]


class DailyUseAdmin(admin.ModelAdmin):
    list_display = [f.name for f in DailyUse._meta.fields]


class ResponderUseAdmin(admin.ModelAdmin):
    list_display = [f.name for f in ResponderUse._meta.fields]


admin.site.register(AdvantagesUpdate, AdvantagesUpdateAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(DailyUse, DailyUseAdmin)
admin.site.register(ResponderUse, ResponderUseAdmin)
