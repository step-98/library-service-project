from django.urls import path, include
from rest_framework import routers
from payments.views import PaymentViewSet, PaymentCancelView, PaymentSuccessView

app_name = "payments"

router = routers.DefaultRouter()
router.register("", PaymentViewSet)

urlpatterns = [
    path("cancel/", PaymentCancelView.as_view(), name="cancel"),
    path("success/", PaymentSuccessView.as_view(), name="success"),
    path("", include(router.urls)),

]