# forms.py (создайте новый файл)
from django import forms
from .models import ProductSilhouette, CustomProductImage

class SilhouetteEditForm(forms.ModelForm):
    base_image = forms.ModelChoiceField(
        queryset=CustomProductImage.objects.none(),
        label="Выберите базовое изображение",
        required=False
    )

    class Meta:
        model = ProductSilhouette
        fields = ['mask_image']
        widgets = {
            'mask_image': forms.FileInput(attrs={'accept': 'image/*'})
        }

    def __init__(self, *args, **kwargs):
        template_id = kwargs.pop('template_id', None)
        super().__init__(*args, **kwargs)

        if template_id:
            self.fields['base_image'].queryset = CustomProductImage.objects.filter(
                template_id=template_id
            ).order_by('order')

            # Автоматически выбираем изображение силуэта, если оно существует
            silhouette_image = CustomProductImage.objects.filter(
                template_id=template_id,
                is_silhouette=True
            ).first()
            if silhouette_image:
                self.fields['base_image'].initial = silhouette_image