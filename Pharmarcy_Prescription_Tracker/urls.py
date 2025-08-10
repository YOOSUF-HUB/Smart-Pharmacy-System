from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),


    # Set the root URL to the medicine card view
    path('', include('Medicine_inventory.urls')),  # now root goes to medicine app
    path('prescriptions/', include('prescriptions.prescription_urls')),
    path('non-medical/', include('Non_Medicine_inventory.urls', namespace='non_medicine')),
    path('payments/' , include('payments.payments_urls'))
]

# For serving media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)