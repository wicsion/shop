from django import forms
from .models import ProductSilhouette, CustomProductImage

class SilhouetteEditForm(forms.ModelForm):
    front_base_image = forms.ModelChoiceField(
        queryset=CustomProductImage.objects.none(),
        label="Выберите базовое изображение для передней стороны",
        required=False
    )
    back_base_image = forms.ModelChoiceField(
        queryset=CustomProductImage.objects.none(),
        label="Выберите базовое изображение для тыловой стороны",
        required=False
    )

    class Meta:
        model = ProductSilhouette
        fields = ['front_mask_image', 'back_mask_image', 'colored_areas']
        widgets = {
            'front_mask_image': forms.FileInput(attrs={'accept': 'image/*'}),
            'back_mask_image': forms.FileInput(attrs={'accept': 'image/*'})
        }

    def __init__(self, *args, **kwargs):
        template_id = kwargs.pop('template_id', None)
        super().__init__(*args, **kwargs)

        if template_id:
            self.fields['front_base_image'].queryset = CustomProductImage.objects.filter(
                template_id=template_id
            ).order_by('order')
            self.fields['back_base_image'].queryset = CustomProductImage.objects.filter(
                template_id=template_id
            ).order_by('order')

            # Автоматически выбираем изображения силуэтов, если они существуют
            front_silhouette_image = CustomProductImage.objects.filter(
                template_id=template_id,
                is_front=True,
                is_silhouette=True
            ).first()
            if front_silhouette_image:
                self.fields['front_base_image'].initial = front_silhouette_image

            back_silhouette_image = CustomProductImage.objects.filter(
                template_id=template_id,
                is_back=True,
                is_silhouette=True
            ).first()
            if back_silhouette_image:
                self.fields['back_base_image'].initial = back_silhouette_image