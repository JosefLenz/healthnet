from django.forms import Form
from django import forms
from .models import *


class AppointmentForm(Form):
    hospital = forms.ModelChoiceField(widget=forms.Select(attrs={'class':'form-control'}),queryset=Hospital.objects.all())
    description = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Description','class':'form-control'}))
    start_date = forms.DateField(required=True,
                                 widget=forms.SelectDateWidget(attrs={'class':'form-control'},years=range(timezone.now().year,
                                                                           timezone.now().year + 10)))
    start_time = forms.TimeField(required=True,
                                 widget=forms.TimeInput(attrs={'placeholder': 'Time: HH:MM', 'class':'form-control'},
                                                        format='%H:%M'))
    # end_date = forms.DateField(required=True,
    #                            widget=forms.SelectDateWidget(years=range(1818, timezone.now().year+1)))
    # end_time = forms.TimeField(required=True,
    #                            widget=forms.TimeInput(format='%H:%M'))


class PatientAppointment(AppointmentForm):
    doctor = forms.ModelChoiceField(widget=forms.Select(attrs={'class':'form-control'}),queryset=Doctor.objects.all())


class DoctorAppointment(AppointmentForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all())


class NurseAppointment(AppointmentForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all())
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all())

