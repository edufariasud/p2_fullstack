from django.contrib.auth.models import User
from django.db import models


class Organizacao(models.Model):
    nome = models.CharField(max_length=120)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Restaurante"
        verbose_name_plural = "Restaurantes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Perfil(models.Model):
    PAPEIS = [
        ("admin", "Administrador"),
        ("operador", "Operador"),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    organizacao = models.ForeignKey(Organizacao, on_delete=models.PROTECT, related_name="perfis")
    papel = models.CharField(max_length=20, choices=PAPEIS, default="operador")

    def __str__(self):
        return f"{self.usuario.username} - {self.get_papel_display()}"
