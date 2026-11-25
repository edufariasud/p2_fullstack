from decimal import Decimal
from django.db.models import Count
from django.db.models.functions import TruncMonth
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .api_permissions import PodeGerenciarRecurso
from .models import Combo, Comanda, ItemComanda, Mesa, Prato
from .serializers import ComboSerializer, ComandaSerializer, ItemComandaSerializer, MesaSerializer, PratoSerializer


class OrganizacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [PodeGerenciarRecurso]

    def get_queryset(self):
        return self.queryset.filter(organizacao=self.request.user.perfil.organizacao)

    def perform_create(self, serializer):
        serializer.save(organizacao=self.request.user.perfil.organizacao)


class MesaViewSet(OrganizacaoViewSet):
    queryset = Mesa.objects.all()
    serializer_class = MesaSerializer


class PratoViewSet(OrganizacaoViewSet):
    queryset = Prato.objects.all()
    serializer_class = PratoSerializer


class ComboViewSet(OrganizacaoViewSet):
    queryset = Combo.objects.prefetch_related("pratos")
    serializer_class = ComboSerializer


class ComandaViewSet(OrganizacaoViewSet):
    queryset = Comanda.objects.select_related("mesa").prefetch_related("itens")
    serializer_class = ComandaSerializer

    def perform_create(self, serializer):
        comanda = serializer.save(organizacao=self.request.user.perfil.organizacao)
        comanda.mesa.status = "ocupada"
        comanda.mesa.save(update_fields=["status"])


class ItemComandaViewSet(OrganizacaoViewSet):
    queryset = ItemComanda.objects.select_related("comanda", "prato", "combo")
    serializer_class = ItemComandaSerializer

    def perform_create(self, serializer):
        item = serializer.save(organizacao=self.request.user.perfil.organizacao)
        if item.prato_id:
            item.preco_unitario = item.prato.preco
        else:
            item.preco_unitario = item.combo.preco
        item.save(update_fields=["preco_unitario"])


class DashboardApi(APIView):
    def get(self, request):
        org = request.user.perfil.organizacao
        comandas = Comanda.objects.filter(organizacao=org)
        itens = ItemComanda.objects.filter(comanda__in=comandas).select_related("prato", "combo")
        faturamento = sum((item.subtotal for item in itens), Decimal("0.00"))
        ranking = itens.values("prato__nome", "combo__nome").annotate(total=Count("id")).order_by("-total")[:5]
        por_mes = comandas.annotate(mes=TruncMonth("data_abertura")).values("mes").annotate(total=Count("id")).order_by("mes")
        return Response({
            "total_comandas": comandas.count(),
            "comandas_abertas": comandas.filter(status="aberta").count(),
            "faturamento": faturamento,
            "ranking": list(ranking),
            "por_mes": list(por_mes),
        })
