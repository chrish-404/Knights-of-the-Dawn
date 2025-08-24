import hashlib
import secrets
from datetime import datetime, date

import requests
import base64

from django.contrib.auth import authenticate, login
import json

from django.contrib.staticfiles import finders
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
    if not token_data:
        return redirect("app:login")

    access_token = token_data.get("access_token")
    if not access_token:
        return HttpResponse("No access token found")

    iss = request.session.get("iss")
    page = int(request.GET.get("page", 1))
    count = int(request.GET.get("count", 5))

    offset = (page - 1) * count
    mc_records = MotherChild.objects.all()[offset:offset + count]

    patient_ids = []
    for mc in mc_records:
        if mc.mother_id:
            patient_ids.append(mc.mother_id)
        if mc.child_id:
            patient_ids.append(mc.child_id[4:])

    if not patient_ids:
        return render(request, "patient-list.html", {"patients": []})

    fhir_url = f"{iss.rstrip('/')}/Patient?_id={','.join(patient_ids)}"
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

    for p in patients:
        birth_date_str = p.get("birthDate")
        if birth_date_str:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            today = datetime.utcnow()
            delta_days = (today - birth_date).days

            if delta_days >= 365:
                p["age"] = f"{delta_days // 365} years"
            else:
                p["age"] = f"{delta_days} days"
        else:
            p["age"] = None

    return render(request, "patient-list.html", {
        "patients": patients,
        "page": page,
        "count": count,
        "has_next": len(MotherChild.objects.all()) > offset + count,
        "has_prev": page > 1
    })

    # return render(request, "patient-list.html", {"patient": patient_data})
    # return render(request, "fhir_patient.html", {"patients": patients})

def fhir_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("Authorization failed, no code received")

    iss = request.session.get("iss")
    code_verifier = request.session.get("code_verifier")

    config_url = iss.rstrip('/') + "/.well-known/smart-configuration"
    r = requests.get(config_url)
    smart_config = r.json()
    token_endpoint = smart_config.get("token_endpoint")

    token_response = requests.post(
        token_endpoint,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.FHIR_REDIRECT_URI,
            "client_id": settings.FHIR_CLIENT_ID,
            "code_verifier": code_verifier,
        },
        headers={"Accept": "application/json"},
    )

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return HttpResponse("Failed to obtain access token")
    request.session["fhir_token"] = token_data

    bundle_file_path = finders.find("data.json")
    if not bundle_file_path:
        return HttpResponse("data.json not found in static files")

    with open(bundle_file_path, "r", encoding="utf-8") as f:
        bundle_data = json.load(f)

    bundle_data["type"] = "transaction"
    for entry in bundle_data.get("entry", []):
        resource = entry.get("resource")
        if not resource or "resourceType" not in resource or "id" not in resource:
            continue

        if resource.get("name"):
            name_obj = resource["name"][0]
            if "text" in name_obj and ("given" not in name_obj or "family" not in name_obj):
                parts = name_obj["text"].split()
                name_obj["given"] = parts[:-1] if len(parts) > 1 else parts
                name_obj["family"] = parts[-1] if len(parts) > 1 else parts[0]

        resource_type = resource["resourceType"]
        resource_id = resource["id"]
        entry["request"] = {
            "method": "PUT",
            "url": f"{resource_type}/{resource_id}"
        }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/fhir+json"
    }

    fhir_base_url = iss.rstrip('/')

    r_post = requests.post(fhir_base_url, headers=headers, json=bundle_data)
    if r_post.status_code not in [200, 201]:
        return HttpResponse(f"Failed to upload Bundle: {r_post.status_code}, {r_post.text}")

    # count = 0
    # for entry in bundle_data.get("entry", []):
    #     resource = entry.get("resource")
    #     if not resource:
    #         continue
    #
    #     if resource.get("resourceType") == "RelatedPerson":
    #         mother_ref = resource["patient"]["reference"]
    #         mother_id = mother_ref.split("/")[1]
    #
    #         if resource.get("name"):
    #             name_obj = resource["name"][0]
    #             if "text" in name_obj:
    #                 mother_name = name_obj["text"]
    #                 child_name = name_obj["text"]
    #             else:
    #                 given = name_obj.get("given", [])
    #                 family = name_obj.get("family", "")
    #                 full_name = " ".join(given + [family]).strip()
    #                 if full_name:
    #                     mother_name = full_name
    #                     child_name = full_name
    #                 else:
    #                     mother_name = "(No name)"
    #                     child_name = "(No name)"
    #         else:
    #             mother_name = "(No name)"
    #             child_name = "(No name)"
    #
    #         child_id = resource.get("id", f"child-{mother_id}")
    #
    #         obj, created = MotherChild.objects.get_or_create(
    #             mother_id=mother_id,
    #             child_id=child_id,
    #             defaults={
    #                 "mother_name": mother_name,
    #                 "child_name": child_name,
    #             }
    #         )
    #         if not created:
    #             obj.mother_name = mother_name
    #             obj.child_name = child_name
    #             obj.save()
    #
    #         count += 1
    # print(f"Imported {count} mother-child records into database.")

    # return redirect("/login/")
    return redirect("/patient_list/")


def launch(request):
    iss = request.GET.get("iss")
    launch = request.GET.get("launch")

    if not iss:
        return HttpResponse("Missing 'iss' parameter")

    request.session["iss"] = iss
    request.session["launch"] = launch

    config_url = iss.rstrip('/') + "/.well-known/smart-configuration"
    r = requests.get(config_url)
    if r.status_code != 200:
        return HttpResponse("Cannot get SMART configuration")

    smart_config = r.json()
    auth_endpoint = smart_config.get("authorization_endpoint")
    if not auth_endpoint:
        return HttpResponse("No authorization_endpoint found in SMART configuration")

    auth_url = f"{auth_endpoint}?response_type=code&client_id={settings.FHIR_CLIENT_ID}" \
               f"&redirect_uri={settings.FHIR_REDIRECT_URI}&scope={settings.FHIR_SCOPE}" \
               f"&aud={iss}&launch={launch}"

    return redirect(auth_url)


def login_view(request):
    if request.method == "GET":
        return render(request, "login.html")

    if request.method == 'POST':
        data = json.loads(request.body)
        form = LoginForm(data)
        if not form.is_valid():
            errors = {field: err[0] for field, err in form.errors.items()}
            return JsonResponse({'status': 'fail', 'errors': errors})

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
        else:
            return JsonResponse({'status': 'fail', 'errors': {'general': 'Username or password incorrect'}})

        return JsonResponse({'status': 'success', 'redirect': '/patient_list/'})




def search_patients(request):
    token_data = request.session.get("fhir_token")
    if not token_data:
        return HttpResponse("No access token found")

    access_token = token_data.get("access_token")
    if not access_token:
        return HttpResponse("No access token found")

    iss = request.session.get("iss")
    fhir_url = request.GET.get("fhir_url")
    if not fhir_url:
        fhir_url = token_data.get("patient") or f"{iss.rstrip('/')}/Patient"

    if "?" in fhir_url:
        fhir_url += "&_count=10"
    else:
        fhir_url += "?_count=10"

    query = request.GET.get("q", "")
    if query:
        fhir_url += f"&name={query}"
        # fhir_url += f"&_id={query}"

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(fhir_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return JsonResponse({'patients': [], 'error': str(e)})

    patients = []
    for entry in data.get('entry', []):
        patient = entry['resource']
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
        birth = datetime.strptime(birth_date, '%Y-%m-%d').date()
        today = date.today()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return None