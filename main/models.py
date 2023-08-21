from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=6)

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    gh_link = models.URLField(blank=True)
    yt_link = models.URLField(blank=True)
    preview_image = models.ImageField(upload_to='projects/images', blank=True)
    tags = models.ManyToManyField('Tag', related_name='projects', blank=True)

    def __str__(self):
        return self.title
