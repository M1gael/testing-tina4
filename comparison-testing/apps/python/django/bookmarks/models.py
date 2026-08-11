from django.db import models


class Bookmark(models.Model):
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
