import hashlib
import secrets
from datetime import datetime

import requests
import base64

from django.contrib.auth import authenticate, login
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from app.forms import LoginForm
from app.models import User
from comp3820 import settings


# Create your views here.
def index(request):
    return render(request, 'index.html')


def patient_list(request):
    token_data = request.session.get("fhir_token")
    if not token_data:
        return redirect("fhir_login")

    access_token = token_data.get("access_token")
    if not access_token:
        return HttpResponse("No access token found")

    iss = request.session.get("iss")
    fhir_url = request.GET.get("fhir_url")
    if not fhir_url:
        fhir_url = token_data.get("patient") or f"{iss.rstrip('/')}/Patient"
        fhir_url = f"{fhir_url}?_count=10"

    response = requests.get(
        fhir_url,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    patient_data = response.json()
    entries = patient_data.get("entry", [])

    patients = []
    for e in entries:
        r = e.get("resource", {})
        patients.append({
            "id": r.get("id"),
            "name": " ".join(r.get("name", [{}])[0].get("given", []) + [r.get("name", [{}])[0].get("family", "")]),
            "gender": r.get("gender"),
            "birthDate": r.get("birthDate"),
            "phone": next((t.get("value") for t in r.get("telecom", []) if t.get("system") == "phone" and "value" in t), ""),
            "email": next((t.get("value") for t in r.get("telecom", []) if t.get("system") == "email" and "value" in t), "")
        })

    for p in patients:
        if p.get("birthDate"):
            birth_year = int(p["birthDate"][:4])
            today_year = datetime.utcnow().year
            p["age"] = today_year - birth_year
        else:
            p["age"] = None

    next_url = prev_url = None
    for link in patient_data.get("link", []):
        if link.get("relation") == "next":
            next_url = link.get("url")
        elif link.get("relation") == "previous":
            prev_url = link.get("url")

    return render(request, "patient-list.html", {
        "patients": patients,
        "next_url": next_url,
        "prev_url": prev_url
    })
    return render(request, "patient-list.html", {"patients": patients})
    # return render(request, "patient-list.html", {"patient": patient_data})
    # return render(request, "fhir_patient.html", {"patients": patients})


def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode('utf-8')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode('utf-8')
    return code_verifier, code_challenge


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
    request.session["fhir_token"] = token_data


    return redirect("/login")


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