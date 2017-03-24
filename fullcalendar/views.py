from django.shortcuts import render
from django.http import HttpResponse
from .models import CalendarEvent
from .util import events_to_json, calendar_options
from main.views import FormMixin
from main.forms import BooleanForm
from django.views import generic
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .forms import *
from django.core.exceptions import PermissionDenied
from datetime import datetime
from django.core.urlresolvers import reverse_lazy, reverse
from HealthNet import customLog
from postman.models import *

OPTIONS = """{  timeFormat: "H:mm",
                header: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'month,agendaWeek,agendaDay',
                },
                allDaySlot: false,
                firstDay: 1,
                weekMode: 'liquid',
                slotMinutes: 15,
                defaultEventMinutes: 30,
                minTime: 0,
                maxTime: 24,
                editable: false,
                dayClick: function(date, allDay, jsEvent, view) {
                    if (allDay) {
                        $('#calendar').fullCalendar('gotoDate', date)
                        $('#calendar').fullCalendar('changeView', 'agendaDay')
                    }
                },
                eventClick: function(event, jsEvent, view) {
                    window.location.href = '/appointment/'+event.id;
                },
            }"""


def index(request):
    event_url = 'filtered_events'
    return render(request, 'FullCalendar/index.html', {'calendar_config_options': calendar_options(event_url, OPTIONS)})

def all_events(request):
    # Use some decorator so only admins can access this URL?

    events = CalendarEvent.objects.all()
    return HttpResponse(events_to_json(events), content_type='application/json')

@login_required
def filtered_events(request):
    user = request.user
    events = CalendarEvent.objects.all()

    if hasattr(user, 'patient'):
        events = CalendarEvent.objects.all().filter(patient=user.patient)
    elif hasattr(user, 'doctor'):
        events = CalendarEvent.objects.all().filter(doctor=user.doctor)
    elif hasattr(user, 'nurse'):
        events = CalendarEvent.objects.all().filter(hospital=user.nurse.hospital)

    return HttpResponse(events_to_json(events), content_type='application/json')

'''the create appointment view creates an appointment for the calendar dependent on the type of user'''
class CreateAppointmentView(FormMixin, generic.FormView):
    template_name = 'main/makeAppointment.html'

    def get_form_class(self):
        user = self.request.user
        if hasattr(user, 'patient'):
            return PatientAppointment
        elif hasattr(user, 'doctor'):
            return DoctorAppointment
        elif hasattr(user, 'nurse'):
            return NurseAppointment

    def get_success_url(self):
        return reverse_lazy('fullcalendar:index')

    def get_initial(self):
        user = self.request.user

        if hasattr(user, 'patient'):
            initial = {'hospital': user.patient.preferred_hospital,
                       'start_date': timezone.now().date(),
                       'start_time': timezone.now().time()}
        else:
            initial = {'start_date': timezone.now().date(), }
        return initial

    def form_valid(self, form):
        user = self.request.user
        if hasattr(user, 'patient'):
            event = CalendarEvent.objects.create(patient=user.patient,
                                                 doctor=form.cleaned_data['doctor'],
                                                 hospital=form.cleaned_data['hospital'],
                                                 title=form.cleaned_data['description'],
                                                 start=datetime.combine(form.cleaned_data['start_date'],
                                                                        form.cleaned_data['start_time']),
                                                 end=datetime.combine(form.cleaned_data['start_date'],
                                                                      form.cleaned_data['start_time'])+ timedelta(hours=1))
            message = Message.objects.create()
            message.sender = user
            message.recipient = event.doctor.user
            message.subject = 'New Appointment'
            message.body = event.patient.get_name() + " has made an appointment, view and confirm from your calendar"
            message.moderation_status = 'a'

            event.save()
            message.save()
        elif hasattr(user, 'doctor'):
            event = CalendarEvent.objects.create(patient=form.cleaned_data['patient'],
                                                 doctor=user.doctor,
                                                 hospital=form.cleaned_data['hospital'],
                                                 title=form.cleaned_data['description'],
                                                 start=datetime.combine(form.cleaned_data['start_date'],
                                                                        form.cleaned_data['start_time']),
                                                 end=datetime.combine(form.cleaned_data['start_date'],
                                                                      form.cleaned_data['start_time'])+ timedelta(hours=1))
            message = Message.objects.create()
            message.sender = user
            message.recipient = event.patient.user
            message.subject = 'New Appointment'
            message.body = event.doctor.get_name() + " has made an appointment for you, view from your calendar"
            message.moderation_status = 'a'

            event.save()
            message.save()
        elif hasattr(user, 'nurse'):
            event = CalendarEvent.objects.create(patient=user.cleaned_data['patient'],
                                                 doctor=form.cleaned_data['doctor'],
                                                 hospital=form.cleaned_data['hospital'],
                                                 title=form.cleaned_data['description'],
                                                 start=datetime.combine(form.cleaned_data['start_date'],
                                                                        form.cleaned_data['start_time']),
                                                 end=datetime.combine(form.cleaned_data['start_date'],
                                                                      form.cleaned_data['start_time'])+ timedelta(hours=1))

            event.save()
        customLog.add_log("%s created an appointment" % user.username, 'APPOINC')
        return super(CreateAppointmentView, self).form_valid(form)

