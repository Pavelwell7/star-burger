from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce


from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name='products_list.html', context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name='restaurants_list.html', context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    menu_items = RestaurantMenuItem.objects.filter(
        availability=True
    ).select_related('restaurant', 'product')

    restaurant_products = {}
    for item in menu_items:
        restaurant_products.setdefault(item.restaurant, set())
        restaurant_products[item.restaurant].add(item.product_id)

    orders = Order.objects.exclude(
        status='done'
    ).prefetch_related(
        'items__product'
    ).select_related(
        'restaurant'
    ).annotate(
        total_price=Coalesce(
            Sum(F('items__quantity') * F('items__price')),
            Value(0, output_field=DecimalField())
        )
    )
    orders_with_restaurants = []
    for order in orders:
        order_products = {item.product_id for item in order.items.all()}
        available_restaurants = [
            restaurant
            for restaurant, products in restaurant_products.items()
            if order_products.issubset(products)
        ]

        orders_with_restaurants.append({
            'order': order,
            'available_restaurants': available_restaurants,
        })

    return render(request, template_name='order_items.html', context={
        'order_items': orders_with_restaurants,
    })
