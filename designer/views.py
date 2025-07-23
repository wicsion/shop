import os

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (
    CustomProductTemplate, UserCustomDesign,
    CustomDesignElement, CustomProductColor,
    CustomDesignArea, CustomProductOrder, ProductSilhouette
)
import uuid
import logging
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import ProductSilhouette
from .forms import SilhouetteEditForm
from .models import CustomProductTemplate, ProductMask
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
import json


def custom_designer_start(request):
    logger = logging.getLogger(__name__)
    logger.debug("Custom designer start view called")

    template = CustomProductTemplate.objects.filter(active=True).first()
    logger.debug(f"Found template: {template}")

    if not template:
        logger.warning("No active templates found")
        return redirect('main:home')

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    logger.debug(f"Session key: {session_key}")

    try:
        user_design, created = UserCustomDesign.objects.get_or_create(
            user_session=session_key,
            template=template,
            defaults={'template': template}
        )
        logger.debug(f"User design: {user_design.id}, created: {created}")
    except Exception as e:
        logger.error(f"Error creating user design: {e}")
        return redirect('main:home')

    # Получаем все активные цвета
    colors = CustomProductColor.objects.filter(active=True)

    # Сохранение выбранного цвета в сессии
    selected_color_id = request.session.get('selected_color_id')
    if selected_color_id:
        try:
            selected_color = colors.get(id=selected_color_id)
        except CustomProductColor.DoesNotExist:
            selected_color = colors.first()
    else:
        selected_color = colors.first()

    # Создаём контекст
    areas = template.design_areas.all()
    sizes = template.get_available_sizes()
    front_image = template.images.filter(is_front=True).first()
    back_image = template.images.filter(is_back=True).first()

    context = {
        'design': user_design,
        'template': template,
        'areas': areas,
        'colors': colors,
        'sizes': sizes,
        'front_image': front_image,
        'back_image': back_image,
        'selected_color': selected_color,
    }

    return render(request, 'designer/designer.html', context)


def custom_designer_edit(request, design_id):
    design = get_object_or_404(UserCustomDesign, id=design_id)
    template = design.template
    areas = template.design_areas.all()
    colors = CustomProductColor.objects.filter(active=True)
    sizes = template.get_available_sizes()

    front_image = template.images.filter(is_front=True).first()
    back_image = template.images.filter(is_back=True).first()

    context = {
        'design': design,
        'template': template,
        'areas': areas,
        'colors': colors,
        'sizes': sizes,
        'front_image': front_image,
        'back_image': back_image,
    }
    return render(request, 'designer/custom_designer.html', context)


@csrf_exempt
def save_custom_design_element(request):
    if request.method == 'POST':
        design_id = request.POST.get('design_id')
        area_id = request.POST.get('area_id')
        text_content = request.POST.get('text_content', '')
        color = request.POST.get('color', '#000000')
        font_size = request.POST.get('font_size', 14)

        design = get_object_or_404(UserCustomDesign, id=design_id)
        area = get_object_or_404(CustomDesignArea, id=area_id)

        element, created = CustomDesignElement.objects.get_or_create(
            design=design,
            area=area,
            defaults={
                'text_content': text_content,
                'color': color,
                'font_size': font_size
            }
        )

        if not created:
            element.text_content = text_content
            element.color = color
            element.font_size = font_size
            element.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def save_custom_design_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        design_id = request.POST.get('design_id')
        area_id = request.POST.get('area_id')

        design = get_object_or_404(UserCustomDesign, id=design_id)
        area = get_object_or_404(CustomDesignArea, id=area_id)

        element, created = CustomDesignElement.objects.get_or_create(
            design=design,
            area=area
        )

        element.image = request.FILES['image']
        element.save()

        return JsonResponse({
            'status': 'success',
            'image_url': element.image.url
        })

    return JsonResponse({'status': 'error'}, status=400)


def preview_custom_design(request, design_id):
    design = get_object_or_404(UserCustomDesign, id=design_id)
    return render(request, 'designer/custom_preview.html', {'design': design})


