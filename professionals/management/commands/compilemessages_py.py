from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from pathlib import Path
import polib

class Command(BaseCommand):
    help = "Compila archivos .po a .mo sin GNU gettext (usa polib). Busca en LOCALE_PATHS, BASE_DIR/locale y locale/ de cada app."

    def add_arguments(self, parser):
        parser.add_argument("--locale","-l",action="append",dest="locales",default=[],
                            help="Locales a compilar (ej.: -l es -l pt). Si se omite, compila todos los encontrados.")

    def handle(self, *args, **options):
        search_roots = set()

        # 1) LOCALE_PATHS definidos en settings
        for p in getattr(settings, "LOCALE_PATHS", []):
            search_roots.add(Path(p))

        # 2) locale/ a nivel proyecto
        search_roots.add(Path(settings.BASE_DIR) / "locale")

        # 3) locale/ en cada app instalada
        for app_config in apps.get_app_configs():
            search_roots.add(Path(app_config.path) / "locale")

        locales_filter = set(options["locales"] or [])
        compiled = 0

        for root in search_roots:
            if not root.exists():
                continue
            for lang_dir in root.iterdir():
                if not lang_dir.is_dir():
                    continue
                lang = lang_dir.name
                if locales_filter and lang not in locales_filter:
                    continue
                po_path = lang_dir / "LC_MESSAGES" / "django.po"
                mo_path = lang_dir / "LC_MESSAGES" / "django.mo"
                if po_path.exists():
                    self.stdout.write(f"Compilando {po_path} -> {mo_path}")
                    po = polib.pofile(str(po_path))
                    mo_path.parent.mkdir(parents=True, exist_ok=True)
                    po.save_as_mofile(str(mo_path))
                    compiled += 1

        if compiled == 0:
            self.stdout.write(self.style.WARNING("No se encontraron .po para compilar."))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Compilación completada. Archivos generados: {compiled}"))
