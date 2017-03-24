from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from HealthNet import customLog
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.views.generic.base import ContextMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from HealthNet.settings import BASE_DIR

import logging
import random
import csv
import zipfile
import io

from .models import *
from .forms import *


logger = logging.getLogger(__name__)


# Forbids access if user is not a doctor, admin, or nurse.
class StaffOnlyMixin(ContextMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if hasattr(user, 'doctor') or hasattr(user, 'nurse') or user.is_superuser:
            return super(generic.ListView, self).dispatch(request, *args, **kwargs)
        else:
           raise PermissionDenied


class FormMixin(ContextMixin):
    def form_invalid(self, form):
        logger.error('Something went wrong!')
        return self.render_to_response(self.get_context_data(form=form))


class LogoutSuccess(generic.TemplateView):
    template_name = 'main/logout.html'  


@login_required
def profileView(request):
    if hasattr(request.user, 'doctor') or hasattr(request.user, 'nurse'):
        return redirect('/patients/')
    if request.user.is_superuser:
        return redirect('/admin/')
    template = loader.get_template('main/profile.html')

    # Sets the object the page is displaying to the current user.
    u = request.user
    # Gets the context list for use in the HTML template
    context = {
        'username': u.username,
        'email': u.email,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'address_line1': u.patient.address_line1,
        'address_line2': u.patient.address_line2,
        'address_city': u.patient.address_city,
        'address_region': u.patient.address_region,
        'address_zip': u.patient.address_zip,
        'address_country': u.patient.address_country,
        'insurance_company': u.patient.insurance_company,
        'insurance_number': u.patient.insurance_number,
        'ID': u.patient.ID,
        'medical_conditions': u.patient.medical_conditions,
        'preferred_hospital': u.patient.preferred_hospital,
        'emergency_contact': u.patient.emergency_contact,
        'emergency_contact_number': u.patient.emergency_contact_number,
        'admitted_hospital': u.patient.admitted_hospital,
        'prescriptions': Prescription.objects.filter(patient=u.patient),
        'tests': Test.objects.filter(testPatient=u.patient),
        }
    return HttpResponse(template.render(context, request))


class TestCreateView(generic.FormView):
    template_name = 'main/createtest.html'
    form_class = TestForm

    def get_success_url(self):
        return reverse('main:viewPatient', kwargs={'pk': self.patient.ID})

    def dispatch(self, request, *args, **kwargs):
        self.patient = self.get_patient()
        return super(TestCreateView, self).dispatch(request, *args, **kwargs)

    def get_patient(self):
        return Patient.objects.get(pk=self.kwargs['pk'])

    def get_initial(self):
        initial = {'test_doctor': self.request.user.doctor.get_name(), }
        return initial

    def form_valid(self, form):
        test_name = form.cleaned_data['test_name']
        test_comment = form.cleaned_data['test_comment']
        test_image = form.cleaned_data['test_image']
        test_doctor = form.cleaned_data['test_doctor']
        test = Test.objects.create(testName=test_name,
                                   testPatient=self.patient,
                                   testComment=test_comment,
                                   testImage=test_image,
                                   testDoctor=test_doctor,
                                   )
        test.save()
        customLog.add_log("User %s test added" % (test.testPatient.user.username), 'TESTCR')
        return super(TestCreateView, self).form_valid(form)


class TestReleaseView(generic.FormView):
    template_name = 'main/viewtest.html'
    form_class = BooleanForm

    def dispatch(self, request, *args, **kwargs):
        self.kwargs['patient'] = Patient.objects.get(test__pk=self.kwargs['pk']).ID
        self.test = self.get_test()
        return super(TestReleaseView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return '/view_patient/'+str(Patient.objects.get(test__pk=self.kwargs['pk']).ID)

    def get_test(self):
        return Test.objects.get(pk=self.kwargs['pk'])

    def form_valid(self, form):
        self.test.testReleased = form.cleaned_data['confirm']
        self.test.save()
        return super(TestReleaseView, self).form_valid(form)

class TestEditView(generic.FormView):
    template_name = 'main/edittest.html'
    form_class = TestForm

    def get_form(self, form_class=None):
        form = super(TestEditView, self).get_form(form_class)
        form.fields.pop('test_name')
        return form

    def dispatch(self, request, *args, **kwargs):
        self.kwargs['patient'] = Patient.objects.get(test__pk=self.kwargs['pk']).ID
        self.test = self.get_test()
        return super(TestEditView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return '/view_patient/'+str(Patient.objects.get(test__pk=self.kwargs['pk']).ID)

    def get_test(self):
        return Test.objects.get(pk=self.kwargs['pk'])

    def get_initial(self):
        initial = {'test_doctor': self.test.testDoctor,
                   'test_name': self.test.testName,
                   'test_comment': self.test.testComment,
                   'test_image': self.test.testImage,
                   }
        return initial

    def form_valid(self, form):
        self.test.testComment = form.cleaned_data['test_comment']
        self.test.testImage = form.cleaned_data['test_image']
        self.test.save()
        customLog.add_log("User %s test edited" % (self.test.testPatient.user.username), 'TESTED')
        return super(TestEditView, self).form_valid(form)



class DeleteTest(generic.DeleteView):
    model = Test
    template_name = 'main/test_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.kwargs['patient'] = Patient.objects.get(test__pk=self.kwargs['pk']).ID
        return super(DeleteTest, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return '/view_patient/'+str(Patient.objects.get(test__pk=self.kwargs['pk']).ID)

    def delete(self, request, *args, **kwargs):
        if hasattr(self.request.user, 'nurse') or hasattr(self.request.user, 'patient'):
            raise PermissionDenied
        else:
            customLog.add_log("%s deleted Test with ID %s" % (self.request.user.username, self.kwargs['pk']),
                              'TESTDL')
            return super(DeleteTest, self).delete(request, *args, **kwargs)


class WritePrescriptionView (generic.FormView):
    template_name = 'main/prescription.html'
    form_class = PrescriptionForm

    def get_success_url(self):
        return reverse('main:viewPatient', kwargs={'pk': self.patient.ID})

    def dispatch(self, request, *args, **kwargs):
        self.patient = self.get_patient()
        return super(WritePrescriptionView, self).dispatch(request, *args, **kwargs)

    def get_patient(self):
        return Patient.objects.get(pk=self.kwargs['pk'])


    def get_initial(self):
        initial = {'prescribing_doctor': self.request.user.doctor.get_name(),
                   'patient': Patient.objects.get(pk=self.kwargs['pk']),}
        return initial

    def form_valid(self, form):
        #patient = form.cleaned_data['patient']
        medication_name = form.cleaned_data['medication_name']
        medication_directions = form.cleaned_data['medication_directions']
        medication_amount = form.cleaned_data['medication_amount']
        medication_type = form.cleaned_data['medication_type']
        medication_refills = form.cleaned_data['medication_refills']
        prescribing_doctor = form.cleaned_data['prescribing_doctor']

        prescription = Prescription.objects.create(patient=self.patient,
                                                   medicationName=medication_name,
                                                   medicationDirections=medication_directions,
                                                   medicationAmount=medication_amount,
                                                   medicationType=medication_type,
                                                   medicationRefills=medication_refills,
                                                   prescribingDoctor=prescribing_doctor)
        prescription.save()
        customLog.add_log("User %s prescription added" % (prescription.patient.user.username), 'PRESCRB')
        return super(WritePrescriptionView, self).form_valid(form)


class DeletePrescription(generic.DeleteView):
    model = Prescription
    template_name = 'main/prescription_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.kwargs['patient'] = Patient.objects.get(prescription__ID=self.kwargs['pk']).ID
        return super(DeletePrescription, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return '/view_patient/'+str(Patient.objects.get(prescription__ID=self.kwargs['pk']).ID)

    def delete(self, request, *args, **kwargs):
        if hasattr(self.request.user, 'nurse') or hasattr(self.request.user, 'patient'):
            raise PermissionDenied
        else:
            customLog.add_log("%s deleted prescription with ID %s" % (self.request.user.username, self.kwargs['pk']),
                              'PRESCRP')
            return super(DeletePrescription, self).delete(request, *args, **kwargs)


# View for updating a patient's info
class ProfileUpdateView (FormMixin, generic.FormView):
    template_name = 'main/edit_profile.html'
    form_class = PatientDataForm

    def get_form(self, form_class=None):
        form = super(ProfileUpdateView, self).get_form(form_class)
        form.fields.pop('username')
        return form

    def get_success_url(self):
        return reverse_lazy('main:profile')

    # Gets the initial values to fill the fields with
    # Uses data from user and patient as initial values.
    def get_initial(self):
        user = self.request.user
        initial = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'date_of_birth': user.patient.date_of_birth,
            'address1': user.patient.address_line1,
            'address2': user.patient.address_line2,
            'city': user.patient.address_city,
            'region': user.patient.address_region,
            'zip': user.patient.address_zip,
            'country': user.patient.address_country,
            'insurance_company': user.patient.insurance_company,
            'insurance_number': user.patient.insurance_number,
            'medical_conditions': user.patient.medical_conditions,
            'preferred_hospital': user.patient.preferred_hospital,
            'emergency_contact_name': user.patient.emergency_contact,
            'emergency_phone_number': user.patient.emergency_contact_number,
            'avatar': user.patient.avatar
        }
        return initial

    # runs if the form fields are all valid.
    # Sets all of the data gathered to fields in the models, and then saves models.
    def form_valid(self, form):
        user = self.request.user
        patient = user.patient  # fields fill out information for user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user.set_password(password)
        patient.date_of_birth = form.cleaned_data['date_of_birth']
        patient.avatar = form.cleaned_data['avatar']

        patient.address_line1 = form.cleaned_data['address1']
        patient.address_line2 = form.cleaned_data['address2']
        patient.address_city = form.cleaned_data['city']
        patient.address_region = form.cleaned_data['region']
        patient.address_zip = form.cleaned_data['zip']
        patient.address_country = form.cleaned_data['country']

        patient.insurance_company = form.cleaned_data['insurance_company']
        patient.insurance_number = form.cleaned_data['insurance_number']

        patient.medical_conditions = form.cleaned_data['medical_conditions']
        patient.preferred_hospital = form.cleaned_data['preferred_hospital']

        patient.emergency_contact = form.cleaned_data['emergency_contact_name']
        patient.emergency_contact_number = form.cleaned_data['emergency_phone_number']

        patient.save()  # saves changes
        user.save()
        login_user = authenticate(username=user.username, password=password)  # logs user back in after save
        login(self.request, login_user)
        customLog.add_log("%s edited his profile info" % user.username, 'EDIT')  # logs changes
        return super(ProfileUpdateView,self).form_valid(form)


# view for registering a patient
class RegisterView(generic.FormView):
    form_class = PatientDataForm
    template_name = 'main/register_1.html'

    def get_success_url(self):
        return reverse_lazy('login')

    # if all fields are valid creates saves and logs the new user
    def form_valid(self, form):
        username = form.cleaned_data['username']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        date_of_birth = form.cleaned_data['date_of_birth']

        address_line1 = form.cleaned_data['address1']
        address_line2 = form.cleaned_data['address2']
        address_city = form.cleaned_data['city']
        address_region = form.cleaned_data['region']
        address_zip = form.cleaned_data['zip']
        address_country = form.cleaned_data['country']

        insurance_company = form.cleaned_data['insurance_company']
        insurance_number = form.cleaned_data['insurance_number']

        medical_conditions = form.cleaned_data['medical_conditions']
        preferred_hospital = form.cleaned_data['preferred_hospital']

        emergency_contact = form.cleaned_data['emergency_contact_name']
        emergency_contact_number = form.cleaned_data['emergency_phone_number']

        user = User.objects.create_user(username, email, password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        patient = Patient.objects.create(user=user,
                                         address_line1=address_line1,
                                         address_line2=address_line2,
                                         address_city=address_city,
                                         address_region=address_region,
                                         address_zip=address_zip,
                                         address_country=address_country,
                                         date_of_birth=date_of_birth,
                                         insurance_company=insurance_company,
                                         insurance_number=insurance_number,
                                         medical_conditions=medical_conditions,
                                         preferred_hospital=preferred_hospital,
                                         emergency_contact=emergency_contact,
                                         emergency_contact_number=emergency_contact_number,
                                         )
        patient.save()
        customLog.add_log("New patient %s registered to HealthNet" % username, 'REGIST')
        return super(RegisterView, self).form_valid(form)

class MessageView(generic.FormView):
    form_class = EmailDataForm #whole class needs to be redone
    template_name = 'main/message.html'
    success_url = '/'

    def form_valid(self, form):
        user = self.request.user
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['message']
        doctor = form.cleaned_data['doctor']


        return send_mail(#none of this works yay
            subject,
            message,
            user.email,
            [doctor.user.email],
            fail_silently=False,
        )


class PatientListView(StaffOnlyMixin, generic.ListView):
    template_name = 'main/patient_list.html'
    model = Patient

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'doctor') or user.is_superuser:
            return Patient.objects.all()
        elif hasattr(user, 'nurse'):
            return Patient.objects.filter(admitted_hospital=user.nurse.hospital)


class PatientView(FormMixin, generic.FormView):
    form_class = MedicalPatientForm
    template_name = 'main/view_patient.html'

    def get_success_url(self):
        return reverse_lazy('main:patients')

    def get_initial(self):
        initial = {
            'medical_conditions': self.patient.medical_conditions,
        }
        return initial

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if hasattr(user, 'doctor') or hasattr(user, 'nurse') or user.is_superuser:
            self.patient = self.get_patient()
            self.isdoctor = hasattr(request.user, 'doctor')
            self.prescriptions = Prescription.objects.filter(patient=self.patient)
            self.tests = Test.objects.filter(testPatient=self.patient)
            return super(PatientView, self).dispatch(request, *args, **kwargs)
        else:
           raise PermissionDenied

    def get_patient(self):
        return Patient.objects.get(pk=self.kwargs['pk'])

    def form_valid(self, form):

        self.patient.medical_conditions = form.cleaned_data['medical_conditions']
        self.patient.save()  # saves changes
        customLog.add_log("%s edited %s medical info" % (self.request.user.username, self.patient), 'EDIT')  # logs changes
        return super(PatientView,self).form_valid(form)


class AdmitPatientView(generic.FormView):
    form_class = AdmittedForm

    template_name = 'main/admit_patient.html'

    def get_success_url(self):
        return reverse('main:viewPatient', kwargs={'pk': self.patient.ID})

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if hasattr(user, 'doctor') or hasattr(user, 'nurse') or user.is_superuser:
            self.patient = self.get_patient()
            return super(AdmitPatientView, self).dispatch(request, *args, **kwargs)
        else:
           raise PermissionDenied

    def get_patient(self):
        return Patient.objects.get(pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super(AdmitPatientView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['pk'] = self.kwargs['pk']
        return kwargs

    def form_valid(self, form):
        self.patient.admitted_hospital = form.cleaned_data['admitted_hospital']
        self.patient.save()  # saves changes
        customLog.add_log("%s admitted %s to %s" % (self.request.user.username, self.patient,
                                                    self.patient.admitted_hospital), 'ADMIT')  # logs changes
        return super(AdmitPatientView,self).form_valid(form)


class TransferPatientView(generic.FormView):
    form_class = AdmittedForm

    template_name = 'main/transfer_patient.html'

    def get_success_url(self):
        return reverse('main:viewPatient', kwargs={'pk': self.patient.ID})

    def get_initial(self):
        initial = {
            'admitted_hospital': self.patient.admitted_hospital,
        }
        return initial

    def dispatch(self, request, *args, **kwargs):
        self.patient = self.get_patient()
        user = request.user
        if hasattr(user, 'doctor') or user.is_superuser:
            return super(TransferPatientView, self).dispatch(request, *args, **kwargs)
        else:
           raise PermissionDenied

    def get_patient(self):
        return Patient.objects.get(pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super(TransferPatientView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['pk'] = self.kwargs['pk']
        return kwargs

    def form_valid(self, form):
        self.patient.admitted_hospital = form.cleaned_data['admitted_hospital']
        self.patient.save()  # saves changes
        customLog.add_log("%s transferred %s to %s" % (self.request.user.username, self.patient,
                                                    self.patient.admitted_hospital), 'TRANSFR')  # logs changes
        return super(TransferPatientView,self).form_valid(form)


class DischargePatientView(generic.FormView):
    form_class = BooleanForm

    template_name = 'main/discharge_patient.html'

    def get_success_url(self):
        return reverse('main:viewPatient', kwargs={'pk': self.patient.ID})

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if hasattr(user, 'doctor'):
            self.patient = self.get_patient()
            return super(DischargePatientView, self).dispatch(request, *args, **kwargs)
        else:
           raise PermissionDenied

    def get_patient(self):
        return Patient.objects.get(pk=self.kwargs['pk'])

    def form_valid(self, form):
        if form.cleaned_data['confirm']:
            hospital = self.patient.admitted_hospital
            self.patient.admitted_hospital = None
            self.patient.save()  # saves changes
            customLog.add_log("%s discharged %s from %s" % (self.request.user.username, self.patient,
                                                            hospital), 'DISCHRG')  # logs changes
        return super(DischargePatientView,self).form_valid(form)


# view for contact page
class ContactView(generic.TemplateView):
    template_name = 'main/contact.html'


class HomeView(generic.TemplateView):
    template_name = 'main/home.html'


# view for about page
def AboutView(request):
    template = loader.get_template('main/about.html')
    template2 = loader.get_template('main/about2.html')
    template3 = loader.get_template('main/about3.html')
    numb = random.random() * 10
    print(numb)
    if numb <= 3:
         return HttpResponse(template.render(request))
    elif numb > 3 and numb <= 6:
        return HttpResponse(template2.render(request))
    else:
        return HttpResponse(template3.render(request))


# View for downloading profile information
def DownloadProfileView(request):
    u = request.user
    # If user is not a patient returns an empty response
    if hasattr(u, 'patient'):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + u.patient.get_name() + '_info.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Birthday', 'Address', 'Insurance Company', 'Insurance Number',
                        'Emergency Contact', 'Emergency Contact Number', 'Conditions', 'Preferred Hospital',
                        'Admitted Hospital'])
        addressString = u.patient.address_line1 + ' ' + u.patient.address_line2 + ' ' + u.patient.address_city + ' ' + \
                        u.patient.address_region + ' ' + u.patient.address_zip + ' ' + u.patient.address_country
        writer.writerow([u.get_full_name(), u.patient.date_of_birth, addressString, u.patient.insurance_company,
                         u.patient.insurance_number, u.patient.emergency_contact, u.patient.emergency_contact_number,
                         u.patient.medical_conditions, u.patient.preferred_hospital, u.patient.admitted_hospital])
    else:
        return HttpResponseRedirect('/')

    return response


def DownloadTestView(request):
    u = request.user
    if hasattr(u, 'patient'):
        tests = Test.objects.filter(testPatient=u.patient, testReleased=True)
        s = io.BytesIO()
        zf = zipfile.ZipFile(s, 'w')
        sTemp = io.StringIO()
        writer = csv.writer(sTemp)
        writer.writerow(['Test Name', 'Doctor', 'Patient', 'Comments'])
        for t in tests:
            writer.writerow([t.testName, t.testDoctor, t.testPatient, t.testComment])
            try:
                zf.write(BASE_DIR + t.testImage.url, t.testName + t.testImage.url[-4:])
            except ValueError:
                pass

        zf.writestr(u.get_full_name() + '_test_info.csv', sTemp.getvalue())
        zf.close()

        response = HttpResponse(s.getvalue(), content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename="' + u.get_full_name() + '_tests.zip"'
        return response
    else:
        return HttpResponseRedirect('/')


class ConfirmDownloadView(generic.TemplateView):
    template_name = 'main/confirm_download.html'

class ConfirmTestDownloadView(generic.TemplateView):
    template_name = 'main/confirm_test_download.html'

