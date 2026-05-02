from django.urls import path
from . import views

app_name = 'pemilwa'

urlpatterns = [ 
    path('', views.login_view, name='login'),
    path('voting/', views.voting_page, name='voting_page'),
    path('submit/', views.submit_vote, name='submit_vote'),
    path('thanks/', views.thanks_view, name='thanks'),
    path('voter-logout/', views.voter_logout, name='voter_logout'),
    # Admin routes (tanpa login terpisah)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
]
