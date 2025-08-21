# urls.py - Add these URLs to your existing urls.py file

from django.urls import path
from . import views

# Add these URL patterns to your existing urlpatterns
urlpatterns = [
    # ... your existing URLs ...
    
    # Daily Logging URLs (Simple Interface)
    path('member_logon/',views.member_food_dashboard_log,name="member_food_dashboard_log"),
    path('daily-log/', views.member_selection_for_logging, name='member_selection_for_logging'),
    path("member_dashboard/<int:member_id>",views.member_dashboard,name="member_dashboard"),
    path('daily-log/<int:member_id>/', views.daily_log_entry, name='daily_log_entry'),
    path('member/<int:member_id>/add-meal/', views.add_meal_entry, name='add_meal_entry'),
    path('member/<int:member_id>/log/<str:date_str>/', views.view_daily_log, name='view_daily_log'),
    path('member/<int:member_id>/history/', views.member_history, name='member_history'),
    path('member/<int:member_id>/meal/<int:meal_id>/delete/', views.delete_meal_entry, name='delete_meal_entry'),
    path('member/logout/', views.member_logout, name='member_logout'),
    
    # # Admin URLs


     # Admin Monitoring URLs
    path('admin/monitoring/dashboard/', views.admin_monitoring_dashboard, name='admin_monitoring_dashboard'),
    path('admin/logs/review/', views.admin_daily_logs_review, name='admin_daily_logs_review'),
    path('admin/members/', views.admin_member_list, name='admin_member_list'),
    path('admin/member/<int:member_id>/logs/', views.member_detail_logs, name='member_detail_logs'),
    path('admin/meal/comment/', views.add_meal_comment, name='add_meal_comment'),
]

    
    
