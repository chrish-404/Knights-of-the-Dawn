'''
@Project ：comp3820 
@Author  ：风&逝
@Date    ：2025/8/24 21:48 
'''

from datetime import datetime, date

import requests


from django.contrib.auth import authenticate, login
import json

from django.contrib.staticfiles import finders
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from app.forms import LoginForm
from app.models import User, MotherChild
from comp3820 import settings


# Create your views here.
def index(request):
    return render(request, 'index.html')

def patient_list(request):
    token_data = request.session.get("fhir_token")
    access_token = token_data.get("access_token")

    iss = settings.FHIR_ISS_URL
    page = int(request.GET.get("p", 1))
    count = int(request.GET.get("c", 5))

    offset = (page - 1) * count
    records = MotherChild.objects.all()[offset:offset + count]

    p_id = []
    for data in records:
        p_id.append(data.mother_id)
        p_id.append(data.child_id)

    fhir_url = f"{iss.rstrip('/')}/Patient?_id={','.join(p_id)}"
    # print(fhir_url)

    response = requests.get(fhir_url, headers={"Authorization": f"Bearer {access_token}"})
    patient_data = response.json()
    # print(patient_data)

    entries = patient_data.get("entry", [])
    # print(entries)
    patients = []

    for e in entries:
        r = e.get("resource", {})
        patients.append({
            "id": r.get("id"),
            "name": " ".join(r.get("name", [{}])[0].get("given", []) + [r.get("name", [{}])[0].get("family", "")]),
            "gender": r.get("gender"),
            "birthDate": r.get("birthDate"),
            "phone": next((t.get("value") for t in r.get("telecom", []) if t.get("system") == "phone"), ""),
            "email": next((t.get("value") for t in r.get("telecom", []) if t.get("system") == "email"), "")
        })
    # print(patients)
    for p in patients:
        birth_date_str = p.get("birthDate")
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        today = datetime.utcnow()
        delta_days = (today - birth_date).days

        if delta_days >= 365:
            p["age"] = f"{delta_days // 365} years"
        else:
            p["age"] = f"{delta_days} days"

    return render(request, "patient-list.html", {
        "patients": patients,
        "page": page,
        "count": count,
        "has_next": len(MotherChild.objects.all()) > offset + count,
        "has_prev": page > 1
    })

    # return render(request, "patient-list.html", {"patient": patient_data})
    # return render(request, "fhir_patient.html", {"patients": patients})


def search_patients(request):
    token_data = request.session.get("fhir_token")
    access_token = token_data.get("access_token")
    fhir_url = settings.FHIR_ISS_URL.rstrip('/')+"/Patient"

    if "?" in fhir_url:
        fhir_url += "&_count=10"
    else:
        fhir_url += "?_count=10"

    query = request.GET.get("q")
    if query:
        fhir_url += "&name="+query
        # fhir_url += "&_id="+query

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(fhir_url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    q=Q()
    patients = []
    for entry in data.get('entry', []):
        patient = entry['resource']
        id_p=patient.get('id')
        q = Q(mother_id=id_p) | Q(child_id=id_p)
        if MotherChild.objects.filter(q).exists():
            patients.append({
                'id': patient.get('id'),
                'name': get_patient_name(patient),
                'gender': patient.get('gender'),
                'age': calculate_age(patient.get('birthDate')) if patient.get('birthDate') else None
            })
    # print(patients)
    return JsonResponse({'patients': patients})


def get_patient_name(patient):
    if not patient.get("name"):
        return "(No name)"
    name_obj = patient["name"][0]
    if "text" in name_obj:
        return name_obj["text"]
    given = name_obj.get("given", [])
    family = name_obj.get("family", "")
    return " ".join(given + [family]).strip() or "(No name)"


def calculate_age(birth_date):
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d").date()
        today = date.today()
        delta_days = (today - birth).days

        if delta_days >= 365:
            return f"{delta_days // 365} years"
        else:
            return f"{delta_days} days"
    except Exception:
        return None
