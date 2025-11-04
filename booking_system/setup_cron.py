import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_system.settings')
django.setup()

def run_cleanup():
    """Запуск автоматической очистки"""
    call_command('cleanup_bookings')

if __name__ == '__main__':
    run_cleanup()