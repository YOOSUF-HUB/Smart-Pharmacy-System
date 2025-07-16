from django.contrib import admin
from django.urls import path, include  # import include
from crudApp import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Student app URLs
    path('view/', views.student_view, name='student_view'),
    path('create', views.create_student, name='student_create'),
    path('delete/<id>', views.delete_student),
    path('update/<id>', views.update_student),
    path('', views.home, name='home'),

    # Medicine_inventory app URLs
    path('medicine/', include('Medicine_inventory.urls')),  # include medicine app URLs here
]