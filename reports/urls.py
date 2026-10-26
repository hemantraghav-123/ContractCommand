
from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.executive_dashboard, name="dashboard"),
    path("export/contracts.csv", views.export_contracts_csv, name="export_contracts"),
    path("export/invoices.csv", views.export_invoices_csv, name="export_invoices"),
]
