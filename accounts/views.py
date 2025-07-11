from django.shortcuts import render,redirect
from django.views.generic import FormView
from .forms import UserRegistationForm,UserUpdateForm
from django.contrib.auth import login,logout
from django.contrib.auth.views import LoginView,LogoutView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash


from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
# Create your views here.



def send_pass_change_email(user, subject, template):
    message = render_to_string(template, {
        'user': user,
    })
    send_email = EmailMultiAlternatives(subject,'',to=[user.email])

    send_email.attach_alternative(message, "text/html")
    send_email.send()



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


class account_pass_change(FormView):
    template_name = 'accounts/user_pass_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy("profile")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)

        # Send email notification
        send_pass_change_email(self.request.user,"Password Changed",'accounts/pass_change_email.html' )
        # messages.success(self.request, f"Password Updated Successfull" )
        return super().form_valid(form)
    





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
    
    