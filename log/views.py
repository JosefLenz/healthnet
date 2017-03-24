from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from HealthNet import customLog
from .models import *
from .forms import *
from main.models import Prescription
from fullcalendar.models import CalendarEvent
from django.views import generic
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
import datetime
from django.template import loader
from django.utils import timezone


# A view for the supplementary admin page
# TODO: Finish, make more features for it
@login_required
def AdminView(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    template = loader.get_template('admin.html')
    # Template goes in render instead template = loader.get_template('main/admin.html')
    today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
    latest_logs = Log.objects.order_by('date')[:10]
    daily_login = Log.objects.filter(type='LOGON', date__range=(today_min, today_max)).count()
    prescriptions = Prescription.objects.all()
    prescription_number = Log.objects.filter(type='PRESCRB').count()
    medicines = []
    max = 0
    max_medication_name = ""
    for medicine in prescriptions:
        num = 0
        check = medicine.medicationName
        for medicine2 in prescriptions:
            if check == medicine2.medicationName:
                num += 1
        if num > max:
            max = num
            max_medication_name = check

        max = 0
        hospitals = Hospital.objects.all()
        busiest_hospital = ""
        for hospital in hospitals:
            hos_patients = Patient.objects.filter(admitted_hospital=hospital).count()
            if hos_patients >= max:
                max = hos_patients
                busiest_hospital = hospital.hospitalName

        patient_count = Patient.objects.all().count()
        doctor_count = Doctor.objects.all().count()
        nurse_count = Nurse.objects.all().count()
    context = {
        'hospitals': hospitals,
        'latest_logs': latest_logs,
        'daily_login': daily_login,
        'max_medication_name': max_medication_name,
        'patient_count': patient_count,
        'doctor_count': doctor_count,
        'nurse_count': nurse_count,
        'busiest_hospital': busiest_hospital,
    }

    if request.method == 'POST':
        hospital_id = request.POST.get('ID')
        return redirect(reverse('main:hospital', kwargs={'pk': hospital_id}))

    return HttpResponse(template.render(context, request))


class StaffRegisterView(generic.FormView):
    form_class = StaffDataForm
    template_name = 'staffregister.html'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            return super(generic.FormView, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_success_url(self):
        return reverse_lazy('main:adminc')

    def form_valid(self, form):

        username = form.cleaned_data['username']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        date_of_birth = form.cleaned_data['date_of_birth']

        type = form.cleaned_data['type']
        hospital = form.cleaned_data['hospital']

        user = User.objects.create_user(username, email, password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        if type == 'doctor':
            staff = Doctor.objects.create(user=user)
            staff.hospitals.add(hospital)
        elif type == 'nurse':
            staff = Nurse.objects.create(user=user,
                                         hospital=hospital)
        staff.save()
        customLog.add_log("New %s named %s registered to HealthNet" % (type, username), 'REGIST')
        return super(StaffRegisterView, self).form_valid(form)


class HospitalStatView(generic.DetailView):
    template_name = 'hospital.html'
    model = Hospital

    def get_context_data(self, **kwargs):
        context = super(HospitalStatView, self).get_context_data(**kwargs)
        context['nurse_count'] = Nurse.objects.filter(hospital=self.object).count()
        context['doctor_count'] = Doctor.objects.filter(hospitals__in=[self.object]).count()
        context['patient_count'] = Patient.objects.filter(admitted_hospital=self.object).count()
        startdate = datetime.date.today()
        enddate1 = startdate - datetime.timedelta(days=7)
        enddate2 = startdate + datetime.timedelta(days=7)
        context['weekly_admissions'] = Log.objects.filter(type='ADMIT', date__range=([enddate1, startdate])).count()
        context['weekly_appointments'] = CalendarEvent.objects.filter(start__range=([startdate, enddate2])).count()

        return context
