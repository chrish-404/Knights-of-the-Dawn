'''
@Project ：comp3820 
@Author  ：风&逝
@Date    ：2025/8/23 19:01 
'''
from django import forms
from django.contrib.auth import authenticate

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        error_messages={'required': 'user name is required'}
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        error_messages={'required': 'password is required'}
    )