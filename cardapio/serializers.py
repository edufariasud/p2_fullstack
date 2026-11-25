from rest_framework import serializers
from .models import Combo, Comanda, ItemComanda, Mesa, Prato


class OrganizacaoSerializerMixin:
    def validate(self, attrs):
        request = self.context["request"]
        org = request.user.perfil.organizacao
        for campo in ("mesa", "prato", "combo", "comanda"):
            obj = attrs.get(campo)
            if obj is not None and obj.organizacao_id != org.id:
                raise serializers.ValidationError({campo: "Este registro não pertence ao seu restaurante."})
        return attrs


class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = ["id", "numero", "capacidade", "status"]


class PratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prato
        fields = ["id", "nome", "categoria", "preco", "descricao", "disponivel"]

    def validate_preco(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value


class ComboSerializer(OrganizacaoSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Combo
        fields = ["id", "nome", "descricao", "preco", "pratos", "disponivel"]

    def validate_preco(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value


class ComandaSerializer(OrganizacaoSerializerMixin, serializers.ModelSerializer):
    total_consumo = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Comanda
        fields = ["id", "mesa", "cliente_nome", "status", "data_abertura", "data_fechamento", "observacoes", "total_consumo"]
        read_only_fields = ["data_abertura", "data_fechamento"]


class ItemComandaSerializer(OrganizacaoSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ItemComanda
        fields = ["id", "comanda", "prato", "combo", "quantidade", "preco_unitario", "observacao"]
        read_only_fields = ["preco_unitario"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        prato, combo = attrs.get("prato"), attrs.get("combo")
        if prato and combo:
            raise serializers.ValidationError("Escolha prato ou combo, não os dois.")
        if not prato and not combo and not self.instance:
            raise serializers.ValidationError("Escolha um prato ou um combo.")
        return attrs
