# asha_project/urls.py
from django.contrib import admin
from django.urls import path, include
from core_app.views import landing_page_view  # root landing page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page_view, name='landing_page'),  # only "/" goes here
    path('', include('core_app.urls')),                # everything else from core_app
]
