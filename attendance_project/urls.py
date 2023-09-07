"""
URL configuration for attendance_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include , re_path
from attendance_app import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', auth_views.LoginView.as_view(), name='login'),
    path('admin/', admin.site.urls),
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('admin_panel/', views.admin_panel, name='admin_panel'),
    path('employee_panel/', views.employee_panel, name='employee_panel'),
    path('api/punch_in/', views.punch_in, name='punch_in'),
    path('api/punch_out/', views.punch_out, name='punch_out'),
    path('', RedirectView.as_view(url='/login/', permanent=True), name='index'),
    path('api/get_weekly_data/', views.get_weekly_data, name='get_weekly_data'),
    path('api/register_box/', views.register_box, name='register_box'),
    path('remote_punch_clock/', views.remote_punch_clock, name='remote_punch_clock'),
]
