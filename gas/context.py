from django.conf import settings
def agency(request):
    return {"agency": settings.AGENCY}
