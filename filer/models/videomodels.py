#-*- coding: utf-8 -*-
from datetime import datetime
from django.core import urlresolvers
from django.db import models
from django.utils.translation import ugettext_lazy as _
from filer import settings as filer_settings
from filer.models.filemodels import File
from filer.utils.filer_easy_thumbnails import FilerThumbnailer
import os, subprocess
from settings import MEDIA_ROOT
try:
    import cPickle as pickle
except:
    import pickle

"""
We have a number of dictionaries to help describe what we're doing. Maybe they should be in settings, but they are here for now.

This could be made simpler, but it's more flexible this way - for example, this allows us to prefer one encoder for one size, and a different encoder for another - just in case.

ENCODERS provides infomration about the commands that will be used to perform the video re-encoding, in this format. Each item in ENCODERS is the commandline name of the program.

Each command has a different schema, because they get their input/output filenames in a different order and with different prefix.
"""
ENCODERS = {
        "HandBrakeCLI": {
            "schema": ("options", "input", "output"), # the order in which the program expects to receive its options
            "input": "--input",
            "output": "--output",
            },
        "ffmpeg2theora": {
            "schema": ("options", "output", "input"),   # the schema is quite different from the one above
            "output": "--output",
            "input": "",
        },
    }

"""
CODECS contains information for the files that are created.

    'code' is a slugified version of the codec's name; it's added to the filename
    
    'description' and 'implications' are human-readable information
"""
CODECS = {
    "H.264": {
        "extension": ".mp4", 
        "code": "h264",
        "description": "MP4/H.264 format video",
        "implications": " - good support in Safari & iOS",
        },

    "Theora": {
        "extension": ".ogv", 
        "code": "theora",
        "description": "Ogg/Theora format video",
        "implications": " - good support in Firefox",
        },
    }

"""
SIZES is a tuple of the sizes we can encode to for output. It needs to be in order of increasing size.
"""

SIZES = (360,720)

"""
VERSIONS describes the different files we can encode to. 

Firstly, we list the different codecs we'll employ, then each size for each.

    'type' is the type attribute of the <source> element in HTML5
    'options' are what we pass to the command
"""

VERSIONS = {
    "H.264": {
        SIZES[0]:    {
                "encoder": "HandBrakeCLI",
                "type": "video/mp4; codecs='avc1.42E01E, .mp4a.40.2'", #supposedly, we should use the codecs attribute of the type attribute, but all it does for me is make Theora video stop working in Firefox
                "options": {
                    "--preset": "iPhone & iPod Touch", 
                    "--width": SIZES[0], #"--vb": "600",  
                    "--two-pass": "", 
                    "--turbo": "", 
                    "--optimize": "",
                    }, 
                },
        SIZES[1]:    {
                "encoder": "HandBrakeCLI",
                "type": "video/mp4; codecs='avc1.42E01E, .mp4a.40.2'",
                "options": {
                    "--preset": "iPhone & iPod Touch", 
                    "--width": SIZES[1], #"--vb": "600",  
                    "--two-pass": "", 
                    "--turbo": "", 
                    "--optimize": "",
                    }, 
                },
            },
    "Theora": {
        SIZES[0]:   {
                "encoder": "ffmpeg2theora",
                "type": "video/ogg; codecs='theo, vorb'",
                "options": {
                    "--videoquality": "5", 
                    "--audioquality": "1", 
                    "--width": SIZES[0],
                    },
            },
        SIZES[1]:   {
                "encoder": "ffmpeg2theora",
                "type": "video/ogg; codecs='theo, vorb'",
                "options": {
                    "--videoquality": "5", 
                    "--audioquality": "1", 
                    "--width": SIZES[1],
                    },
            },
        },
    }

