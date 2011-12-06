#-*- coding: utf-8 -*-
from datetime import datetime
from django.core import urlresolvers
from django.db import models
from django.utils.translation import ugettext_lazy as _
from filer import settings as filer_settings
from filer.models.filemodels import File
from filer.utils.filer_easy_thumbnails import FilerThumbnailer
import os
from settings import MEDIA_ROOT, MEDIA_URL
try:
    import cPickle as pickle
except Exception, e:
    print e
    import pickle

class Video(File):
    SIDEBAR_IMAGE_WIDTH = 210
    DEFAULT_THUMBNAILS = {
        'admin_clipboard_icon': {'size': (32, 32), 'crop': True,
                                 'upscale': True},
        'admin_sidebar_preview': {'size': (SIDEBAR_IMAGE_WIDTH, 10000)},
        'admin_directory_listing_icon': {'size': (48, 48),
                                         'crop': True, 'upscale': True},
        'admin_tiny_icon': {'size': (32, 32), 'crop': True, 'upscale': True},
    }
    file_type = 'Video'
    _icon = "video"

    def save(self, *args, **kwargs):
        print "** saving", self
        super(Video, self).save(*args, **kwargs)

    @classmethod
    def matches_file_type(cls, iname, ifile, request):
      # This was originally in admin/clipboardadmin.py  it was inside of a try
      # except, I have moved it here outside of a try except because I can't
      # figure out just what kind of exception this could generate... all it was
      # doing for me was obscuring errors...
      # --Dave Butler <croepha@gmail.com>
      iext = os.path.splitext(iname)[1].lower()
      return iext in ['.dv', '.mov', '.mp4', '.avi', '.wmv',]
        
            
    def get_admin_url_path(self):
        print urlresolvers.reverse('admin:filer_video_change', args=(self.id,))
        return urlresolvers.reverse('admin:filer_video_change', args=(self.id,))
                
            
    class Meta:
        app_label = 'filer'
        verbose_name = _('video')
        verbose_name_plural = _('videos')
