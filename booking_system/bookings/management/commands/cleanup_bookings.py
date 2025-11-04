from django.core.management.base import BaseCommand
from bookings.models import Booking

class Command(BaseCommand):
    help = 'Автоматическое обслуживание бронирований'
    
    def handle(self, *args, **options):
        # Отменяем просроченные неподтвержденные бронирования
        cancelled_count = Booking.cleanup_expired_pending()
        
        # Завершаем прошедшие подтвержденные бронирования
        completed_count = Booking.complete_past_bookings()
        
        if cancelled_count > 0 or completed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Отменено {cancelled_count} просроченных бронирований, '
                    f'завершено {completed_count} прошедших бронирований'
                )
            )
        else:
            self.stdout.write('Нет бронирований для обслуживания')