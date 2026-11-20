from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'), path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'), path('register/', views.register, name='register'), path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/pending/', views.pending_accounts, name='pending_accounts'), path('accounts/<int:user_id>/approve/', views.approve_account, name='approve_account'),
    path('students/', views.students, name='students'), path('students/add/', views.student_add, name='student_add'),
    path('examinations/', views.examinations, name='examinations'), path('examinations/add/', views.examination_add, name='examination_add'),
    path('biometrics/enroll/', views.enrollment, name='enrollment'), path('biometrics/verify/', views.verification, name='verification'),
    path('attendance/', views.attendance, name='attendance'), path('reports/', views.reports, name='reports'),
]
