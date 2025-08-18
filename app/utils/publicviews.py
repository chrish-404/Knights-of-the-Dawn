# author 风逝
from app.forms import Regusername
from app.models import Payment


def global_variable(request):
    if request.user.is_authenticated:
        unread_list = request.user.notifications.unread()
        if request.user.type==1:
            all = Payment.objects.all().count()
            if all!=0:
                pay = Payment.objects.filter(statue=1).count()
                per = pay / all * 100
                if per==100:
                    task=None
                else:
                    task=1
    return locals()
