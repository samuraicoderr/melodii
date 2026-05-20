import os
import sys

import django
from rest_framework.exceptions import ValidationError


def _setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")
    django.setup()


def _prompt_file_path() -> str:
    while True:
        file_path = input("Enter the path to an audio file: ").strip()
        if not file_path:
            print("File path is required.")
            continue
        if not os.path.isfile(file_path):
            print("File does not exist. Try again.")
            continue
        return file_path


def _prompt_model_choice() -> str:
    from django.conf import settings

    options = [
        ("1", settings.GENRE_AI_DEFAULT_MODEL, True),
        ("2", "custom-cnn", False),
        ("3", "random-forest", False),
    ]

    print("\nChoose a model:")
    for key, model_name, enabled in options:
        status = "available" if enabled else "unavailable"
        print(f"  {key}. {model_name} ({status})")

    while True:
        choice = input("Select 1-3: ").strip()
        match = next((item for item in options if item[0] == choice), None)
        if not match:
            print("Invalid choice. Try again.")
            continue
        if not match[2]:
            print("That model will be available in V2. Pick another.")
            continue
        return match[1]


def main() -> int:
    _setup_django()

    from src.genre_ai.services import GenreAIService

    file_path = _prompt_file_path()
    model_name = _prompt_model_choice()

    try:
        result = GenreAIService.classify_file_path(file_path, model_name=model_name)
    except ValidationError as exc:
        print(f"Validation error: {exc}")
        return 2
    except Exception:
        print("Classification failed. Please try again.")
        return 1

    top = result["top_prediction"]
    print("\nPrediction complete")
    print(f"Model: {result['model_used']}")
    print(f"File: {result['filename']}")
    print(f"Top genre: {top['label']} ({top['score']:.3f})")

    print("\nTop 5 predictions:")
    for idx, prediction in enumerate(result["predictions"], start=1):
        print(f"  {idx}. {prediction['label']} ({prediction['score']:.3f})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
