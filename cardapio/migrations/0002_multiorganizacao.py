import django.db.models.deletion
from django.db import migrations, models


def associar_dados_existentes(apps, schema_editor):
    Organizacao = apps.get_model("core", "Organizacao")
    User = apps.get_model("auth", "User")
    Perfil = apps.get_model("core", "Perfil")
    org, _ = Organizacao.objects.get_or_create(nome="Restaurante Principal")
    for model_name in ("Mesa", "Prato", "Combo", "Comanda", "ItemComanda"):
        apps.get_model("cardapio", model_name).objects.filter(organizacao__isnull=True).update(organizacao=org)
    for user in User.objects.all():
        Perfil.objects.get_or_create(usuario=user, defaults={"organizacao": org, "papel": "admin" if user.is_superuser else "operador"})


class Migration(migrations.Migration):
    dependencies = [("cardapio", "0001_initial"), ("core", "0001_initial")]
    operations = [
        migrations.AddField(model_name="mesa", name="organizacao", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="mesas", to="core.organizacao")),
        migrations.AddField(model_name="prato", name="organizacao", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pratos", to="core.organizacao")),
        migrations.AddField(model_name="combo", name="organizacao", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="combos", to="core.organizacao")),
        migrations.AddField(model_name="comanda", name="organizacao", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="comandas", to="core.organizacao")),
        migrations.AddField(model_name="itemcomanda", name="organizacao", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="itens_comanda", to="core.organizacao")),
        migrations.RunPython(associar_dados_existentes, migrations.RunPython.noop),
        migrations.AlterField(model_name="mesa", name="organizacao", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mesas", to="core.organizacao")),
        migrations.AlterField(model_name="prato", name="organizacao", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pratos", to="core.organizacao")),
        migrations.AlterField(model_name="combo", name="organizacao", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="combos", to="core.organizacao")),
        migrations.AlterField(model_name="comanda", name="organizacao", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="comandas", to="core.organizacao")),
        migrations.AlterField(model_name="itemcomanda", name="organizacao", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="itens_comanda", to="core.organizacao")),
        migrations.AlterField(model_name="mesa", name="numero", field=models.PositiveIntegerField(verbose_name="Número da Mesa")),
        migrations.AddConstraint(model_name="mesa", constraint=models.UniqueConstraint(fields=("organizacao", "numero"), name="mesa_numero_por_organizacao")),
    ]
