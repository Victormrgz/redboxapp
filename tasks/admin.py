from django.contrib import admin
from .models import Profile, Invitacion

# Register your models here.


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)


@admin.register(Invitacion)
class InvitacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'usado', 'fecha_creacion', 'fecha_expiracion')
    readonly_fields = ('codigo', 'fecha_creacion')