class AppointmentView(FormMixin, generic.DetailView):

    model = CalendarEvent

    template_name = 'fullcalendar/event_detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.canverify = hasattr(request.user, 'doctor')
        self.event = self.get_event()
        return super(AppointmentView, self).dispatch(request, *args, **kwargs)

    def get_event(self):
        return CalendarEvent.objects.get(pk=self.kwargs['pk'])


class AppointmentVerify(generic.FormView):
    template_name = 'fullcalendar/event_verify.html'
    form_class = BooleanForm

    def dispatch(self, request, *args, **kwargs):
        self.event = self.get_event()
        return super(AppointmentVerify, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('fullcalendar:detail', kwargs={'pk': self.kwargs['pk']})

    def get_event(self):
        return CalendarEvent.objects.get(pk=self.kwargs['pk'])

    def form_valid(self, form):
        self.event.verified = form.cleaned_data['confirm']
        self.event.save()
        return super(AppointmentVerify, self).form_valid(form)


'''view for displaying an appointment, retrieves the correct type of information based on user type
and allows for modification of appointment'''
class AppointmentEdit(FormMixin, generic.FormView):

    template_name = 'fullcalendar/event_edit.html'

    def dispatch(self, request, *args, **kwargs):
        self.event = self.get_event()
        return super(AppointmentEdit, self).dispatch(request, *args, **kwargs)

    def get_event(self):
        return CalendarEvent.objects.get(pk=self.kwargs['pk'])

    def get_form_class(self):
        user = self.request.user
        if hasattr(user, 'patient'):
            return PatientAppointment
        elif hasattr(user, 'doctor'):
            return DoctorAppointment
        elif hasattr(user, 'nurse'):
            return NurseAppointment

    def get_success_url(self):
        return reverse('fullcalendar:detail', kwargs={'pk': self.kwargs['pk']})

    def get_initial(self):
        event = self.get_event()
        user = self.request.user
        if hasattr(user, 'patient'):
            initial = {
                'hospital': event.hospital,
                'patient': event.patient,
                'doctor': event.doctor,
                'start_date': event.start.date(),
                'start_time': event.start.time(),
                'description': event.title
            }
            if user.patient != event.patient:
                raise PermissionDenied
        elif hasattr(user, 'doctor'):
            initial = {
                'hospital': event.hospital,
                'patient': event.patient,
                'doctor': event.doctor,
                'start_date': event.start.date(),
                'start_time': event.start.time(),
                'description': event.title,
                'verified': event.verified
            }
            if user.doctor != event.doctor:
                raise PermissionDenied
        elif hasattr(user, 'nurse'):
            initial = {
                'hospital': event.hospital,
                'patient': event.patient,
                'doctor': event.doctor,
                'start_date': event.start.date(),
                'start_time': event.start.time(),
                'description': event.title
            }
            if user.urse.hospital != event.hospital:
                raise PermissionDenied
        else:
            initial = {}

        return initial

    def form_valid(self, form):
        user = self.request.user
        if hasattr(user, 'patient'):
            event = self.get_event()
            event.patient = user.patient
            event.doctor = form.cleaned_data['doctor']
            event.hospital = form.cleaned_data['hospital']
            event.title = form.cleaned_data['description']
            event.start = datetime.combine(form.cleaned_data['start_date'], form.cleaned_data['start_time'])
            event.verified = False

            message = Message.objects.create()
            message.sender = user
            message.recipient = event.doctor.user
            message.subject = 'Edited Appointment'
            message.body = event.patient.get_name() + " has edited an appointment, view and confirm from your calendar"
            message.moderation_status = 'a'

            event.save()
            message.save()
        elif hasattr(user, 'doctor'):
            event = self.get_event()
            event.patient = form.cleaned_data['patient']
            event.doctor = user.doctor
            event.hospital = form.cleaned_data['hospital']
            event.title = form.cleaned_data['description']
            event.start = datetime.combine(form.cleaned_data['start_date'], form.cleaned_data['start_time'])

            message = Message.objects.create()
            message.sender = user
            message.recipient = event.patient.user
            message.subject = 'Edited Appointment'
            message.body = event.doctor.get_name() + " has edited an appointment for you, view from your calendar"
            message.moderation_status = 'a'

            event.save()
            message.save()
        elif hasattr(user, 'nurse'):
            event = self.get_event()
            event.patient = form.cleaned_data['patient']
            event.doctor = form.cleaned_data['doctor']
            event.hospital = form.cleaned_data['hospital']
            event.title = form.cleaned_data['description']
            event.start = datetime.combine(form.cleaned_data['start_date'], form.cleaned_data['start_time'])

            event.save()
        customLog.add_log("%s modified appointment with ID %d" % (user.username, self.get_event().ID), 'APPOINE')
        return super(AppointmentEdit, self).form_valid(form)


'''delete view used for deleting appointments'''
class DeleteAppointment(generic.DeleteView):
    model = CalendarEvent
    success_url = reverse_lazy('fullcalendar:index')
    template_name = 'fullcalendar/event_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        if hasattr(self.request.user, 'nurse'):
            raise PermissionDenied
        else:
            customLog.add_log("%s deleted appointment with ID %s" % (self.request.user.username, self.kwargs['pk']), 'APPOINE')
            return super(DeleteAppointment, self).delete(request, *args, **kwargs)









