'''
@Project ：comp3820 
@Author  ：风&逝
@Date    ：2025/8/24 21:47 
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


def fhir_callback(request):
    code = request.GET.get("code")
    iss = settings.FHIR_ISS_URL
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
    request.session["fhir_token"] = token_data

    bundle_file_path = finders.find("data.json")

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
    #         child_id = resource.get("id", f"child-{mother_id}")
    #
    #         obj, created = MotherChild.objects.get_or_create(
    #             mother_id=mother_id,
    #             child_id=child_id
    #         )
    #         count += 1
    #
    # print(f"Imported {count} mother-child records into database.")

    return redirect("/login/")
    # return redirect("/patient_list/")


def launch(request):
    iss = request.GET.get("iss")
    launch_id = request.GET.get("launch")

    request.session['iss'] = settings.FHIR_ISS_URL
    request.session["launch"] = launch_id
    config_url = iss.rstrip('/') + "/.well-known/smart-configuration"
    r = requests.get(config_url)
    smart_config = r.json()
    auth_endpoint = smart_config.get("authorization_endpoint")

    auth_url = f"{auth_endpoint}?response_type=code&client_id={settings.FHIR_CLIENT_ID}" \
               f"&redirect_uri={settings.FHIR_REDIRECT_URI}&scope={settings.FHIR_SCOPE}" \
               f"&aud={iss}&launch={launch_id}"

    return redirect(auth_url)


def login_view(request):
    if request.method == "GET":
        return render(request, "login.html")

    if request.method == 'POST':
        # data={
        #     'username':'404',
        #     'password':'123456',
        # }
        # User.objects.create_user(**data)
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
