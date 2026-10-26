
"""
URL configuration for the ContractCommand project.
"""


from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("contracts/", include("contracts.urls")),
    path("procurement/", include("procurement.urls")),
    path("vendors/", include("vendors.urls")),
    path("evaluations/", include("evaluations.urls")),
    path("invoices/", include("invoices.urls")),
    path("payments/", include("payments.urls")),
    path("", include("accounts.urls")),
]

