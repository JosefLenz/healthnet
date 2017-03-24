from log import models


def add_log(record, event_type):
    log_entry = record
    log_level = event_type
    log = models.Log.objects.create(description=log_entry, type=log_level)
    log.save()
