# professionals/management/commands/seed_demo.py
import random
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import transaction
from django.apps import apps
from django.core.files.base import ContentFile

try:
    from faker import Faker
except ImportError:
    raise ImportError("Por favor, instala la biblioteca Faker para usar este seeder: pip install Faker")

User = get_user_model()

# --------- Utilidades seguras (sin cambios) ----------
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
    codes = [c[0] for c in choices]
    return preferred if preferred in codes else codes[0]

def get_choice_value(choices, idx=0, fallback=None):
    if not choices:
        return fallback
    v = choices[idx % len(choices)]
    return v[0] if isinstance(v, (list, tuple)) else v

def set_if_field(model, container: dict, field_name: str, value):
    if model_has_field(model, field_name):
        container[field_name] = value

# -----------------------------------------------------

class Command(BaseCommand):
    help = "Crea datos de prueba realistas y completos para todas las funcionalidades de la aplicación."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando la creación de datos de demostración...")

        # --- Carga segura de modelos ---
        Professional = apps.get_model('professionals', 'Professional')
        Service = apps.get_model('services', 'Service')
        Client = apps.get_model('clients', 'Client') if apps.is_installed('clients') else None
        Certification = apps.get_model('professionals', 'Certification') if apps.is_installed('professionals') else None
        Review = apps.get_model('reviews', 'Review') if apps.is_installed('reviews') else None
        Appointment = apps.get_model('appointments', 'Appointment') if apps.is_installed('appointments') else None

        faker = Faker('es_CL')

        primary_specialties = [
            "Yoga Instructor", "Personal Trainer", "Nutritionist", "Physical Therapist",
            "Pilates Instructor", "Mindfulness Coach", "Massage Therapist", "Acupuncturist",
            "Holistic Health Practitioner", "Reiki Master"
        ]
        
        comunas = [
            "Las Condes", "Providencia", "Santiago", "Vitacura", "Ñuñoa",
            "La Reina", "Lo Barnechea", "Macul", "Peñalolén", "La Florida"
        ]

        service_names = [
            "Yoga Vinyasa Flow", "Entrenamiento de Fuerza", "Consulta Nutricional", "Terapia de Masaje Deportivo",
            "Clase de Pilates Reformer", "Sesión de Meditación Guiada", "Rehabilitación de Lesiones",
            "Acupuntura para el Estrés", "Terapia Reiki Energética", "Coaching de Bienestar Integral"
        ]
        
        cert_names = [
            ("Yoga Alliance RYT 200", "Yoga Alliance"), ("Certified Personal Trainer (CPT)", "NASM"),
            ("Registered Dietitian Nutritionist (RDN)", "Commission on Dietetic Registration"),
            ("Licensed Massage Therapist (LMT)", "State Medical Board"), ("Certified Pilates Teacher", "PMA"),
            ("Mindfulness-Based Stress Reduction (MBSR) Instructor", "UMass Memorial Health"),
        ]

        password = "demo"
        created_users = []
        self.stdout.write(f"Creando 20 profesionales...")

        for i in range(20):
            first_name = faker.first_name()
            last_name = faker.last_name()
            username = f"{slugify(first_name)}{random.randint(10,99)}"
            email = f"{username}@demo.local"
            
            user, created = User.objects.get_or_create(username=username, defaults={
                "first_name": first_name, "last_name": last_name, "email": email,
            })
            user.set_password(password)
            user.save()
            
            if created:
                created_users.append((user.username, email, password))

            base_slug = slugify(f"{first_name}-{last_name}")
            slug = f"{base_slug}-{i}"
            specialty = random.choice(primary_specialties)
            
            prof_defaults = {
                "username_slug": slug, "primary_specialty": specialty, "comuna": random.choice(comunas),
                "bio": f"Soy un(a) {specialty.lower()} con más de {random.randint(3, 15)} años de experiencia. {faker.paragraph(nb_sentences=4)}",
                "is_active": True, "verification_status": "verified", "average_rating": round(random.uniform(3.8, 5.0), 1),
                "total_reviews": 0, "total_bookings": 0,
            }
            
            prof, _ = Professional.objects.update_or_create(user=user, defaults=prof_defaults)

            num_services = random.randint(1, 4)
            professional_services = []
            for j in range(num_services):
                service_name = random.choice(service_names)
                service_defaults = {
                    "description": f"Sesión personalizada de {service_name.lower()}. {faker.paragraph(nb_sentences=2)}",
                    "price": Decimal(random.randrange(15000, 50000, 5000)),
                    "duration_minutes": random.choice([30, 45, 60, 90]),
                    "modality": random.choice([c[0] for c in field_choices(Service, "modality")]),
                    "service_type": random.choice([c[0] for c in field_choices(Service, "service_type")]),
                    "is_active": True,
                }
                service, _ = Service.objects.update_or_create(professional=prof, name=service_name, defaults=service_defaults)
                professional_services.append(service)
            
            if Certification:
                num_certs = random.randint(0, 5)
                for _ in range(num_certs):
                    cert_name, institution = random.choice(cert_names)
                    Certification.objects.create(
                        professional=prof, name=cert_name, institution=institution,
                        year=random.randint(2010, datetime.now().year), verification_status="verified",
                    )
            
            # --- CORRECCIÓN: Se crean citas y luego reseñas asociadas a esas citas ---
            if Review and Appointment and Client and professional_services:
                num_bookings = random.randint(10, 50)
                for _ in range(num_bookings):
                    # 1. Crear un cliente para la cita/reseña
                    client_user = User.objects.create(username=f"client_{uuid.uuid4().hex[:8]}", first_name=faker.first_name())
                    client_profile, _ = Client.objects.get_or_create(user=client_user)

                    # 2. Crear una cita (booking) completada en el pasado
                    service_booked = random.choice(professional_services)
                    start_time = datetime.now() - timedelta(days=random.randint(1, 365), hours=random.randint(1, 12))
                    
                    completed_appointment = Appointment.objects.create(
                        professional=prof,
                        client=client_profile,
                        service=service_booked, # Asumiendo que Appointment tiene un campo 'service'
                        start_time=start_time,
                        end_time=start_time + timedelta(minutes=service_booked.duration_minutes),
                        status='completed', # Importante: la cita debe estar completada
                    )

                    # 3. Crear la reseña ASOCIADA a la cita recién creada
                    Review.objects.create(
                        professional=prof,
                        client=client_profile,
                        booking=completed_appointment, # Se enlaza la cita a la reseña
                        rating=random.randint(4, 5),
                        comment=faker.paragraph(nb_sentences=3),
                        is_approved=True,
                    )
                
                # Actualizar contadores
                prof.total_bookings = num_bookings
                prof.total_reviews = num_bookings

            prof.save()

        self.stdout.write(self.style.SUCCESS("\n✅ Seed de demo creado con éxito."))
        self.stdout.write("Se han creado 20 profesionales con datos realistas.")
        self.stdout.write("\n--- Credenciales de ejemplo (usuario / email / password) ---")
        for u, e, p in created_users[:5]:
            self.stdout.write(f"  - {u} / {e} / {p}")
        self.stdout.write("\nVisita las siguientes URLs para probar:")
        self.stdout.write("  • /results/                          (página de resultados con filtros)")
        self.stdout.write("  • /<slug-del-profesional>/          (perfil detallado con reseñas)")