# author 风逝
from django.urls import path, re_path
from django.views.static import serve

from app.views import public, launch
from comp3820 import settings

app_name = 'app'
urlpatterns = [
    path('login/', launch.login_view, name='login'),
    path('index/', public.index),
    path('patient_list/', public.patient_list),
    path("launch/", launch.launch, name="launch"),
    path("callback/", launch.fhir_callback, name="fhir_callback"),
    path('search/', public.search_patients, name='search_patients'),
]
