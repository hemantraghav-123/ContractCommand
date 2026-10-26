
from django.urls import path

from . import views

app_name = "contracts"

urlpatterns = [
    path("", views.contract_list, name="list"),
    path("create/", views.contract_create, name="create"),
    path("<int:pk>/", views.contract_detail, name="detail"),
    path("<int:pk>/edit/", views.contract_update, name="update"),
    path("<int:pk>/archive/", views.contract_archive, name="archive"),
]
