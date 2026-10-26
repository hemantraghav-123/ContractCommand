
from django.urls import path

from . import views

app_name = "evaluations"

urlpatterns = [
    path("", views.evaluation_list, name="list"),
    path("create/", views.evaluation_create, name="create"),
    path(
        "compare/<int:plan_id>/",
        views.evaluation_compare,
        name="compare",
    ),
]
