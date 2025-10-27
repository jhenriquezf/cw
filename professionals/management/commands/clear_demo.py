# professionals/management/commands/clear_demo.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.apps import apps
from django.db import transaction

User = get_user_model()

def model_or_none(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None

def model_has_field(model, name: str) -> bool:
    if not model:
        return False
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False

def delete_fieldfile_safely(obj, field_name: str):
    try:
        f = getattr(obj, field_name, None)
        if f and hasattr(f, "name") and f.name:
            # Esto borra el archivo del storage y NO guarda el modelo
            f.delete(save=False)
    except Exception:
        # no interrumpir el proceso por problemas de IO/storage
        pass

class Command(BaseCommand):
    help = "Elimina los datos de prueba creados por seed_demo (usuarios *@demo.local y relacionados)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra lo que se borraría, sin borrar nada."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options.get("dry_run", False)

        Professional = model_or_none("professionals", "Professional")
        Certification = model_or_none("professionals", "Certification")
        Service = model_or_none("services", "Service")

        # 1) Identifica usuarios de demo
        users_qs = User.objects.filter(email__iendswith="@demo.local")
        users_count = users_qs.count()

        # 2) Relacionados
        pros_qs = Professional.objects.filter(user__in=users_qs) if Professional else None
        pros_count = pros_qs.count() if pros_qs is not None else 0

        certs_qs = Certification.objects.filter(professional__in=pros_qs) if (Certification and pros_qs is not None) else None
        certs_count = certs_qs.count() if certs_qs is not None else 0

        services_qs = Service.objects.filter(professional__in=pros_qs) if (Service and pros_qs is not None) else None
        services_count = services_qs.count() if services_qs is not None else 0

        self.stdout.write("Resumen (modo {}):".format("DRY-RUN" if dry else "EJECUCIÓN"))
        self.stdout.write(f"  Usuarios demo          : {users_count}")
        self.stdout.write(f"  Professionals asociados: {pros_count}")
        self.stdout.write(f"  Services asociados     : {services_count}")
        self.stdout.write(f"  Certifications asociadas: {certs_count}")

        if dry:
            self.stdout.write(self.style.WARNING("\n--dry-run activado. No se borró nada."))
            return

        # 3) Borrar archivos adjuntos primero (para no dejar huérfanos en el storage)
        if certs_qs is not None and model_has_field(Certification, "document"):
            for c in certs_qs.iterator():
                delete_fieldfile_safely(c, "document")

        if pros_qs is not None and model_has_field(Professional, "photo"):
            for p in pros_qs.iterator():
                delete_fieldfile_safely(p, "photo")

        # 4) Borrar registros en orden (hijos -> padres)
        if services_qs is not None:
            deleted_services = services_qs.delete()[0]
            self.stdout.write(f"Eliminados Services: {deleted_services}")

        if certs_qs is not None:
            deleted_certs = certs_qs.delete()[0]
            self.stdout.write(f"Eliminadas Certifications: {deleted_certs}")

        if pros_qs is not None:
            deleted_pros = pros_qs.delete()[0]
            self.stdout.write(f"Eliminados Professionals: {deleted_pros}")

        # 5) Finalmente, borrar usuarios de demo
        deleted_users = users_qs.delete()[0]
        self.stdout.write(f"Eliminados Usuarios demo: {deleted_users}")

        self.stdout.write(self.style.SUCCESS("✅ Limpieza de datos de demo completada."))
