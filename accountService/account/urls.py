from django.urls import path
from .views import AccountListView, AccountDetailView, AccountCreateView, TopUpAccountView

urlpatterns = [
    path('accounts/', AccountListView.as_view(), name='account_list'),
    path('accounts/<uuid:account_id>/', AccountDetailView.as_view(), name='account_detail'),
    path('accounts/create/', AccountCreateView.as_view(), name='account_create'),
    path('accounts/top-up/', TopUpAccountView.as_view(), name='account_top_up'),
]