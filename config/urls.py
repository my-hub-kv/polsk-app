from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "Polsk App-administration"
admin.site.site_title = "Polsk App-administration"
admin.site.index_title = "Nødadministration"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
]
