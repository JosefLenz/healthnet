from django.conf.urls import url
from django.conf import settings
from . import views
from log.views import *
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required


app_name = 'main'

# url's for main application
urlpatterns = [
    # URL for Djangos logout solution, redirects to our own success page after logging them out
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/logout_success/'}),
    # Landing page for logging out users
    url(r'^logout_success/$', views.LogoutSuccess.as_view(), name='logout_success'),
    # URL for the profile page
    url(r'^profile/$', views.profileView, name='profile'),
    # URL for the about page
    url(r'^about/$', login_required(views.AboutView), name='about'),
    # URL for new Home Page
    url(r'^$', views.HomeView.as_view(), name='home'),
    # URL for the contact page
    url(r'^contact/$', login_required(views.ContactView.as_view()), name='contact'),
    # URL for the edit profile page
    url(r'^edit_profile/$', login_required(views.ProfileUpdateView.as_view()), name='edit_profile'),
    # URL for the regrestration page
    url(r'^register/$', views.RegisterView.as_view(), name='register1'),
    # URL for the message doctor page
    url(r'^message/$', login_required(views.MessageView.as_view()), name='message'),
    # URL for the prescriptions page
    url(r'^prescription/(?P<pk>[0-9]+)$', login_required(views.WritePrescriptionView.as_view()), name='prescribe'),
    # URL to access the admin page
    url(r'^adminc/$', AdminView, name='adminc'),
    url(r'^staffregist/$', login_required(StaffRegisterView.as_view()), name='staffregist'),
    url(r'^hospital/(?P<pk>[0-9]+)$', login_required(HospitalStatView.as_view()), name='hospital'),
    # URL for the Test page
    url(r'^test/(?P<pk>[0-9]+)$', login_required(views.TestCreateView.as_view()), name='test'),
    url(r'^editTest/(?P<pk>[0-9]+)$', login_required(views.TestEditView.as_view()), name='editTest'),
    url(r'^deleteTest/(?P<pk>[0-9]+)$', login_required(views.DeleteTest.as_view()),
        name='deleteTest'),
    url(r'^releaseTest/(?P<pk>[0-9]+)$', login_required(views.TestReleaseView.as_view()),
        name='releaseTest'),
    url(r'^deletePrescription/(?P<pk>[0-9]+)$', login_required(views.DeletePrescription.as_view()),
        name='deletePrescription'),
    # URL for the view_patient page
    url(r'^view_patient/(?P<pk>[0-9]+)$', login_required(views.PatientView.as_view()), name='viewPatient'),
    url(r'^discharge_patient/(?P<pk>[0-9]+)$', login_required(views.DischargePatientView.as_view()), name='discharge'),
    url(r'^transfer_patient/(?P<pk>[0-9]+)$', login_required(views.TransferPatientView.as_view()), name='transfer'),
    url(r'^admit_patient/(?P<pk>[0-9]+)$', login_required(views.AdmitPatientView.as_view()), name='admit'),
    #URL for the page the patient list page
    url(r'^patients/$', login_required(views.PatientListView.as_view()), name='patients'),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT,}),
    url(r'confirm_download/$', login_required(views.ConfirmDownloadView.as_view()), name='confirm_download'),
    url(r'confirm_test_download/$', login_required(views.ConfirmTestDownloadView.as_view()), name='confirm_test_download'),
    url(r'download_info/$', login_required(views.DownloadProfileView), name='download'),
    url(r'download_test_info/$', login_required(views.DownloadTestView), name='download_test_info')
]

urlpatterns += staticfiles_urlpatterns()
#urlpatterns += static(settings.MEDIA_URL, document_root=MEDIA_ROOT)