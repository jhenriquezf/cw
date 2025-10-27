# professionals/management/commands/seed_demo.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import transaction
from django.apps import apps
from decimal import Decimal
import random
import uuid
from datetime import datetime

User = get_user_model()

# --------- utilidades seguras ----------
def model_has_field(model, name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False

def field_choices(model, name: str):
    try:
        return model._meta.get_field(name).choices or []
    except Exception:
        return []

def first_choice_or(choices, preferred):
    if not choices:
        return None
    codes = [c[0] if isinstance(c, (list, tuple)) else c for c in choices]
    return preferred if preferred in codes else codes[0]

def get_choice_value(choices, idx=0, fallback=None):
    if not choices:
        return fallback
    v = choices[idx % len(choices)]
    return v[0] if isinstance(v, (list, tuple)) else v

def set_if_field(model, container: dict, field_name: str, value):
    if model_has_field(model, field_name):
        container[field_name] = value

# ---------------------------------------

class Command(BaseCommand):
    help = "Crea datos de prueba para las pantallas de búsqueda (search) y onboarding."

    @transaction.atomic
    def handle(self, *args, **options):
        # Obtiene modelos reales desde apps (evita import rígido)
        Professional = apps.get_model('professionals', 'Professional')
        Service = apps.get_model('services', 'Service')
        Certification = None
        try:
            Certification = apps.get_model('professionals', 'Certification')
        except Exception:
            pass

        password = "demo12345"
        base_names = [
            ("sofia", "garcia"),
            ("martin", "rojas"),
            ("camila", "perez"),
            ("diego", "torres"),
            ("valentina", "lopez"),
            ("nicolas", "soto"),
        ]

        # Choices (si los modelos los exponen como atributos de clase, se usan; si no, se leerán desde fields)
        primary_specialties = getattr(Professional, "PRIMARY_SPECIALTIES", [])
        comunas            = getattr(Professional, "COMUNAS", [])

        created_users = []

        for i, (first, last) in enumerate(base_names, start=1):
            # --- Usuario
            username = f"{first}{i}"
            email = f"{first}.{last}{i}@demo.local"
            user, _ = User.objects.get_or_create(username=username, defaults={
                "first_name": first.capitalize(),
                "last_name": last.capitalize(),
                "email": email,
            })
            user.set_password(password)
            user.save()
            created_users.append((user.username, email, password))

            # --- Professional profile (slug único)
            base_slug = slugify(f"{first}-{last}")
            slug = base_slug
            k = 0
            while Professional.objects.filter(username_slug=slug).exists():
                k += 1
                slug = f"{base_slug}-{k}" if k < 5 else f"{base_slug}-{uuid.uuid4().hex[:6]}"

            prof_defaults = {"username_slug": slug}

            # Campos opcionales que quizá existan en tu modelo
            if model_has_field(Professional, "primary_specialty"):
                prof_defaults["primary_specialty"] = get_choice_value(primary_specialties, i-1, None)
            if model_has_field(Professional, "comuna"):
                prof_defaults["comuna"] = get_choice_value(comunas, i-1, None)
            if model_has_field(Professional, "is_active"):
                prof_defaults["is_active"] = True
            if model_has_field(Professional, "verification_status"):
                vs_choices = field_choices(Professional, "verification_status")
                prof_defaults["verification_status"] = first_choice_or(vs_choices, "verified")
            if model_has_field(Professional, "average_rating"):
                prof_defaults["average_rating"] = round(random.uniform(3.3, 5.0), 1)
            if model_has_field(Professional, "total_reviews"):
                prof_defaults["total_reviews"] = random.randint(3, 120)
            if model_has_field(Professional, "total_bookings"):
                prof_defaults["total_bookings"] = random.randint(5, 300)

            prof, _ = Professional.objects.get_or_create(user=user, defaults=prof_defaults)

            # --- Services (2 por profesional), SOLO campos que existan
            for j in range(2):
                service_name = [
                    "Yoga Vinyasa", "Entrenamiento Funcional",
                    "Pilates Mat", "Mindfulness 1:1",
                    "Nutrición Deportiva", "Masoterapia"
                ][(i + j) % 6]

                # valores tentativos; solo se usarán si el campo existe
                duration_val = random.choice([45, 60, 90])
                price_val = Decimal(random.choice([15000, 20000, 25000, 30000, 35000, 40000]))

                # service_type / modality / level desde choices del modelo (si existen)
                st_val = None
                md_val = None
                lv_val = None
                if model_has_field(Service, "service_type"):
                    st_val = get_choice_value(field_choices(Service, "service_type"), i+j, None)
                if model_has_field(Service, "modality"):
                    md_val = get_choice_value(field_choices(Service, "modality"), i+j, None)
                if model_has_field(Service, "level"):
                    lv_val = get_choice_value(field_choices(Service, "level"), i+j, None)

                # build de defaults SEGURO
                service_defaults = {}
                set_if_field(Service, service_defaults, "description", f"Sesión de {service_name.lower()} orientada a resultados.")
                set_if_field(Service, service_defaults, "service_type", st_val)
                set_if_field(Service, service_defaults, "modality", md_val)
                set_if_field(Service, service_defaults, "duration_minutes", duration_val)
                set_if_field(Service, service_defaults, "level", lv_val)
                set_if_field(Service, service_defaults, "price", price_val)
                set_if_field(Service, service_defaults, "is_active", True)

                # ¡OJO! Nada de 'requirements' ni 'what_to_bring': solo se setean si existen

                Service.objects.get_or_create(
                    professional=prof,
                    name=f"{service_name} ({j+1})",
                    defaults=service_defaults
                )

            # --- Certifications (si el modelo existe)
            if Certification:
                year_now = datetime.now().year
                vs_verified = None
                vs_pending = None
                if model_has_field(Certification, "verification_status"):
                    vs_choices = field_choices(Certification, "verification_status")
                    vs_verified = first_choice_or(vs_choices, "verified")
                    vs_pending  = first_choice_or(vs_choices, "pending_review")

                plan = [
                    ("TRX Level 2", "Fitness Training Institute", year_now - random.randint(1, 6), vs_verified),
                    ("Mindfulness Coach", "Mindful Org", year_now - random.randint(1, 6), vs_pending),
                ]

                for cname, inst, cyear, vstatus in plan:
                    c = Certification(
                        professional=prof,
                        name=cname,
                        institution=inst,
                        year=cyear,
                    )
                    if vstatus and model_has_field(Certification, "verification_status"):
                        c.verification_status = vstatus

                    # adjunta un archivo mínimo si existe el campo document y es requerido
                    try:
                        from django.core.files.base import ContentFile
                        if model_has_field(Certification, "document") and not getattr(c, "document", None):
                            c.document.save(f"{slug}-{uuid.uuid4().hex[:4]}.txt",
                                            ContentFile(b"Demo certificate"),
                                            save=False)
                    except Exception:
                        pass

                    c.save()

        self.stdout.write(self.style.SUCCESS("✅ Seed de demo creado con éxito.\n"))
        self.stdout.write("Usuarios de prueba (usuario / email / password):")
        for u, e, p in created_users:
            self.stdout.write(f"  - {u} / {e} / {p}")
        self.stdout.write("\nVisita:")
        self.stdout.write("  • /profesionales/                          (búsqueda)")
        self.stdout.write("  • /profesionales/onboarding/certifications/  (onboarding)")
