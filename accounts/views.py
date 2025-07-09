from django.shortcuts import render,redirect
from django.views.generic import FormView
from .forms import UserRegistationForm,UserUpdateForm
from django.contrib.auth import login,logout
from django.contrib.auth.views import LoginView,LogoutView
from django.views import View
from django.urls import reverse_lazy

# Create your views here.


class UserRegistrationView(FormView):
    
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistationForm
    success_url = reverse_lazy("profile")


    def form_valid(self, form):
        # print(form.cleaned_data)
        user = form.save()
        login(self.request, user)
        # print(user)
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'

    def get_success_url(self):
        return reverse_lazy("homepage")


# class UserLogoutView(LogoutView):
#     def get_success_url(self):
#         return reverse_lazy('homepage')

def User_logout(request):
    logout(request)
    return redirect("homepage")


class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(data=request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})
    
    