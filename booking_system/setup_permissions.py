import os
import django
import sys

# Добавляем путь к проекту
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_system.settings')

try:
    django.setup()
    
    from django.contrib.auth.models import Group, Permission, User
    from django.contrib.contenttypes.models import ContentType
    from bookings.models import Booking, Service, TimeSlot, Category, Review
    
    def setup_groups_and_permissions():
        print("🔧 Настройка групп и прав доступа...")
        
        # Создаем группу Managers
        managers_group, created = Group.objects.get_or_create(name='Managers')
        if created:
            print("✓ Создана группа Managers")
        
        # Создаем группу Admins
        admins_group, created = Group.objects.get_or_create(name='Admins')
        if created:
            print("✓ Создана группа Admins")
        
        try:
            booking_ct = ContentType.objects.get_for_model(Booking)
            service_ct = ContentType.objects.get_for_model(Service)
            timeslot_ct = ContentType.objects.get_for_model(TimeSlot)
            category_ct = ContentType.objects.get_for_model(Category)
            review_ct = ContentType.objects.get_for_model(Review)
            user_ct = ContentType.objects.get_for_model(User)
            
            manager_permissions = []
            
            permissions_to_add = [
                (booking_ct, 'add_booking'),
                (booking_ct, 'change_booking'), 
                (booking_ct, 'delete_booking'),
                (booking_ct, 'view_booking'),
                
                (service_ct, 'view_service'),
                
                (timeslot_ct, 'add_timeslot'),
                (timeslot_ct, 'change_timeslot'),
                (timeslot_ct, 'delete_timeslot'),
                (timeslot_ct, 'view_timeslot'),
                
                (category_ct, 'view_category'),
                
                (review_ct, 'view_review'),
                (review_ct, 'change_review'),
                (review_ct, 'delete_review'),
            ]
            
            for content_type, codename in permissions_to_add:
                try:
                    perm = Permission.objects.get(content_type=content_type, codename=codename)
                    manager_permissions.append(perm)
                    print(f"  ✓ Добавлено право: {codename}")
                except Permission.DoesNotExist:
                    print(f"  ⚠ Право {codename} не найдено")
            
            admin_permissions = list(Permission.objects.all())
            
            managers_group.permissions.set(manager_permissions)
            admins_group.permissions.set(admin_permissions)
            
            print(f"✓ Права назначены группам:")
            print(f"  - Managers: {len(manager_permissions)} прав")
            print(f"  - Admins: {len(admin_permissions)} прав")
            
        except Exception as e:
            print(f"⚠ Ошибка при настройке прав: {e}")
        
        # Создаем тестовых пользователей с группами
        users_to_create = [
            {
                'username': 'manager',
                'password': 'manager123',
                'email': 'manager@beauty-salon.ru',
                'first_name': 'Анна',
                'last_name': 'Иванова',
                'is_staff': True,
                'groups': [managers_group]
            },
            {
                'username': 'admin', 
                'password': 'admin123',
                'email': 'admin@beauty-salon.ru',
                'first_name': 'Мария',
                'last_name': 'Петрова',
                'is_staff': True,
                'is_superuser': True,
                'groups': [admins_group]
            },
            {
                'username': 'testuser',
                'password': 'testpass123',
                'email': 'client@example.com',
                'first_name': 'Елена',
                'last_name': 'Сидорова',
                'groups': []
            },
            {
                'username': 'client1',
                'password': 'client123',
                'email': 'client1@example.com',
                'first_name': 'Ольга',
                'last_name': 'Кузнецова',
                'groups': []
            },
            {
                'username': 'client2', 
                'password': 'client123',
                'email': 'client2@example.com',
                'first_name': 'Ирина',
                'last_name': 'Смирнова',
                'groups': []
            }
        ]
        
        for user_data in users_to_create:
            username = user_data['username']
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False)
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                
                for group in user_data['groups']:
                    user.groups.add(group)
                
                print(f"✓ Создан пользователь: {username}")
            else:
                user.set_password(user_data['password'])
                user.save()
                print(f"✓ Обновлен пользователь: {username}")
        
        print("\n" + "="*50)
        print("✅ Настройка завершена!")
        print("\n👥 Доступные пользователи:")
        print("   Менеджер:     manager / manager123")
        print("   Администратор: admin / admin123") 
        print("   Клиенты:      testuser / testpass123")
        print("                 client1 / client123")
        print("                 client2 / client123")
        print(f"\n📊 Всего пользователей в системе: {User.objects.count()}")
        print("="*50)
    
    if __name__ == '__main__':
        setup_groups_and_permissions()

except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    print("\n🔧 Убедитесь, что:")
    print("   1. Django правильно установлен")
    print("   2. База данных настроена и миграции применены")
    print("   3. Вы находитесь в правильной директории проекта")
    print("   4. Файл settings.py доступен")