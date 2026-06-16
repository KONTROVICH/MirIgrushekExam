import os
from django import forms
from django.conf import settings
from .models import Product, Order

class ProductForm(forms.ModelForm):
    clear_image = forms.BooleanField(
        required=False,
        label='Удалить текущее изображение',
    )

    class Meta:
        model = Product
        fields = [
            'article', 'name', 'unit', 'price', 'discount',
            'stock_quantity', 'description', 'image',
            'category', 'supplier', 'manufacturer',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной.')
        return price

    def clean_stock_quantity(self):
        quantity = self.cleaned_data.get('stock_quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Количество не может быть отрицательным.')
        return quantity

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('clear_image') and instance.image:
            old_path = os.path.join(settings.MEDIA_ROOT, str(instance.image))
            if os.path.isfile(old_path):
                os.remove(old_path)
            instance.image.delete(save=False)
            instance.image = None
        if commit:
            instance.save()
        return instance

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_number', 'order_date', 'issue_date',
            'status', 'pickup_point', 'client_name',
        ]
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
        }
