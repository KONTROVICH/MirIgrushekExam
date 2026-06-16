import os
import shutil
import openpyxl
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.conf import settings

from catalog.models import Category, Supplier, Manufacturer, Product, PickupPoint, Order, OrderItem, User


def _name_parts(full_name):
    parts = full_name.strip().split(maxsplit=2)
    last = parts[0] if len(parts) > 0 else ''
    first = parts[1] if len(parts) > 1 else ''
    patronymic = parts[2] if len(parts) > 2 else ''
    return last, first, patronymic


ROLE_MAP = {
    'Администратор': 'admin',
    'Менеджер': 'manager',
    'Клиент': 'client',
}

STATUS_MAP = {
    'Новый': 'new',
    'В обработке': 'processing',
    'Готов': 'ready',
    'Выдан': 'issued',
    'Отменён': 'cancelled',
    'Отменен': 'cancelled',
}


class Command(BaseCommand):
    help = 'Импорт данных из XLSX и изображений'

    def handle(self, *args, **options):
        import_dir = settings.BASE_DIR.parent / 'import'
        if not os.path.exists(import_dir):
            self.stdout.write(self.style.ERROR(f'Папка import не найдена: {import_dir}'))
            return

        self._import_users(import_dir)
        self._import_tovar(import_dir)
        self._import_pickup_points(import_dir)
        self._import_orders(import_dir)
        self._copy_images(import_dir)
        self.stdout.write(self.style.SUCCESS('Импорт завершён успешно.'))

    def _open_sheet(self, import_dir, xlsx_name):
        path = os.path.join(import_dir, xlsx_name)
        if not os.path.isfile(path):
            self.stdout.write(self.style.WARNING(f'Файл не найден: {xlsx_name}'))
            return None
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            return wb['Лист1']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка чтения {xlsx_name}: {e}'))
            return None

    def _rows(self, ws):
        if ws is None:
            return
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            yield row

    def _import_users(self, import_dir):
        ws = self._open_sheet(import_dir, 'user_import.xlsx')
        for row in self._rows(ws):
            try:
                role_raw = str(row[0] or '').strip()
                full_name = str(row[1] or '').strip()
                email = str(row[2] or '').strip()
                if not email:
                    continue
                if User.objects.filter(username=email).exists():
                    continue
                role = ROLE_MAP.get(role_raw, 'client')
                last, first, patronymic = _name_parts(full_name)
                User.objects.create_user(
                    username=email,
                    email=email,
                    password=str(row[3] or '12345'),
                    last_name=last,
                    first_name=first,
                    patronymic=patronymic,
                    role=role,
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка импорта пользователя: {e}'))

    def _get_or_create(self, model, name, default='Общее'):
        if not name:
            name = default
        obj, _ = model.objects.get_or_create(name=name)
        return obj

    def _import_tovar(self, import_dir):
        ws = self._open_sheet(import_dir, 'Tovar.xlsx')
        for row in self._rows(ws):
            try:
                article = str(row[0] or '').strip()
                if not article or Product.objects.filter(article=article).exists():
                    continue
                name = str(row[1] or '').strip()
                unit = str(row[2] or 'шт.').strip()
                price_str = str(row[3] or '0').replace(',', '.').strip()
                try:
                    price = Decimal(price_str)
                except InvalidOperation:
                    price = Decimal('0')
                supplier_name = str(row[4] or '').strip()
                manufacturer_name = str(row[5] or '').strip()
                category_name = str(row[6] or '').strip()
                discount_str = str(row[7] or '0').strip()
                try:
                    discount = int(float(discount_str))
                except ValueError:
                    discount = 0
                stock_str = str(row[8] or '0').strip()
                try:
                    stock_quantity = int(float(stock_str))
                except ValueError:
                    stock_quantity = 0
                description = str(row[9] or '').strip()
                category = self._get_or_create(Category, category_name)
                supplier = self._get_or_create(Supplier, supplier_name)
                manufacturer = self._get_or_create(Manufacturer, manufacturer_name)
                Product.objects.create(
                    article=article,
                    name=name,
                    unit=unit,
                    price=price,
                    discount=discount,
                    stock_quantity=stock_quantity,
                    description=description,
                    category=category,
                    supplier=supplier,
                    manufacturer=manufacturer,
                )
                image_file = str(row[10] or '').strip()
                if image_file:
                    src = os.path.join(import_dir, image_file)
                    if os.path.isfile(src):
                        media_products = os.path.join(settings.MEDIA_ROOT, 'products')
                        os.makedirs(media_products, exist_ok=True)
                        dst = os.path.join(media_products, image_file)
                        shutil.copy2(src, dst)
                        Product.objects.filter(article=article).update(
                            image=os.path.join('products', image_file).replace('\\', '/')
                        )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка импорта товара: {e}'))

    def _import_pickup_points(self, import_dir):
        ws = self._open_sheet(import_dir, 'Пункты выдачи_import.xlsx')
        for i, row in enumerate(self._rows(ws)):
            try:
                address = str(row[0] or '').strip()
                if not address:
                    continue
                code = f'ПВЗ-{i + 1:03d}'
                if not PickupPoint.objects.filter(code=code).exists():
                    PickupPoint.objects.create(code=code, address=address)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка импорта ПВЗ: {e}'))

    def _import_orders(self, import_dir):
        ws = self._open_sheet(import_dir, 'Заказ_import.xlsx')
        for row in self._rows(ws):
            try:
                order_number = str(row[0] or '').strip()
                if not order_number or Order.objects.filter(order_number=order_number).exists():
                    continue
                items_str = str(row[1] or '').strip()
                order_date = row[2]
                if isinstance(order_date, datetime):
                    order_date = order_date.date()
                elif isinstance(order_date, str):
                    try:
                        order_date = datetime.strptime(order_date.strip(), '%Y-%m-%d').date()
                    except ValueError:
                        order_date = datetime.now().date()
                else:
                    order_date = datetime.now().date()
                issue_date = row[3]
                if isinstance(issue_date, datetime):
                    issue_date = issue_date.date()
                elif isinstance(issue_date, str):
                    try:
                        issue_date = datetime.strptime(issue_date.strip(), '%Y-%m-%d').date()
                    except ValueError:
                        issue_date = order_date + timedelta(days=7)
                else:
                    issue_date = order_date + timedelta(days=7)
                pickup_code_int = row[4]
                pickup_code = str(pickup_code_int or '').strip()
                client_name = str(row[5] or '').strip()
                code = row[6]
                code_str = str(code or '').strip()
                status_raw = str(row[7] or 'Новый').strip()
                status = STATUS_MAP.get(status_raw, 'new')
                try:
                    pickup_point = PickupPoint.objects.get(code=code_str)
                except PickupPoint.DoesNotExist:
                    pickup_point, _ = PickupPoint.objects.get_or_create(
                        code=code_str or f'ПВЗ-XXX',
                        defaults={'address': 'Неизвестно'},
                    )
                order = Order.objects.create(
                    order_number=order_number,
                    order_date=order_date,
                    issue_date=issue_date,
                    status=status,
                    pickup_point=pickup_point,
                    client_name=client_name,
                )
                if items_str:
                    parts = items_str.split(',')
                    for j in range(0, len(parts), 2):
                        article = parts[j].strip()
                        qty = 1
                        if j + 1 < len(parts):
                            try:
                                qty = int(float(parts[j + 1].strip()))
                            except ValueError:
                                qty = 1
                        if article:
                            try:
                                product = Product.objects.get(article=article)
                                OrderItem.objects.create(
                                    order=order,
                                    product=product,
                                    quantity=qty,
                                )
                            except Product.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'Товар с артикулом {article} не найден')
                                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка импорта заказа: {e}'))

    def _copy_images(self, import_dir):
        media_products = os.path.join(settings.MEDIA_ROOT, 'products')
        os.makedirs(media_products, exist_ok=True)
        ws = self._open_sheet(import_dir, 'Tovar.xlsx')
        for row in self._rows(ws):
            try:
                article = str(row[0] or '').strip()
                image_file = str(row[10] or '').strip() if len(row) > 10 else ''
                if not article or not image_file:
                    continue
                src = os.path.join(import_dir, image_file)
                if not os.path.isfile(src):
                    base, ext = os.path.splitext(image_file)
                    src = os.path.join(import_dir, base + ext.upper())
                if os.path.isfile(src):
                    dst_name = f'{article}{os.path.splitext(image_file)[1].lower()}'
                    dst = os.path.join(media_products, dst_name)
                    shutil.copy2(src, dst)
                    image_rel_path = os.path.join('products', dst_name).replace('\\', '/')
                    Product.objects.filter(article=article).update(image=image_rel_path)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка копирования {image_file}: {e}'))
