# core_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('volunteer/dashboard/', views.volunteer_dashboard_view, name='volunteer_dashboard'),

    path('request/<int:request_id>/assign/', views.assign_request_view, name='assign_request'),
    path('request/<int:request_id>/auto-assign/', views.auto_assign_request_view, name='auto_assign_request'),
    path('request/<int:request_id>/details/', views.request_detail_view, name='request_detail'),

    path('alerts/create/', views.create_alert_view, name='create_alert'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),

    path('update-location/', views.update_location, name='update_location'),
]
