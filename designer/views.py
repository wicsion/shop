import os

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from main.models import XMLProduct
from .models import (
    CustomProductTemplate, UserCustomDesign,
    CustomDesignElement, CustomProductColor,
    CustomDesignArea, CustomProductOrder, ProductSilhouette
)
import uuid
import logging
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy, reverse
from .models import ProductSilhouette
from .forms import SilhouetteEditForm
from .models import CustomProductTemplate, ProductMask
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
import json


# views.py
def custom_designer_start(request):
    logger = logging.getLogger(__name__)
    product_id = request.GET.get('product_id')

    if not product_id:
        return redirect('main:home')

    product = get_object_or_404(XMLProduct, product_id=product_id)
    template = CustomProductTemplate.objects.filter(active=True).first()

    if not template:
        return redirect('main:home')

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    # Создаем или получаем дизайн для этого товара
    user_design, created = UserCustomDesign.objects.get_or_create(
        user_session=session_key,
        product=product,
        defaults={'template': template}
    )

    colors = CustomProductColor.objects.filter(active=True)
    selected_color_id = request.session.get('selected_color_id')
    selected_color = colors.get(id=selected_color_id) if selected_color_id else colors.first()

    # Получаем размеры из параметров GET
    product_sizes = request.GET.get('sizes', '')
    if product_sizes:
        sizes = [size.strip() for size in product_sizes.split(',') if size.strip()]
        request.session['product_sizes'] = product_sizes
    else:
        sizes = template.get_available_sizes()

    areas = template.design_areas.all()
    front_image = template.images.filter(is_front=True).first()
    back_image = template.images.filter(is_back=True).first()

    context = {
        'design': user_design,
        'template': template,
        'product': product,  # Добавляем товар в контекст
        'areas': areas,
        'colors': colors,
        'sizes': sizes,
        'front_image': front_image,
        'back_image': back_image,
        'selected_color': selected_color,
    }
    return render(request, 'designer/designer.html', context)


# В функции custom_designer_edit добавим сохранение выбранного цвета
# views.py
def custom_designer_edit(request, design_id):
    design = get_object_or_404(UserCustomDesign, id=design_id)
    template = design.template
    product = design.product  # Получаем привязанный товар

    areas = template.design_areas.all()
    colors = CustomProductColor.objects.filter(active=True)

    # Получаем размеры из сессии (если они были сохранены)
    product_sizes = request.session.get('original_product_sizes', '')
    if product_sizes:
        sizes = [size.strip() for size in product_sizes.split(',') if size.strip()]
    else:
        # Если нет в сессии, используем размеры товара или шаблона
        sizes = template.get_available_sizes()

    front_image = template.images.filter(is_front=True).first()
    back_image = template.images.filter(is_back=True).first()

    # Получаем выбранный цвет из заказа
    custom_order = CustomProductOrder.objects.filter(design=design, in_cart=True).first()
    selected_color = custom_order.selected_color if custom_order else colors.first()

    if selected_color:
        request.session['selected_color_id'] = selected_color.id

    elements = design.elements.all().select_related('area')

    context = {
        'design': design,
        'product': product,  # Передаем товар в контекст
        'template': template,
        'areas': areas,
        'colors': colors,
        'sizes': sizes,
        'front_image': front_image,
        'back_image': back_image,
        'from_cart': request.GET.get('from_cart', False),
        'elements': elements,
        'selected_color': selected_color,
    }
    return render(request, 'designer/designer.html', context)

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
    template = design.template
    product = design.product  # Получаем привязанный товар
    areas = template.design_areas.all()
    colors = CustomProductColor.objects.filter(active=True)

    # Получаем размеры из параметров GET (если переход из карточки товара)
    product_sizes = request.GET.get('sizes', '')
    if product_sizes:
        sizes = [size.strip() for size in product_sizes.split(',') if size.strip()]
        # Сохраняем в сессию
        request.session['original_product_sizes'] = product_sizes
    else:
        # Если нет в GET, проверяем сессию
        product_sizes = request.session.get('original_product_sizes', '')
        if product_sizes:
            sizes = [size.strip() for size in product_sizes.split(',') if size.strip()]
        else:
            sizes = template.get_available_sizes()

    front_image = template.images.filter(is_front=True).first()
    back_image = template.images.filter(is_back=True).first()

    # Получаем выбранный цвет из сессии
    selected_color_id = request.session.get('selected_color_id')
    if selected_color_id:
        try:
            selected_color = colors.get(id=selected_color_id)
        except CustomProductColor.DoesNotExist:
            selected_color = colors.first()
    else:
        selected_color = colors.first()

    context = {
        'design': design,
        'template': template,
        'product': product,  # Добавляем товар в контекст
        'areas': areas,
        'colors': colors,
        'sizes': sizes,
        'front_image': front_image,
        'back_image': back_image,
        'selected_color': selected_color,
        'preview_mode': True,
    }
    return render(request, 'designer/designer.html', context)


