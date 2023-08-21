import os

from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=6)

    def __str__(self):
        return self.name


def project_image_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f"projects/images/{instance.id}{ext}"


class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    gh_link = models.URLField(blank=True)
    yt_link = models.URLField(blank=True)
    preview_image = models.ImageField(upload_to=project_image_path, blank=True)
    tags = models.ManyToManyField('Tag', related_name='projects', blank=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.title
