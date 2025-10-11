from django.urls import path
from . import views

app_name = "onlinePrescription"

urlpatterns = [
    # Customer
    path("", views.PrescriptionListView.as_view(), name="list"),
    path("upload/", views.PrescriptionCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PrescriptionDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", getattr(views, "PrescriptionUpdateView", views.PrescriptionCreateView).as_view(), name="edit"),
    path("<int:pk>/delete/", views.PrescriptionDeleteView.as_view(), name="delete"),

    # Pharmacist
    path("pharmacist/", views.PharmacistPrescriptionListView.as_view(), name="pharmacist_list"),
    path("pharmacist/<int:pk>/", views.PharmacistPrescriptionDetailView.as_view(), name="pharmacist_detail"),
    path("pharmacist/<int:pk>/review/", views.PharmacistPrescriptionReviewView.as_view(), name="pharmacist_review"),
]