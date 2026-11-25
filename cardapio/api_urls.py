from rest_framework.routers import DefaultRouter
from .api_views import ComboViewSet, ComandaViewSet, ItemComandaViewSet, MesaViewSet, PratoViewSet
from .api_views import DashboardApi
from django.urls import path

router = DefaultRouter()
router.register("mesas", MesaViewSet, basename="mesa")
router.register("pratos", PratoViewSet, basename="prato")
router.register("combos", ComboViewSet, basename="combo")
router.register("comandas", ComandaViewSet, basename="comanda")
router.register("itens", ItemComandaViewSet, basename="item")

urlpatterns = [path("dashboard/", DashboardApi.as_view(), name="api-dashboard")] + router.urls
