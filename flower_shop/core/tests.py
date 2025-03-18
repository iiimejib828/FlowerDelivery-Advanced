from django.test import TestCase, Client
from django.urls import reverse

class CoreViewsTest(TestCase):
    def setUp(self):
        # Создаем клиент для тестирования
        self.client = Client()

    def test_home_view(self):
        """Тест доступности главной страницы."""
        # Получаем URL для главной страницы
        url = reverse("home")
        # Выполняем GET-запрос к главной странице
        response = self.client.get(url)

        # Проверяем, что статус ответа равен 200 (успешно)
        self.assertEqual(response.status_code, 200)

    def test_home_view_template(self):
        """Тест корректного шаблона для главной страницы."""
        # Получаем URL для главной страницы
        url = reverse("home")
        # Выполняем GET-запрос к главной странице
        response = self.client.get(url)

        # Проверяем, что используется правильный шаблон
        self.assertTemplateUsed(response, "core/home.html")