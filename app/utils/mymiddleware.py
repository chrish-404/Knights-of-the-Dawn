# author 风逝
import sys

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.views.debug import technical_500_response



class mymiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = request.user
        if user.is_authenticated:
            return
        elif request.path not in ['/login/']:
            return redirect('/login/')
        # request_type = (request.path).split("/")[1]
        # if request.user.is_authenticated:
        #     if request.user.type == 2 and request_type not in ['user','public','media']:
        #         return redirect('/user/index/')
        #     elif request.user.type == 3 and request_type not in ['fix','public','media']:
        #         return redirect('/fix/index/')
        #     else:
        #         return
        # elif request.path not in ['/login/','/img/code/','/logout/'] and request_type not in ['face'] and not request.user.is_authenticated:
        #     print(request.path)
        #     # if request.path !='/register/':
        #     return redirect('/login/')
        # else:
        #     return
    def process_responsw(self,request,response):
        pass

    # 给管理员报错
    def process_exception(self,request,exception):
        ip=request.META.get('REMOTE_ADDR')
        if ip=='127.0.0.1':
            return technical_500_response(request,*sys.exc_info())
        return redirect('/index/')
