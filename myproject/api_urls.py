from django.urls import path
from django.http import JsonResponse

def ping(_request):
    return JsonResponse({"ping": "pong"})

urlpatterns = [
    path("ping/", ping),   # /api/ping/  (sonunda slash var!)
]
