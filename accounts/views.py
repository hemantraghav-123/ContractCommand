
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    role_names = list(
        request.user.groups.values_list("name", flat=True)
    )

    if request.user.is_superuser:
        role = "Administrator"
    elif role_names:
        role = ", ".join(role_names)
    else:
        role = "No role assigned"

    return render(
        request,
        "accounts/dashboard.html",
        {
            "role": role,
            "username": request.user.username,
        },
    )

