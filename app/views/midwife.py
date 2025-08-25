'''
@Project ：comp3820 
@Author  ：风&逝
@Date    ：2025/8/25 15:53 
'''
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render

from app.models import ShiftSchedule


def index(request):
    return render(request,"midwife_index.html")


def search_date(request):
    date_str = request.GET.get('date')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    user = request.user
    shifts = ShiftSchedule.objects.filter(staff=user.id, date=date_obj)

    if not shifts.exists():
        return JsonResponse({'data': []})

    data_list = [
        {
            'date': s.date.strftime('%Y-%m-%d'),
            'shift': s.get_shift_display()
        } for s in shifts
    ]

    return JsonResponse({'data': data_list})