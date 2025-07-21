from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (
    CustomProductTemplate, UserCustomDesign,
    CustomDesignElement, CustomProductColor,
    CustomDesignArea, CustomProductOrder
)
import uuid
import logging


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

    # Создаём контекст, как в `custom_designer_edit`
    areas = template.design_areas.all()
    colors = CustomProductColor.objects.filter(active=True)
    sizes = template.get_available_sizes()
    front_image = template.images.filter(is_front=True).first()
    back_image = template.images.filter(is_back=True).first()

    context = {
        'design': user_design,  # Используем созданный user_design
        'template': template,
        'areas': areas,
        'colors': colors,
        'sizes': sizes,
        'front_image': front_image,
        'back_image': back_image,
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