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

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        selected_size = self.cleaned_data.get('selected_size')

        if self.product:
            if selected_size:
                variant = self.product.variants.filter(size=selected_size).first()
                if variant and quantity > variant.quantity:
                    raise forms.ValidationError("Недостаточно товара в наличии")
            elif quantity > self.product.quantity:
                raise forms.ValidationError("Недостаточно товара в наличии")

        return quantity

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