from django.utils.translation import ugettext  as _
from django import forms
from django.contrib import admin
from filer.admin.fileadmin import FileAdmin
from filer.models import Video

from django.conf import settings

class VideoAdminChangeForm(forms.ModelForm):
    class Meta:
        model = Video

class VideoAdmin(FileAdmin):
    form = VideoAdminChangeForm
    fieldsets = (
        (None, {
            'fields': ('name', 'owner','description')
        }),
        (None, {
            'fields': ('is_public',)
            
        }),
        (_('Advanced'), {
            'fields': ('file','sha1',),
            'classes': ('collapse',),
        }),
    )