from django import forms
from .models import CartItem, Order

class AddToCartForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'style': 'width: 70px;'
    }))

    class Meta:
        model = CartItem
        fields = ['quantity']

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