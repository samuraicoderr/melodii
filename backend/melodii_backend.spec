# PyInstaller spec for Melodii backend sidecar
# Build from backend/ with: pyinstaller melodii_backend.spec

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

backend_root = Path.cwd()

ffmpeg_dir = backend_root / "ffmpeg"
models_dir = backend_root / "models"

hiddenimports = (
    collect_submodules("django")
    + collect_submodules("rest_framework")
    + collect_submodules("celery")
    + collect_submodules("kombu")
    + collect_submodules("billiard")
    + collect_submodules("sentry_sdk")
)

# Django templates, static, and app data
collects = []
collects += collect_data_files("django")
collects += collect_data_files("rest_framework")
collects += collect_data_files("celery")
collects += collect_data_files("sentry_sdk")

third_party_apps = [
    "actstream",
    "autoslug",
    "channels",
    "channels_redis",
    "corsheaders",
    "countries_plus",
    "daphne",
    "django_celery_beat",
    "django_cities_light",
    "django_countries",
    "django_countries_plus",
    "django_csp",
    "django_dotenv",
    "django_extensions",
    "django_filters",
    "django_inlinecss",
    "django_jet",
    "django_money",
    "django_redis",
    "django_rest_passwordreset",
    "django_summernote",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "easy_thumbnails",
    "health_check",
    "phonenumber_field",
    "social_core",
    "social_django",
    "storages",
    "webauthn",
    "whitenoise",
]

for app in third_party_apps:
    hiddenimports += collect_submodules(app)
    collects += collect_data_files(app)

# Include the backend package
collects.append((str(backend_root / "src"), "src"))

# Bundle ffmpeg and model artifacts if present
if ffmpeg_dir.exists():
    collects.append((str(ffmpeg_dir), "ffmpeg"))
if models_dir.exists():
    collects.append((str(models_dir), "models"))

block_cipher = None

analysis = Analysis(
    [str(backend_root / "launcher" / "run_backend.py")],
    pathex=[str(backend_root)],
    binaries=[],
    datas=collects,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    name="melodii-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
