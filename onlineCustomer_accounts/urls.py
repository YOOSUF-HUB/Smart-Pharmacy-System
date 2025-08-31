from django.urls import path
from . import views

app_name = 'onlineCustomer_accounts'

urlpatterns = [
    path('create-account/', views.create_account, name='create_account'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
]