# views.py
@csrf_exempt
def save_custom_design_order(request):
    if request.method == 'POST':
        try:
            design_id = request.POST.get('design_id')
            color_id = request.POST.get('color_id')
            size = request.POST.get('size')
            quantity = int(request.POST.get('quantity', 1))

            design = get_object_or_404(UserCustomDesign, id=design_id)
            color = get_object_or_404(CustomProductColor, id=color_id) if color_id else None

            # Сохраняем выбранный цвет в сессии
            request.session['selected_color_id'] = color_id

            # Рассчитываем цену с учетом цены оригинального товара
            price = design.template.base_price * quantity
            if design.product:
                price += design.product.price * quantity

            # Создаем или обновляем заказ
            order, created = CustomProductOrder.objects.update_or_create(
                design=design,
                in_cart=True,
                defaults={
                    'selected_color': color,
                    'quantity': quantity,
                    'size': size,
                    'price': price,
                    'original_product': design.product  # Используем привязанный товар
                }
            )

            # Обновляем сессию корзины
            cart = request.session.get('cart', {})
            cart[f'custom_{order.id}'] = {
                'type': 'custom',
                'id': order.id,
                'quantity': quantity,
                'product_id': design.product.product_id if design.product else None
            }
            request.session['cart'] = cart
            request.session.modified = True

            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('main:cart_view')
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


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
        rotation = request.POST.get('rotation', 0)  # Добавляем параметр поворота
        side = request.POST.get('side', 'front')
        element_id = request.POST.get('element_id')  # Для обновления существующего элемента
        area_id = request.POST.get('area_id')  # Для обновления существующей области

        design = get_object_or_404(UserCustomDesign, id=design_id)
        template = design.template

        try:
            # Если есть element_id, обновляем существующий элемент
            if element_id:
                element = CustomDesignElement.objects.get(id=element_id, design=design)
                area = element.area

                # Обновляем параметры области
                area.x_position = x_position
                area.y_position = y_position
                area.width = width
                area.height = height
                area.save()

                # Обновляем параметры элемента
                if request.FILES.get('image'):
                    element.image = request.FILES['image']
                if text_content:
                    element.text_content = text_content
                    element.color = color
                    element.font_size = font_size

                element.rotation = rotation  # Сохраняем поворот
                element.side = side
                element.save()
            else:
                # Создаем новую область и элемент
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
                        rotation=rotation,
                        side=side
                    )
                elif text_content:
                    element = CustomDesignElement.objects.create(
                        design=design,
                        area=area,
                        text_content=text_content,
                        color=color,
                        font_size=font_size,
                        rotation=rotation,
                        side=side
                    )
                else:
                    return JsonResponse({'status': 'error', 'message': 'No content provided'}, status=400)

            return JsonResponse({
                'status': 'success',
                'element_id': element.id,
                'area_id': area.id,
                'image_url': element.image.url if element.image else '',
                'rotation': element.rotation,
                'width': area.width,
                'height': area.height
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

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


def get_custom_items_in_cart(request):
    cart = request.session.get('cart', {})
    custom_items = []

    for key, item in cart.items():
        if item.get('type') == 'custom':
            try:
                custom_order = CustomProductOrder.objects.get(id=item['id'], in_cart=True)

                # Add information about the original product if it exists
                if custom_order.original_product:
                    custom_order.original_product_info = {
                        'name': custom_order.original_product.name,
                        'price': custom_order.original_product.price,
                        'image': custom_order.original_product.main_image,
                        'product_id': custom_order.original_product.product_id,
                        'url': custom_order.original_product.get_absolute_url()
                    }
                else:
                    # If there's no original product, create empty info
                    custom_order.original_product_info = None

                custom_items.append(custom_order)
            except CustomProductOrder.DoesNotExist:
                del cart[key]

    request.session['cart'] = cart
    request.session.modified = True
    return custom_items


@csrf_exempt
def update_custom_item(request, item_id):
    if request.method == 'POST':
        quantity = request.POST.get('quantity', 1)

        try:
            item = CustomProductOrder.objects.get(id=item_id, in_cart=True)
            item.quantity = quantity
            item.price = item.design.template.base_price * int(quantity)
            item.save()

            # Обновляем сессию корзины
            cart = request.session.get('cart', {})
            for key, cart_item in cart.items():
                if cart_item.get('type') == 'custom' and cart_item.get('id') == item_id:
                    cart_item['quantity'] = quantity
                    break
            request.session['cart'] = cart
            request.session.modified = True

            return redirect('main:cart_view')
        except CustomProductOrder.DoesNotExist:
            pass

    return redirect('main:cart_view')


@csrf_exempt
def remove_custom_item(request, item_id):
    if request.method == 'POST':
        try:
            item = CustomProductOrder.objects.get(id=item_id, in_cart=True)
            item.in_cart = False
            item.save()

            # Удаляем из сессии корзины
            cart = request.session.get('cart', {})
            for key in list(cart.keys()):
                if cart[key].get('type') == 'custom' and cart[key].get('id') == item_id:
                    del cart[key]
                    break
            request.session['cart'] = cart
            request.session.modified = True

            return redirect('main:cart_view')
        except CustomProductOrder.DoesNotExist:
            pass

    return redirect('main:cart_view')




