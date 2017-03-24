from django import forms
from main.models import *

# form for used for the patient specified fields
class StaffDataForm(forms.Form):

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
    TYPES = [('doctor', 'Doctor'),
             ('nurse', 'Nurse')]
    type = forms.ChoiceField(choices=TYPES, widget=forms.RadioSelect)
    hospital = forms.ModelChoiceField(Hospital.objects.all())

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
