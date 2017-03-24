from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from . import views
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^calendar/filtered_events', 'fullcalendar.views.filtered_events', name='filtered_events'),
    url(r'^calendar/', 'fullcalendar.views.index', name='index'),
    url(r'^all_events/', 'fullcalendar.views.all_events', name='all_events'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^appointment/(?P<pk>[0-9]+)', login_required(views.AppointmentView.as_view()), name='detail'),
    url(r'^editAppointment/(?P<pk>[0-9]+)', login_required(views.AppointmentEdit.as_view()), name='editAppointment'),
    url(r'^verifyAppointment/(?P<pk>[0-9]+)', login_required(views.AppointmentVerify.as_view()),
        name='verifyAppointment'),
    url(r'^makeAppointment/$', views.CreateAppointmentView.as_view(), name='makeAppointment'),
    url(r'^deleteAppointment/(?P<pk>[0-9]+)$', login_required(views.DeleteAppointment.as_view()),
        name='deleteAppointment')
)
