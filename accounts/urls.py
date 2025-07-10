from django.urls import path
from . views import UserRegistrationView,UserLoginView,UserBankAccountUpdateView,User_logout,account_pass_change

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name = 'register'),
    path('login/', UserLoginView.as_view(), name = 'login'),
    path('logout/', User_logout, name = 'logout'),
    path('pass_change/', account_pass_change.as_view(), name = 'pass_change'),
    path('profile/', UserBankAccountUpdateView.as_view(), name = 'profile'),
]
