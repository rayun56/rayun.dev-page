import os
import hashlib

from django.db import models
from django.core.files.storage import FileSystemStorage


class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=6)

    def __str__(self):
        return self.name


def project_image_path(instance, filename):
    hash = instance.preview_image_hash
    ext = os.path.splitext(filename)[1]
    return f'projects/images/{hash}{ext.lower()}'


class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    gh_link = models.URLField(blank=True)
    yt_link = models.URLField(blank=True)
    preview_image = models.ImageField(upload_to=project_image_path, blank=True)
    preview_image_hash = models.CharField(max_length=64, blank=True, editable=False)
    tags = models.ManyToManyField('Tag', related_name='projects', blank=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.preview_image:
            md5 = hashlib.md5()
            for chunk in self.preview_image.chunks():
                md5.update(chunk)
            self.preview_image_hash = md5.hexdigest()
        super(Project, self).save(*args, **kwargs)


class CrudtoberDay(models.Model):
    day = models.IntegerField()
    items = models.TextField()  # Delimited by newlines

    def __str__(self):
        return f"Day {self.day}"
