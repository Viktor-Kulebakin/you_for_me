import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
from dating_app.models import Profile, Action

class Command(BaseCommand):
    help = 'Генерация тысяч моковых анкет и лайков'

    def handle(self, *args, **kwargs):
        fake = Faker(['ru_RU'])
        self.stdout.write('Генерация данных начата...')

        # 1. Создаем пользователей и профили
        genders = ['male', 'female']
        statuses = ['searching', 'busy', 'talking']
        profiles = []

        for _ in range(100): # Можно выставить 1000+
            username = fake.unique.email()
            user = User.objects.create_user(username=username, email=username, password='password123')
            profile = Profile(
                user=user,
                first_name=fake.first_name(),
                gender=random.choice(genders),
                age=random.randint(18, 50),
                city=fake.city(),
                interests=fake.text(max_nb_chars=100),
                status=random.choice(statuses)
            )
            profiles.append(profile)
        
        Profile.objects.bulk_create(profiles)
        self.stdout.write(self.style.SUCCESS(f'Создано {len(profiles)} анкет!'))
