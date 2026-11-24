from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'), path('administrator-setup/<str:token>/', views.administrator_setup, name='administrator_setup'), path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'), path('register/', views.register, name='register'), path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/pending/', views.pending_accounts, name='pending_accounts'), path('accounts/<int:user_id>/approve/', views.approve_account, name='approve_account'),
    path('students/', views.students, name='students'), path('students/add/', views.student_add, name='student_add'),
    path('examinations/', views.examinations, name='examinations'), path('examinations/add/', views.examination_add, name='examination_add'),
    path('verification/', views.verification, name='verification'), path('reviews/', views.review_queue, name='review_queue'),
    path('attendance/', views.attendance, name='attendance'), path('reports/', views.reports, name='reports'),
    path('incidents/', views.incident_queue, name='incident_queue'), path('incidents/create/', views.incident_create, name='incident_create'), path('incidents/<int:case_id>/', views.incident_detail, name='incident_detail'), path('board/cases/', views.board_case_queue, name='board_case_queue'),
]