"""
We provide these so we know we which encoded videos are available or missing for each kind of player.
"""
PLAYERS = {
    "HTML5": ("H.264", "Theora"),
    "FLASH": ("H.264",),
    }


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

    encode_on_save = models.BooleanField(default=False)
    delete_encoded_videos_on_save = models.BooleanField(default=False) # not used yet
    status = models.TextField(max_length = 200, default=pickle.dumps({}), null=True, blank = True)

    @classmethod
    def matches_file_type(cls, iname, ifile, request):
      # This was originally in admin/clipboardadmin.py  it was inside of a try
      # except, I have moved it here outside of a try except because I can't
      # figure out just what kind of exception this could generate... all it was
      # doing for me was obscuring errors...
      # --Dave Butler <croepha@gmail.com>
      iext = os.path.splitext(iname)[1].lower()
      return iext in ['.dv',]

    def save(self, *args, **kwargs):
        print "saving video"
    #     if self.delete_encoded_videos_on_save:
    #         pass
    #     if self.encode_on_save:
    #       pass
    #       self.encode_on_save = False

        # if not self.status: # probably no longer needed, since all videos should acquire the empty dict when created
        #     self.status = pickle.dumps({})
        super(Video, self).save(*args, **kwargs)

    def _check_validity(self):
        if not self.name:
            return False
        return True

    def sidebar_image_ratio(self):
        if self.width:
            return float(self.width) / float(self.SIDEBAR_IMAGE_WIDTH)
        else:
            return 1.0

    def has_edit_permission(self, request):
        return self.has_generic_permission(request, 'edit')

    def has_read_permission(self, request):
        return self.has_generic_permission(request, 'read')

    def has_add_children_permission(self, request):
        return self.has_generic_permission(request, 'add_children')

    def has_generic_permission(self, request, type):
        """
        Return true if the current user has permission on this
        image. Return the string 'ALL' if the user has all rights.
        """
        user = request.user
        if not user.is_authenticated() or not user.is_staff:
            return False
        elif user.is_superuser:
            return True
        elif user == self.owner:
            return True
        elif self.folder:
            return self.folder.has_generic_permission(request, type)
        else:
            return False

    @property
    def label(self):
        if self.name in ['', None]:
            return self.original_filename or 'unnamed file'
        else:
            return self.name

    @property
    def width(self):
        return self._width or 0

    @property
    def height(self):
        return self._height or 0

    @property
    def thumbnails(self):
        _thumbnails = {}
        for name, opts in Image.DEFAULT_THUMBNAILS.items():
            try:
                opts.update({'subject_location': self.subject_location})
                thumb = self.file.get_thumbnail(opts)
                _thumbnails[name] = thumb.url
            except:
                # swallow the exception to avoid it bubbling up
                # to the template {{ image.icons.48 }}
                pass
        return _thumbnails

    @property
    def easy_thumbnails_thumbnailer(self):
        tn = FilerThumbnailer(file=self.file.file, name=self.file.name,
                         source_storage=self.file.source_storage,
                         thumbnail_storage=self.file.thumbnail_storage)
        return tn

    def create_version(self, codec, size):
        # we're going to create an encoded version of our video, using <codec>, at <size>
        
        # this is always called by multiprocessing.Process - so:
        # close the database connection, because otherwise the database will hate us 
        from django.db import connection    
        connection.close()
        # now we've been asked to create a version
        # let's find out from the dictionaries what 
        codec_profile = VERSIONS[codec][size]
        codec_code = CODECS[codec]["code"]
        encoder = codec_profile["encoder"]
        schema = ENCODERS[encoder]["schema"]
        command = [encoder]
        # check the output folder exists; create it if not
        if not os.path.exists(self.abs_directory_path()):
            os.mkdir(self.abs_directory_path())
        # loop over the schema and assemble the command
        for item in schema:
            # input and output are special cases, because they take values that aren't determined by the schema
            if item == "input":
                command.extend((ENCODERS[encoder]["input"], self.file.path))
            elif item == "output":
                command.extend((ENCODERS[encoder]["output"], self.outputpath(codec, size)))
            else:
                for option_prefix, option_value in codec_profile[item].items():
                    command.extend((option_prefix,str(option_value)))

        try:
            # mark it as "encoding", so nothing else tries to encode it while we're doing this
            self.save_status(codec,size,"encoding") 
            # now do the encoding and don't let anything after this happen until we finish executing command:
            exit_status = subprocess.call(command) 
            if exit_status == 0: # it's OK, so mark the version OK
                self.save_status(codec,size,"OK")
            else:
                self.save_status(codec,size,"failed") # mark it as failed because the command returned an error
        except Exception, e:
            print " =================================== exception, ", e
            self.save_status(codec,size,"failed") # mark it as failed because there was an exception
        # we should never return from here with the status still "encoding" - but that has happened - how?
        
    def codec_and_size(self, codec, size):
        # returns a string containing codec and size - e.g. h264-720 - used in various ways, such as version filenames
        return "-".join((CODECS[codec]["code"], str(size)))

    def get_status(self):
        # get the status dictionary
        return pickle.loads(str(self.status))

    def save_status(self, codec, size, status):
        # save a key/value into the status dictionary
        current_status = self.get_status()
        current_status[self.codec_and_size(codec,size)] = status
        self.status=pickle.dumps(current_status)
        self.save()

    def check_status(self,codec,size):
        # report the status of a version
        return self.get_status().get(self.codec_and_size(codec,size), "missing")

    def outputpath(self, codec, size):
        # the output path and filename for the version
        return os.path.join(self.abs_directory_path(), \
        "-".join((self.filename_without_extension(), \
        self.codec_and_size(codec,size))) \
        + CODECS[codec]["extension"])
        
    def url(self, codec, size):
        # the url for a particular version
        return os.path.join(MEDIA_URL, \
            self.directory(), \
            THUMBNAIL_SUBDIR, \
            "-".join((self.filename_without_extension(),
            self.codec_and_size(codec,size))) \
            + CODECS[codec]["extension"])
            
    def get_admin_url_path(self):
        # I don't actually understand what this is for - stefan?
        print urlresolvers.reverse('admin:filer_video_change', args=(self.id,))
        return urlresolvers.reverse('admin:filer_video_change', args=(self.id,))
        
    def directory(self):
        # e.g. "filer_private/2010/11/23"
        return os.path.dirname(str(self.file)) 
        
    def filename(self):    
        # e.g. "video.dv"
        return os.path.basename(str(self.file)) 

    def filename_without_extension(self):
        # e.g. "video"
        return os.path.splitext(self.filename())[0].lower() 
        
    def abs_directory_path(self):
        # e.g. "/var/www/html/arkestra_medic/media/filer_private/2010/11/23/output"
        return os.path.join(MEDIA_ROOT, self.directory(), THUMBNAIL_SUBDIR)
        
    def sizes(self):
        return SIZES
        
    def codecs(self):
        return CODECS  
        
    def get_absolute_url(self):
        print "not done yet"
        return "/video%s/" % os.path.join(MEDIA_URL, \
            self.directory(), \
            self)
            
    class Meta:
        app_label = 'filer'
        verbose_name = _('video')
        verbose_name_plural = _('videos')
