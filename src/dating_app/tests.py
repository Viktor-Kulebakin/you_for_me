from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Profile, Action

class DatingActionTests(APITestCase):
    def setUp(self):
        # Создаем двух тестовых пользователей
        self.user1 = User.objects.create_user(username='user1@test.ru', email='user1@test.ru', password='password123')
        self.user2 = User.objects.create_user(username='user2@test.ru', email='user2@test.ru', password='password123')
        
        # Создаем им профили
        self.profile1 = Profile.objects.create(user=self.user1, first_name="Иван", gender="male", age=25, city="Москва")
        self.profile2 = Profile.objects.create(user=self.user2, first_name="Анна", gender="female", age=23, city="Москва")

    def test_like_profile(self):
        """Проверка отправки лайка (без взаимности)"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('profile-like', kwargs={'pk': self.profile2.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем структуру ответа из ProfileViewSet
        self.assertEqual(response.data['liked'], True)
        self.assertEqual(response.data['is_match'], False) # Мэтча еще нет, Анна не лайкала
        
        # Проверяем физическое наличие записи в PostgreSQL
        self.assertTrue(Action.objects.filter(from_profile=self.profile1, to_profile=self.profile2, action_type='like').exists())

    def test_mutual_match(self):
        """Проверка фиксации взаимного мэтча (требование К7)"""
        # 1. Сначала Анна (user2) лайкает Ивана (profile1) напрямую через базу данных
        Action.objects.create(from_profile=self.profile2, to_profile=self.profile1, action_type='like')
        
        # 2. Иван (user1) авторизуется и лайкает Анну через API
        self.client.force_authenticate(user=self.user1)
        url = reverse('profile-like', kwargs={'pk': self.profile2.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Проверяем, что система распознала взаимную симпатию
        self.assertEqual(response.data['liked'], True)
        self.assertEqual(response.data['is_match'], True) # Теперь мэтч зафиксирован!
