from django import forms
from .models import Mesa, Prato, Combo, Comanda, ItemComanda


class PeriodoForm(forms.Form):
    inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    fim = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ["numero", "capacidade", "status"]
        widgets = {
            "numero": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ex: 10"}),
            "capacidade": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ex: 4"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

class ComandaForm(forms.ModelForm):
    class Meta:
        model = Comanda
        fields = ["mesa", "cliente_nome", "observacoes"]
        widgets = {
            "mesa": forms.Select(attrs={"class": "form-select"}),
            "cliente_nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome do cliente (opcional)"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Observações gerais"}),
        }

    def __init__(self, *args, organizacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["mesa"].queryset = Mesa.objects.filter(organizacao=organizacao, status="livre")

class ItemComandaForm(forms.ModelForm):
    tipo_item = forms.ChoiceField(
        choices=[("prato", "Prato Individual"), ("combo", "Combo Promocional")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial="prato",
        label="Tipo de Lançamento"
    )

    class Meta:
        model = ItemComanda
        fields = ["prato", "combo", "quantidade", "observacao"]
        widgets = {
            "prato": forms.Select(attrs={"class": "form-select"}),
            "combo": forms.Select(attrs={"class": "form-select"}),
            "quantidade": forms.NumberInput(attrs={"class": "form-control", "min": 1, "value": 1}),
            "observacao": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: sem cebola, gelo e limão"}),
        }

    def __init__(self, *args, organizacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prato"].queryset = Prato.objects.filter(organizacao=organizacao, disponivel=True)
        self.fields["combo"].queryset = Combo.objects.filter(organizacao=organizacao, disponivel=True)
        self.fields["prato"].required = False
        self.fields["combo"].required = False

    def clean(self):
        cleaned_data = super().clean()
        prato = cleaned_data.get("prato")
        combo = cleaned_data.get("combo")
        tipo = cleaned_data.get("tipo_item")

        if tipo == "prato" and not prato:
            raise forms.ValidationError("Por favor, selecione um prato do cardápio.")
        if tipo == "combo" and not combo:
            raise forms.ValidationError("Por favor, selecione um combo promocional.")

        return cleaned_data

class PratoForm(forms.ModelForm):
    class Meta:
        model = Prato
        fields = ["nome", "categoria", "preco", "descricao", "disponivel"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "preco": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "disponivel": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_preco(self):
        preco = self.cleaned_data["preco"]
        if preco <= 0:
            raise forms.ValidationError("O preço do prato deve ser maior que zero.")
        return preco

class ComboForm(forms.ModelForm):
    class Meta:
        model = Combo
        fields = ["nome", "preco", "descricao", "pratos", "disponivel"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "preco": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "pratos": forms.SelectMultiple(attrs={"class": "form-select", "size": 5}),
            "disponivel": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, organizacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pratos"].queryset = Prato.objects.filter(organizacao=organizacao)

    def clean_preco(self):
        preco = self.cleaned_data["preco"]
        if preco <= 0:
            raise forms.ValidationError("O preço do combo deve ser maior que zero.")
        return preco
