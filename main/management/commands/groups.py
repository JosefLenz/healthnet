#This file defines a custom manage.py command for use in the console.
#This command will establish user groups.


from django.contrib.auth.models import Group, Permission

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def handle(self, *args, **options):
        doctor, doctorMade = Group.objects.get_or_create(name='Doctor')
        doctor.permissions.add(Permission.objects.get(codename='createowndoctor_appointment'))

        patient, patientMade = Group.objects.get_or_create(name='Patient')
        patient.permissions.add(Permission.objects.get(codename='createownpatient_appointment'))

        nurse, nurseMade = Group.objects.get_or_create(name='Nurse')
        nurse.permissions.add(Permission.objects.get(codename='createany_appointment'))





