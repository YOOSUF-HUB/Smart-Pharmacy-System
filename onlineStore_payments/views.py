from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import Cart, Order, OrderItem

import stripe
from django.conf import settings
from django.http import JsonResponse
import json

# Customer required
def customer_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "customer")(view_func)


