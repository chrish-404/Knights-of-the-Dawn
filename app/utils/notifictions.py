# author 风逝

def global_variable(request):
    if request.user.is_authenticated:
        unread_list = request.user.notifications.unread()
    return locals()
