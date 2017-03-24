# -*- coding: utf-8 -*-

from django.db import models
from datetime import timedelta
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from main.models import *

class CalendarEvent(models.Model):
    """The event set a record for an 
    activity that will be scheduled at a 
    specified date and time. 
    
    It could be on a date and time 
    to start and end, but can also be all day.
    
    :param title: Title of event
    :type title: str.
    
    :param start: Start date of event
    :type start: datetime.
    
    :param end: End date of event
    :type end: datetime.
    
    :param all_day: Define event for all day
    :type all_day: bool.
    """
    title = models.CharField(_('Title'), blank=True, max_length=200)
    start = models.DateTimeField(_('Start'), default=timezone.now())
    end = models.DateTimeField(_('End'), default=timezone.now() + timedelta(hours=1))
    all_day = models.BooleanField(_('All day'), default=False)

    ID = models.AutoField(primary_key=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)

    verified = models.BooleanField(default=False)


    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title