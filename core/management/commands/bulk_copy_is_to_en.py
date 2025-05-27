# core/management/commands/bulk_copy_is_to_en.py
from django.core.management.base import BaseCommand
from core.bulk_copy import duplicate_is_to_en

class Command(BaseCommand):
    help = "Copy Icelandic pages into the English locale."

    def handle(self, *args, **options):
        created, skipped = duplicate_is_to_en()
        self.stdout.write(
            self.style.SUCCESS(f"✓ {created} pages copied, {skipped} skipped")
        )
