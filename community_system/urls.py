from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    # You must also include Django's built-in auth URLs for login/logout to work correctly.
    # These will use the templates we created.
    path('accounts/', include('django.contrib.auth.urls')),
]