# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm

from main.models import CartItem, Order, DeliveryAddress
from .models import Company, CustomUser, Document
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class CompanyRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Пароль',
        required=True
    )

    role = forms.ChoiceField(
        choices=CustomUser.ROLES,
        label='Должность',
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'hidden'})
    )
    first_name = forms.CharField(
        label='Имя',
        required=True
    )

    last_name = forms.CharField(
        label='Фамилия',
        required=True
    )

    middle_name = forms.CharField(
        label='Отчество',
        required=False
    )

    class Meta:
        model = Company
        fields = [
            'email',
            'inn',
            'legal_name',

        ]





class CompanyUserForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=CustomUser.ROLES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}))

    class Meta:
        model = CustomUser
        fields = [ 'email', 'phone', 'role', 'password1', 'password2']


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['doc_type', 'file']


class CartItemForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 70px'})
    )

    class Meta:
        model = CartItem
        fields = ['quantity']

class OrderCreateForm(forms.ModelForm):
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label='Примечания к заказу'
    )

    class Meta:
        model = Order
        fields = ['notes']



class EmailAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(
                request=self.request,
                email=email,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Неправильный email или пароль."
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    "Аккаунт не активирован. Проверьте вашу почту."
                )
        return self.cleaned_data


class DeliveryAddressForm(forms.ModelForm):
    class Meta:
        model = DeliveryAddress
        fields = ['address', 'is_default']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'w-full border rounded-lg px-3 py-2 text-sm'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-checkbox h-4 w-4 text-blue-600'})
        }