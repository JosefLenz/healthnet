from django.db import models
from django.utils import timezone



class Log(models.Model):
    date = models.DateTimeField(default=timezone.now, blank=True)
    description = models.TextField()
    type = models.CharField(max_length=7)

    def __str__(self):
        return self.description;