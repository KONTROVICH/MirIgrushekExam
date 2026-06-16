from django.db import models
from django.contrib.auth.models import AbstractUser
import os

from django.conf import settings

class User(AbstractUser):
    GUEST = 'guest'
    CLIENT = 'client'
    MANAGER = 'manager'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (GUEST, 'Гость'),
        (CLIENT, 'Клиент'),
        (MANAGER, 'Менеджер'),
        (ADMIN, 'Администратор'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=GUEST,
        verbose_name='Роль',
    )

    patronymic = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Отчество',
    )

    def get_full_name(self):
        full_name = super().get_full_name()
        if self.patronymic:
            full_name += f' {self.patronymic}'
        return full_name.strip()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class Category(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название',
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название',
    )

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'

    def __str__(self):
        return self.name

class Manufacturer(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название',
    )

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def __str__(self):
        return self.name

class Product(models.Model):
    article = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Артикул',
    )

    name = models.CharField(
        max_length=500,
        verbose_name='Наименование товара',
    )

    unit = models.CharField(
        max_length=50,
        default='шт.',
        verbose_name='Единица измерения',
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена',
    )

    discount = models.IntegerField(
        default=0,
        verbose_name='Скидка (%)',
    )

    stock_quantity = models.IntegerField(
        default=0,
        verbose_name='Кол-во на складе',
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        verbose_name='Изображение',
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name='Категория',
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        verbose_name='Поставщик',
    )

    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.CASCADE,
        verbose_name='Производитель',
    )

    def discounted_price(self):
        return round(float(self.price) * (1 - float(self.discount) / 100), 2)

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_product = Product.objects.get(pk=self.pk)
                if old_product.image and old_product.image != self.image:
                    old_image_path = os.path.join(settings.MEDIA_ROOT, str(old_product.image))
                    if os.path.isfile(old_image_path):
                        os.remove(old_image_path)
            except Product.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if self.image:
            self._resize_image()

    def _resize_image(self):
        try:
            from PIL import Image
            image_path = os.path.join(settings.MEDIA_ROOT, str(self.image))
            if os.path.isfile(image_path):
                img = Image.open(image_path)
                target_width = 300
                target_height = 200
                original_width, original_height = img.size
                ratio = max(target_width / original_width, target_height / original_height)
                new_size = (int(original_width * ratio), int(original_height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                left = (new_size[0] - target_width) // 2
                top = (new_size[1] - target_height) // 2
                right = left + target_width
                bottom = top + target_height
                img = img.crop((left, top, right, bottom))
                img.save(image_path)
        except Exception:
            pass

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return f'{self.article} - {self.name}'

class PickupPoint(models.Model):
    address = models.TextField(
        verbose_name='Адрес',
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код пункта выдачи',
    )

    class Meta:
        verbose_name = 'Пункт выдачи'
        verbose_name_plural = 'Пункты выдачи'

    def __str__(self):
        return f'{self.code}: {self.address}'

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('ready', 'Готов'),
        ('issued', 'Выдан'),
        ('cancelled', 'Отменён'),
    ]

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Номер заказа',
    )

    order_date = models.DateField(
        verbose_name='Дата заказа',
    )

    issue_date = models.DateField(
        verbose_name='Дата выдачи',
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус',
    )

    pickup_point = models.ForeignKey(
        PickupPoint,
        on_delete=models.CASCADE,
        verbose_name='Пункт выдачи',
    )

    client_name = models.CharField(
        max_length=500,
        verbose_name='ФИО клиента',
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ №{self.order_number}'

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ',
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар',
    )

    quantity = models.IntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product.article} x {self.quantity}'