@csrf_exempt
def save_custom_design_order(request):
    if request.method == 'POST':
        design_id = request.POST.get('design_id')
        color_id = request.POST.get('color_id')
        size = request.POST.get('size')
        quantity = request.POST.get('quantity', 1)

        design = get_object_or_404(UserCustomDesign, id=design_id)
        color = get_object_or_404(CustomProductColor, id=color_id) if color_id else None

        price = design.template.base_price * int(quantity)

        order = CustomProductOrder.objects.create(
            design=design,
            selected_color=color,
            quantity=quantity,
            price=price
        )

        return JsonResponse({
            'status': 'success',
            'order_id': order.id,
            'redirect_url': '/cart/'  # Измените на ваш URL корзины
        })

    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def save_custom_element(request):
    if request.method == 'POST':
        design_id = request.POST.get('design_id')
        x_position = request.POST.get('x_position', 0)
        y_position = request.POST.get('y_position', 0)
        width = request.POST.get('width', 200)
        height = request.POST.get('height', 50)
        text_content = request.POST.get('text_content', '')
        color = request.POST.get('color', '#000000')
        font_size = request.POST.get('font_size', 14)
        side = request.POST.get('side', 'front')  # Получаем сторону

        design = get_object_or_404(UserCustomDesign, id=design_id)
        template = design.template

        # Create a new area for this element
        area = CustomDesignArea.objects.create(
            template=template,
            name=f"User Area {uuid.uuid4().hex[:6]}",
            x_position=x_position,
            y_position=y_position,
            width=width,
            height=height,
            allow_text=True,
            allow_images=True
        )

        if request.FILES.get('image'):
            element = CustomDesignElement.objects.create(
                design=design,
                area=area,
                image=request.FILES['image'],
                side=side  # Сохраняем сторону
            )
        elif text_content:
            element = CustomDesignElement.objects.create(
                design=design,
                area=area,
                text_content=text_content,
                color=color,
                font_size=font_size,
                side=side  # Сохраняем сторону
            )
        else:
            return JsonResponse({'status': 'error', 'message': 'No content provided'}, status=400)

        return JsonResponse({
            'status': 'success',
            'element_id': element.id,
            'area_id': area.id
        })

    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def delete_custom_element(request):
    if request.method == 'POST':
        element_id = request.POST.get('element_id')
        element = get_object_or_404(CustomDesignElement, id=element_id)
        area = element.area
        element.delete()
        area.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def save_selected_color(request):
    if request.method == 'POST':
        color_id = request.POST.get('color_id')
        request.session['selected_color_id'] = color_id
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def add_custom_color(request):
    if request.method == 'POST':
        color_type = request.POST.get('type')

        if color_type == 'solid':
            hex_code = request.POST.get('value')
            color = CustomProductColor.objects.create(
                name=f"Custom Color {hex_code}",
                hex_code=hex_code,
                active=True
            )
        elif color_type == 'gradient':
            gradient_css = request.POST.get('value')
            color = CustomProductColor.objects.create(
                name=f"Custom Gradient",
                gradient_css=gradient_css,
                active=True
            )
        elif color_type == 'pattern' and request.FILES.get('image'):
            pattern_image = request.FILES['image']
            color = CustomProductColor.objects.create(
                name=f"Custom Pattern",
                pattern_image=pattern_image,
                is_pattern=True,
                active=True
            )
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

        return JsonResponse({'status': 'success', 'color_id': color.id})

    return JsonResponse({'status': 'error'}, status=400)


@staff_member_required
def edit_mask(request, object_id):
    silhouette = get_object_or_404(ProductSilhouette, pk=object_id)

    if request.method == 'POST' and request.FILES.get('mask_image'):
        silhouette.mask_image = request.FILES['mask_image']
        silhouette.save()
        return redirect('admin:designer_productsilhouette_change', object_id)

    return render(request, 'admin/edit_mask.html', {
        'silhouette': silhouette,
        'opts': ProductSilhouette._meta,
    })


# views.py
class SilhouetteEditView(UpdateView):
    model = ProductSilhouette
    form_class = SilhouetteEditForm
    template_name = 'admin/silhouette_editor.html'
    success_url = reverse_lazy('admin:designer_productsilhouette_changelist')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # For new objects, get template_id from GET parameter
        if not self.object:
            template_id = self.request.GET.get('template_id')
            if template_id:
                kwargs['template_id'] = template_id
        else:
            kwargs['template_id'] = self.object.template_id
        return kwargs

    def get_object(self, queryset=None):
        # Для новых объектов
        if 'pk' not in self.kwargs:
            return None
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("Debug: Object in view:", self.object)

        return context

    def form_valid(self, form):
        colored_areas = self.request.POST.get('colored_areas', '[]')
        try:
            form.instance.colored_areas = json.loads(colored_areas)
        except json.JSONDecodeError:
            form.instance.colored_areas = []

        if 'mask_image' in self.request.FILES:
            form.instance.mask_image = self.request.FILES['mask_image']

        # If this is a new object, set the template relationship
        if not form.instance.pk and 'template_id' in self.request.GET:
            form.instance.template_id = self.request.GET['template_id']

        # If a base image is selected, use it as the mask
        base_image = form.cleaned_data.get('base_image')
        if base_image and not form.cleaned_data.get('mask_image'):
            form.instance.mask_image = base_image.image
            # Mark the image as silhouette
            base_image.is_silhouette = True
            base_image.save()

        return super().form_valid(form)

