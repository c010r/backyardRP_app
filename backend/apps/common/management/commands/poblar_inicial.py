"""
Comando de management para poblar datos iniciales del sistema.

Uso:
    python manage.py poblar_inicial

Crea (si no existen):
  - Usuario admin con contraseña 'admin1234' (cambiar en producción)
  - Empresa con datos de Backyard Resto Pub
  - Horarios del negocio: jue/vie/sáb/dom
  - Categorías base del menú
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.configuracion.models import DiaSemana, Empresa, HorarioNegocio

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Pobla los datos iniciales del sistema Backyard Resto Pub."

    def handle(self, *args, **options):
        self._crear_admin()
        self._crear_empresa()
        self._crear_horarios()
        self._crear_categorias()
        self.stdout.write(
            self.style.SUCCESS("\n✓ Datos iniciales cargados correctamente.")
        )

    def _crear_admin(self):
        if not Usuario.objects.filter(username="admin").exists():
            from apps.usuarios.models import Rol

            admin = Usuario.objects.create_superuser(
                username="admin",
                email="admin@backyardrestopub.com",
                password="admin1234",
                first_name="Administrador",
                last_name="Sistema",
                rol=Rol.ADMINISTRADOR,
            )
            admin.primer_ingreso = True
            admin.save(update_fields=["primer_ingreso"])
            self.stdout.write(
                "  • Usuario admin creado (contraseña: admin1234 — cambiar en producción)"
            )
        else:
            self.stdout.write("  • Usuario admin ya existe, omitido.")

    def _crear_empresa(self):
        if not Empresa.objects.exists():
            Empresa.objects.create(
                nombre="Backyard Resto Pub",
                razon_social="Backyard Resto Pub S.R.L.",
                rut="210000000010",
                direccion="Dirección del local",
                ciudad="",
                telefono="",
                email="info@backyardrestopub.com",
            )
            self.stdout.write("  • Empresa creada.")
        else:
            self.stdout.write("  • Empresa ya existe, omitida.")

    def _crear_horarios(self):
        horarios = [
            # (dia, apertura, cierre, cierre_siguiente_dia)
            (DiaSemana.JUEVES, datetime.time(20, 0), datetime.time(0, 0), False),
            (DiaSemana.VIERNES, datetime.time(21, 0), datetime.time(2, 0), True),
            (DiaSemana.SABADO, datetime.time(21, 0), datetime.time(4, 0), True),
            (DiaSemana.DOMINGO, datetime.time(20, 0), datetime.time(0, 0), False),
        ]
        creados = 0
        for dia, apertura, cierre, siguiente_dia in horarios:
            _, created = HorarioNegocio.objects.get_or_create(
                dia=dia,
                defaults={
                    "apertura": apertura,
                    "cierre": cierre,
                    "cierre_siguiente_dia": siguiente_dia,
                    "activo": True,
                },
            )
            if created:
                creados += 1
        if creados:
            self.stdout.write(f"  • {creados} horario(s) del negocio creados.")
        else:
            self.stdout.write("  • Horarios ya existen, omitidos.")

    def _crear_categorias(self):
        from apps.catalogo.models import Categoria

        categorias = [
            ("Cervezas", "Cervezas artesanales e industriales", 1),
            ("Tragos", "Cócteles y tragos de la carta", 2),
            ("Vinos y Espumantes", "Selección de vinos y champagnes", 3),
            ("Bebidas sin alcohol", "Aguas, gaseosas y jugos", 4),
            ("Picadas y Entradas", "Tablas y entradas para compartir", 5),
            ("Hamburguesas", "Hamburguesas artesanales", 6),
            ("Platos principales", "Cocina principal del menú", 7),
            ("Postres", "Postres de la carta", 8),
        ]
        creados = 0
        for nombre, desc, orden in categorias:
            _, created = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": desc, "orden": orden},
            )
            if created:
                creados += 1
        if creados:
            self.stdout.write(f"  • {creados} categoría(s) del menú creadas.")
        else:
            self.stdout.write("  • Categorías ya existen, omitidas.")
