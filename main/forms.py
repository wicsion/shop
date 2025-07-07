from django import forms
from .models import CartItem, Order


class AddToCartForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'border rounded px-3 py-2 w-20 mr-4',
        }))
    selected_size = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    size = forms.ChoiceField(  # Добавляем поле size в начало класса
        required=False,
        widget=forms.Select(attrs={
            'class': 'border rounded px-3 py-2 w-full mb-4',
        })
    )

    class Meta:
        model = CartItem
        fields = ['quantity']

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        if self.product:
            # Устанавливаем максимальное значение для quantity
            if self.product.variants.exists():
                max_quantity = self.product.variants.first().quantity
            else:
                max_quantity = self.product.quantity
            self.fields['quantity'].widget.attrs['max'] = max_quantity

            # Добавляем варианты размеров
            if self.product.variants.exists():
                size_choices = []
                for variant in self.product.variants.all().order_by('size'):
                    if variant.quantity > 0:  # Показываем только доступные размеры
                        size_choices.append((variant.size, variant.size))
                self.fields['size'].choices = [('', 'Выберите размер')] + size_choices
                self.fields['size'].required = True
            elif self.product.sizes_available:
                sizes = [s.strip() for s in self.product.sizes_available.split(',') if s.strip()]
                self.fields['size'].choices = [('', 'Выберите размер')] + [(s, s) for s in sizes]
                self.fields['size'].required = True
            else:
                self.fields['size'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        size = cleaned_data.get('size')
        quantity = cleaned_data.get('quantity')

        if self.product:
            if size and self.product.variants.exists():
                variant = self.product.variants.filter(size=size).first()
                if variant and quantity > variant.quantity:
                    raise forms.ValidationError("Недостаточно товара в наличии для выбранного размера")
            elif quantity > self.product.quantity:
                raise forms.ValidationError("Недостаточно товара в наличии")

        return cleaned_data

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'comment']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SearchForm(forms.Form):
    q = forms.CharField(
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск...',
        })
    )