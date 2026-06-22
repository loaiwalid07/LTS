from django.contrib.auth import login
from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import LoginForm, RegisterForm


class LoginView(BaseLoginView):
    """Handles user login with custom styled form."""

    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class RegisterView(CreateView):
    """Handles user registration."""

    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class ProfileView(DetailView):
    """Display the authenticated user's profile."""

    template_name = 'accounts/profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)
