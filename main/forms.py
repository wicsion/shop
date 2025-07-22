from django import forms
from .models import CartItem, Order, DeliveryAddress


class SelectSizesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        cart_item = kwargs.pop('cart_item', None)
        super().__init__(*args, **kwargs)

        if product and product.has_variants:
            available_sizes = product.get_available_sizes()
            initial_sizes = getattr(cart_item, 'selected_sizes', {}) if cart_item else {}

            for size in available_sizes:
                self.fields[f'size_{size}'] = forms.IntegerField(
                    label=size,
                    min_value=0,
                    max_value=product.get_variant_quantity(size) or product.quantity,
                    initial=initial_sizes.get(size, 0),
                    required=False,
                    widget=forms.NumberInput(attrs={
                        'class': 'size-quantity-input border rounded px-3 py-1 w-full',
                    }))


class AddToCartForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'border rounded px-3 py-2 w-20 mr-4',
        }))
    selected_size = forms.CharField(
        required=False,  # Делаем необязательным
        widget=forms.HiddenInput()
    )
    size = forms.ChoiceField(
        required=False,  # Делаем необязательным
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
            if self.product.variants.exists() or self.product.sizes_available:
                size_choices = []
                if self.product.variants.exists():
                    for variant in self.product.variants.all().order_by('size'):
                        size_choices.append((variant.size, variant.size))
                elif self.product.sizes_available:
                    sizes = [s.strip() for s in self.product.sizes_available.split(',') if s.strip()]
                    size_choices = [(s, s) for s in sizes]

                if size_choices:
                    self.fields['size'].choices = [('', 'Выберите размер')] + size_choices
                else:
                    self.fields['size'].widget = forms.HiddenInput()
            else:
                self.fields['size'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        size = cleaned_data.get('size')
        selected_size = cleaned_data.get('selected_size')
        quantity = cleaned_data.get('quantity')

        # Если есть варианты размеров, но размер не выбран
        if (self.product.variants.exists() or self.product.sizes_available) and not size and not selected_size:
            raise forms.ValidationError("Пожалуйста, выберите размер")

        # Если размер выбран, проверяем его доступность
        if size and self.product.variants.exists():
            if not self.product.variants.filter(size__iexact=size).exists():
                raise forms.ValidationError("Выбранный размер недоступен")

        if self.product:
            if size and self.product.variants.exists():
                variant = self.product.variants.filter(size=size).first()
                if variant and quantity > variant.quantity:
                    raise forms.ValidationError("Недостаточно товара в наличии для выбранного размера")
            elif quantity > self.product.quantity:
                raise forms.ValidationError("Недостаточно товара в наличии")

        return cleaned_data


class OrderForm(forms.ModelForm):
    delivery_address = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'comment']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'company') and user.company.delivery_addresses.exists():
            addresses = user.company.delivery_addresses.all()
            choices = [('', 'Выберите сохранённый адрес')]
            choices += [(str(a.id), a.address) for a in addresses]
            choices.append(('new', 'Добавить новый адрес'))
            self.fields['delivery_address'].choices = choices
        else:
            self.fields['delivery_address'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        delivery_address_id = cleaned_data.get('delivery_address')
        address = cleaned_data.get('address')

        # Если выбран сохраненный адрес, используем его
        if delivery_address_id and delivery_address_id != 'new':
            try:
                address_obj = DeliveryAddress.objects.get(id=delivery_address_id)
                cleaned_data['address'] = address_obj.address  # Подставляем адрес из сохраненного
            except DeliveryAddress.DoesNotExist:
                self.add_error('delivery_address', 'Выбранный адрес не найден')
        # Если выбрано "новый адрес" или нет сохраненных адресов, проверяем поле address
        elif not address:
            self.add_error('address', 'Необходимо указать адрес доставки')

        return cleaned_data

class SearchForm(forms.Form):
    q = forms.CharField(
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск...',
        })
    )


