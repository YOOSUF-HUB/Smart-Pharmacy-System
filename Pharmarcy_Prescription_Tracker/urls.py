from django.contrib import admin
from django.urls import path, include  # import include

urlpatterns = [
    path('admin/', admin.site.urls),


    # Set the root URL to the medicine card view
    path('', include('Medicine_inventory.urls')),  # now root goes to medicine app
    path('prescriptions/', include('prescriptions.prescription_urls')),
]