# middleware.py
from django.http import HttpResponseForbidden

import logging
from django.contrib.auth import logout
from django.shortcuts import redirect
from main.models import Cart
from django.urls import reverse
logger = logging.getLogger('cart')




class CartSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Создаем сессию, если ее нет
        if not request.session.session_key:
            request.session.create()
            logger.debug(f"Created new session: {request.session.session_key}")

        response = self.get_response(request)

        # После обработки запроса проверяем авторизацию
        if request.user.is_authenticated and 'cart_session_key' in request.session:
            try:
                session_key = request.session['cart_session_key']
                session_cart = Cart.objects.filter(session_key=session_key).first()
                user_cart, created = Cart.objects.get_or_create(user=request.user)

                if session_cart:
                    logger.debug(f"Merging carts - session: {session_cart.id}, user: {user_cart.id}")
                    # Переносим товары из сессионной корзины в пользовательскую
                    for item in session_cart.items.all():
                        existing_item = user_cart.items.filter(
                            xml_product=item.xml_product,
                            size=item.size
                        ).first()

                        if existing_item:
                            existing_item.quantity += item.quantity
                            existing_item.save()
                            logger.debug(f"Merged item {item.id}, new quantity: {existing_item.quantity}")
                        else:
                            item.cart = user_cart
                            item.pk = None
                            item.save()
                            logger.debug(f"Added new item {item.id} to user cart")

                    # Удаляем сессионную корзину
                    session_cart.delete()
                    logger.debug("Deleted session cart after merge")

                    # Удаляем ключ сессии
                    del request.session['cart_session_key']
                    logger.debug("Removed cart_session_key from session")

                    # Редиректим обратно в корзину
                    if request.path != reverse('main:cart_view'):
                        return redirect('main:cart_view')

            except Exception as e:
                logger.error(f"Error merging carts: {str(e)}")

        return response