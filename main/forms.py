from django import forms
from django.core.validators import RegexValidator
from .models import *


class PrescriptionForm(forms.Form):
    #patient = forms.ModelChoiceField(queryset=Patient.objects.all(), disabled=False)
    medication_name = forms.CharField(max_length=30, required=True,
                                      widget=forms.TextInput(attrs={'placeholder': ''}))
    medication_directions = forms.CharField(max_length=100, required=True,
                                            widget=forms.Textarea(attrs={'placeholder': 'Directions'}))
    medication_amount = forms.IntegerField(min_value=1, required=True)
    medication_type = forms.CharField(max_length=30, required=True,
                                      widget=forms.TextInput(attrs={'placeholder': ''}))
    medication_refills = forms.IntegerField(min_value=1, required=True)

    prescribing_doctor = forms.CharField(max_length=60, required=True, disabled=True)


class TestForm(forms.Form):
    test_name = forms.CharField(max_length=30, required=True,
                                widget=forms.TextInput(attrs={'placeholder': 'Test Name'}))
    test_comment = forms.CharField(max_length=500, required=False,
                                   widget=forms.Textarea(attrs={'placeholder': 'Comment'}))
    test_image = forms.ImageField(required=False)

    test_doctor = forms.CharField(max_length=60, required=True, disabled=True)


class BooleanForm(forms.Form):
    confirm = forms.BooleanField(required=True)


# form for used for the patient specified fields
class PatientDataForm(forms.Form):

    username = forms.CharField(max_length=30, required=True,
                               widget=forms.TextInput(attrs={'placeholder': 'UserName', 'class':'form-control'}))
    avatar = forms.ImageField(required=False)
    first_name = forms.CharField(max_length=30, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class':'form-control'}))
    last_name = forms.CharField(max_length=30, required=True,
                                widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class':'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class':'form-control'}), required=True,)
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class':'form-control'}),
                                       required=True,)

    email = forms.EmailField(required=True,
                             widget=forms.TextInput(attrs={'placeholder': 'Email', 'class':'form-control'}))
    date_of_birth = forms.DateField(required=True,
                                    widget=forms.SelectDateWidget(attrs={'class':'form-control'},years=range(1900, timezone.now().year+1)))

    address1 = forms.CharField(max_length=60, required=True,
                               widget=forms.TextInput(attrs={'placeholder': 'Address Line 1', 'class':'form-control'}))
    address2 = forms.CharField(max_length=60, required=False,
                               widget=forms.TextInput(attrs={'placeholder': 'Address Line 2', 'class':'form-control'}))
    city = forms.CharField(max_length=60, required=True,
                           widget=forms.TextInput(attrs={'placeholder': 'City', 'class':'form-control'}))
    region = forms.CharField(max_length=60, required=True,
                             widget=forms.TextInput(attrs={'placeholder': 'State/Province/Region', 'class':'form-control'}))
    zip = forms.CharField(max_length=60, required=True,
                          widget=forms.TextInput(attrs={'placeholder': 'ZIP/Postal Code', 'class':'form-control'}))
    country = forms.CharField(max_length=60, required=True,
                              widget=forms.TextInput(attrs={'placeholder': 'Country', 'class':'form-control'}))

    insurance_company = forms.CharField(required=True,
                                        widget=forms.TextInput(attrs={'placeholder': 'Insurance Company', 'class':'form-control'}))
    insurance_number = forms.CharField(required=True,
                                       widget=forms.TextInput(attrs={'placeholder': 'Insurance Number', 'class':'form-control'}))

    medical_conditions = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Medical Conditions', 'class':'form-control'}))
    preferred_hospital = forms.ModelChoiceField(widget=forms.Select(attrs={'class':'form-control'}),queryset=Hospital.objects.all())

    emergency_contact_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Emergency Contact Name', 'class':'form-control'}))
    emergency_phone_number = forms.RegexField(
        regex=r'^\+?1?\d{9,15}$',
        error_message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
        widget=forms.TextInput(attrs={'placeholder': 'Emergency Contact Number', 'class':'form-control'}))

    def clean_username(self):
        data = self.cleaned_data['username']
        user = User.objects.filter(username=data).first()
        if user is not None:
            raise forms.ValidationError('Username Already Taken', code='invalid')
        return data

    def clean_password_confirm(self):
        password = self.cleaned_data['password']
        confirm = self.cleaned_data['password_confirm']
        if password != confirm:
            raise forms.ValidationError('Passwords do not match.', code='invalid')
        return password


class EmailDataForm(forms.Form):
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all())
    subject = forms.CharField(max_length=30, required=True,
                              widget=forms.TextInput(attrs={'placeholder': 'Subject'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Message'}))


class MedicalPatientForm(forms.Form):
    medical_conditions = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Medical Conditions'}))


class AdmittedForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.patient = Patient.objects.get(pk=kwargs.pop('pk', None))
        super(AdmittedForm, self).__init__(*args, **kwargs)
        if hasattr(self.user, 'doctor'):
            self.fields['admitted_hospital'] = \
                forms.ModelChoiceField(Hospital.objects.filter(doctor=
                                                               self.user.doctor).exclude(admitted_hospital=self.patient),
                                       required=True)
        elif hasattr(self.user, 'nurse') and self.patient.admitted_hospital is None:
            self.fields['admitted_hospital'] = forms.ModelChoiceField(Hospital.objects.filter(nurse=self.user.nurse),
                                                                      required=True)
        elif self.user.is_superuser:
            self.fields['admitted_hospital'] = forms.ModelChoiceField(Hospital.objects.all().exclude(
                admitted_hospital=self.patient))




