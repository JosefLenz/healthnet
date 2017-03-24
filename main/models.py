from django.db import models
from django.contrib.auth.models import User
from django.template import loader
from django.utils import timezone
# Create your models here.


# model for holding hospital information
class Hospital(models.Model):
    hospitalName = models.CharField(max_length=100)     # Human readable hospital name
    location = models.CharField(max_length=100)         # Human readable hospital location, ideally an address
    ID = models.AutoField(primary_key=True)             # Identifying Primary Key ID

    # Function returns human-readable identifying string. For the hospital, that is the Hospital's name.
    def __str__(self):
        return self.hospitalName

    def get_id(self):
        return self.ID


class Test(models.Model):
    testName = models.CharField(max_length=30)
    testComment = models.TextField(max_length=500, blank=True, null=True)
    testImage = models.ImageField(upload_to='media/tests/', null=True, blank=True, default=None)
    testReleased = models.BooleanField(default=False)
    testPatient = models.ForeignKey('Patient', on_delete=models.CASCADE)

    # This field should be written in the view to match the Dr's name and ID, and not be editable by the doctor.
    testDoctor = models.CharField(max_length=60)

    def __str__(self):
        return self.testName+" " + self.testPatient.get_name() + " " + self.testDoctor


# Model for patient's prescriptions
class Prescription(models.Model):
    ID = models.AutoField(primary_key=True)
    medicationName = models.CharField(max_length=30)
    medicationDirections = models.TextField(max_length=100)
    medicationAmount = models.IntegerField()
    medicationType = models.CharField(max_length=30)
    medicationRefills = models.IntegerField()
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)

    # This field should be written in the view to match the Dr's name and ID, and not be editable by the doctor.
    prescribingDoctor = models.CharField(max_length=60)

    #  Returns prescription label in the form (or near the form) given here:
    # http://www.knowledgeisthebestmedicine.org/index.php/en/know_your_healthcare_team/prescription_label
    def __str__(self):
        return "RX: " + str(self.ID) + "      Ref: " + str(self.medicationRefills) +\
               "      DR. " + self.prescribingDoctor +\
               "\n" + self.patient.get_name() + "\n" + \
               "\n" + self.medicationDirections + "\n" + \
               "\n" + self.medicationName + \
               "\n" + str(self.medicationAmount) + " " + self.medicationType

    def get_id(self):
        return self.ID

    def get_name(self):
        return self.medicationName


# Base model to hold Universal HealthNet user data
class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # All UserData models have an associate Django user
    ID = models.AutoField(primary_key=True)  # All UserData models have an associated Primary Key ID

    def get_name(self):
        return self.user.get_full_name()

    # Function returns human-readable identifying string. For all users, that string is the user's full name and ID
    def __str__(self):
        return str(self.get_id()) + " " + self.user.get_full_name()

    # Function the user's ID number, for identifying the user. The IDs exist for all users.
    def get_id(self):
        return self.ID

    # Meta class allows this model to be specified as an abstract model
    # As an abstract model, UserData will not be in the database
    class Meta:
        abstract = True


# Model for holding patient information
class Patient(UserData):
    avatar = models.ImageField(upload_to='media/avatars/', default='media/avatars/generic_800.jpg')

    date_of_birth = models.DateField(default=timezone.now())                          # Patient DOB obviously needed for medical purposes

    address_line1 = models.CharField(default="123 pls ln", max_length=50)             # Address stored as a char fields, allows for formatting
    address_line2 = models.CharField(default=None, max_length=50, null=True)
    address_city = models.CharField(default="pls city", max_length=50)
    address_region = models.CharField(default="pls state", max_length=50)
    address_zip = models.CharField(default="pls zip code", max_length=50)
    address_country = models.CharField(default="country pls", max_length=50)

    insurance_company = models.CharField(default="insurance pls", max_length=100)     # Insurance information stored as a textfield
    insurance_number = models.CharField(default="insurance numba pls", max_length=50)

    medical_conditions = models.TextField(default=None)                               # Patient's medical conditions, stored in textfield
    preferred_hospital = models.ForeignKey(Hospital,                                  # Patient's preferred hospital
                                           related_name="preferred_hospital")
    emergency_contact = models.CharField(default="emergency pls", max_length=60)      # Patient's emergency contact information
    emergency_contact_number = models.CharField(default="5555555555", max_length=16)

    admitted_hospital = models.ForeignKey(Hospital,                                   # Hospital to which the patient is admitted.
                                          default=None,
                                          blank=True,
                                          null=True,
                                          related_name="admitted_hospital")


# Model for holding doctor information
class Doctor(UserData):
    hospitals = models.ManyToManyField(Hospital)  # All Doctors have an association with one or more valid hospitals


# Model for holding nurse information
class Nurse(UserData):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)  # Nurses are associated with a single hospital