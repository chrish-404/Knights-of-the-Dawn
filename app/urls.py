# author 风逝
from django.urls import path, re_path
from django.views.static import serve

from app import views
from comp3820 import settings

app_name = 'app'
urlpatterns =[
    path('login/', views.login),
    path('index/', views.index),
    path('patient_list/', views.patient_list),
    path("launch/", views.launch, name="launch"),
    path("callback/", views.fhir_callback, name="fhir_callback"),
]
