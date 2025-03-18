from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from catalog.models import Flower

class FlowerModelTest(TestCase):
    def setUp(self):
        # Создаем тестовое изображение
        self.image = SimpleUploadedFile(
            name="test_image.jpg",
            content=b"file_content",
            content_type="image/jpeg"
        )

    def test_flower_creation(self):
        """Тест создания объекта Flower."""
        flower = Flower.objects.create(
            name="Роза",
            price=500.00,
            image=self.image
        )

        # Проверяем, что объект создан корректно
        self.assertEqual(flower.name, "Роза")
        self.assertEqual(flower.price, 500.00)
        self.assertTrue(flower.image)

    def test_flower_image_preview(self):
        """Тест метода image_preview."""
        flower = Flower.objects.create(
            name="Роза",
            price=500.00,
            image=self.image
        )

        # Проверяем, что метод возвращает корректный HTML-код для превью изображения
        self.assertIn('<img src="', flower.image_preview())

class CatalogViewsTest(TestCase):
    def setUp(self):
        # Создаем клиент для тестирования
        self.client = Client()

        # Создаем тестовое изображение
        self.image = SimpleUploadedFile(
            name="test_image.jpg",
            content=b"file_content",
            content_type="image/jpeg"
        )

        # Создаем несколько цветов для тестирования
        Flower.objects.create(name="Роза", price=500.00, image=self.image)
        Flower.objects.create(name="Тюльпан", price=300.00, image=self.image)

    def test_flower_list_view(self):
        """Тест доступности страницы каталога."""
        # Получаем URL для страницы каталога
        url = reverse("flower_list")
        # Выполняем GET-запрос к странице каталога
        response = self.client.get(url)

        # Проверяем, что статус ответа равен 200 (успешно)
        self.assertEqual(response.status_code, 200)

    def test_flower_list_view_template(self):
        """Тест корректного шаблона для страницы каталога."""
        # Получаем URL для страницы каталога
        url = reverse("flower_list")
        # Выполняем GET-запрос к странице каталога
        response = self.client.get(url)

        # Проверяем, что используется правильный шаблон
        self.assertTemplateUsed(response, "catalog/catalog.html")

    def test_flower_list_view_context(self):
        """Тест передачи списка цветов в контекст шаблона."""
        # Получаем URL для страницы каталога
        url = reverse("flower_list")
        # Выполняем GET-запрос к странице каталога
        response = self.client.get(url)

        # Проверяем, что в контексте передаются все цветы
        self.assertEqual(len(response.context["flowers"]), 2)