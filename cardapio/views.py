import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import papel_obrigatorio
from core.utils import eh_admin, org_atual
from .forms import ComboForm, ComandaForm, ItemComandaForm, PratoForm
from .models import Combo, Comanda, ItemComanda, Mesa, Prato


@login_required
def index(request):
    org = org_atual(request)
    mesas = Mesa.objects.filter(organizacao=org).prefetch_related("comandas__itens")
    comandas_abertas = Comanda.objects.filter(organizacao=org, status="aberta").select_related("mesa")
    return render(request, "cardapio/index.html", {
        "mesas": mesas, "comandas_abertas": comandas_abertas,
        "total_abertas": comandas_abertas.count(),
        "mesas_livres": mesas.filter(status="livre").count(),
        "mesas_ocupadas": mesas.filter(status="ocupada").count(),
    })


@login_required
def abrir_comanda(request, mesa_id=None):
    org = org_atual(request)
    mesa_pre = get_object_or_404(Mesa, id=mesa_id, organizacao=org) if mesa_id else None
    form = ComandaForm(request.POST or None, initial={"mesa": mesa_pre} if mesa_pre else None, organizacao=org)
    if request.method == "POST" and form.is_valid():
        comanda = form.save(commit=False)
        comanda.organizacao = org
        comanda.status = "aberta"
        comanda.save()
        comanda.mesa.status = "ocupada"
        comanda.mesa.save()
        messages.success(request, f"Comanda #{comanda.id} aberta para a Mesa {comanda.mesa.numero}.")
        return redirect("comanda_detalhes", comanda_id=comanda.id)
    return render(request, "cardapio/abrir_comanda.html", {"form": form, "mesa_pre": mesa_pre})


@login_required
def comanda_detalhes(request, comanda_id):
    org = org_atual(request)
    comanda = get_object_or_404(Comanda, id=comanda_id, organizacao=org)
    itens = comanda.itens.select_related("prato", "combo").all()
    form_item = ItemComandaForm(request.POST or None, organizacao=org)
    if request.method == "POST" and comanda.status == "aberta" and form_item.is_valid():
        item = form_item.save(commit=False)
        item.comanda, item.organizacao = comanda, org
        if form_item.cleaned_data["tipo_item"] == "prato":
            item.combo, item.preco_unitario = None, item.prato.preco
        else:
            item.prato, item.preco_unitario = None, item.combo.preco
        item.save()
        messages.success(request, f"Item adicionado à comanda #{comanda.id}.")
        return redirect("comanda_detalhes", comanda_id=comanda.id)
    return render(request, "cardapio/comanda_detalhe.html", {
        "comanda": comanda, "itens": itens, "form_item": form_item, "total_consumo": comanda.total_consumo,
    })


@login_required
def remover_item(request, item_id):
    item = get_object_or_404(ItemComanda, id=item_id, organizacao=org_atual(request))
    comanda_id = item.comanda_id
    if item.comanda.status == "aberta":
        item.delete()
        messages.info(request, "Item removido da comanda.")
    return redirect("comanda_detalhes", comanda_id=comanda_id)


@login_required
def fechar_conta(request, comanda_id):
    comanda = get_object_or_404(Comanda, id=comanda_id, organizacao=org_atual(request))
    if request.method == "POST" and comanda.status == "aberta":
        comanda.fechar_conta()
        messages.success(request, f"Conta da Mesa {comanda.mesa.numero} fechada. Mesa liberada.")
        return redirect("comanda_detalhes", comanda_id=comanda.id)
    total = comanda.total_consumo
    return render(request, "cardapio/fechar_conta.html", {
        "comanda": comanda, "itens": comanda.itens.select_related("prato", "combo"), "total": total,
        "taxa_servico": total * Decimal("0.10"), "total_com_taxa": total * Decimal("1.10"),
    })


@login_required
def cardapio_lista(request):
    org = org_atual(request)
    pratos = Prato.objects.filter(organizacao=org, disponivel=True)
    return render(request, "cardapio/cardapio_lista.html", {
        "entradas": pratos.filter(categoria="entrada"), "principais": pratos.filter(categoria="principal"),
        "sobremesas": pratos.filter(categoria="sobremesa"), "bebidas": pratos.filter(categoria="bebida"),
        "combos": Combo.objects.filter(organizacao=org, disponivel=True).prefetch_related("pratos"),
    })


@papel_obrigatorio("admin")
def novo_prato(request):
    form = PratoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        prato = form.save(commit=False)
        prato.organizacao = org_atual(request)
        prato.save()
        messages.success(request, f"Prato {prato.nome} cadastrado.")
        return redirect("cardapio_lista")
    return render(request, "cardapio/form_generico.html", {"form": form, "titulo": "Cadastrar Novo Prato"})


@papel_obrigatorio("admin")
def novo_combo(request):
    org = org_atual(request)
    form = ComboForm(request.POST or None, organizacao=org)
    if request.method == "POST" and form.is_valid():
        combo = form.save(commit=False)
        combo.organizacao = org
        combo.save()
        form.save_m2m()
        messages.success(request, f"Combo {combo.nome} cadastrado.")
        return redirect("cardapio_lista")
    return render(request, "cardapio/form_generico.html", {"form": form, "titulo": "Cadastrar Novo Combo"})


def _base_dashboard(request):
    org = org_atual(request)
    qs = Comanda.objects.filter(organizacao=org)
    inicio, fim = request.GET.get("inicio"), request.GET.get("fim")
    if inicio:
        qs = qs.filter(data_abertura__date__gte=inicio)
    if fim:
        qs = qs.filter(data_abertura__date__lte=fim)
    return qs


@login_required
def dashboard(request):
    base = _base_dashboard(request)
    itens = ItemComanda.objects.filter(comanda__in=base)
    ranking = itens.values("prato__nome", "combo__nome").annotate(total=Count("id")).order_by("-total")[:5]
    por_mes = base.annotate(mes=TruncMonth("data_abertura")).values("mes").annotate(total=Count("id")).order_by("mes")
    distribuicao = base.values("status").annotate(total=Count("id")).order_by("status")
    faturamento = sum((item.subtotal for item in itens.select_related("prato", "combo")), Decimal("0.00"))
    return render(request, "cardapio/dashboard.html", {
        "total_comandas": base.count(), "abertas": base.filter(status="aberta").count(), "faturamento": faturamento,
        "ranking": ranking, "por_mes": list(por_mes), "distribuicao": distribuicao, "inicio": request.GET.get("inicio", ""),
        "fim": request.GET.get("fim", ""), "pode_exportar": eh_admin(request),
    })


@papel_obrigatorio("admin")
def exportar_comandas_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="relatorio_comandas.csv"'
    writer = csv.writer(response)
    writer.writerow(["Comanda", "Mesa", "Cliente", "Status", "Abertura", "Total"])
    for comanda in _base_dashboard(request).select_related("mesa"):
        writer.writerow([comanda.id, comanda.mesa.numero, comanda.cliente_nome, comanda.get_status_display(), comanda.data_abertura.strftime("%d/%m/%Y %H:%M"), f"{comanda.total_consumo:.2f}"])
    return response
