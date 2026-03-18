from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin, TabularInline

from .models import UserProfile


class UserProfileInline(TabularInline):
    model = UserProfile
    extra = 1
    fields = ('role', 'active')
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin, ModelAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_active')
    list_filter = ('is_active', 'is_staff', 'profile__role')

    @admin.display(description='Role')
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return '—'


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ('user', 'role', 'active')
    list_filter = ('role', 'active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('user',)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
