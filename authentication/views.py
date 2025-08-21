from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django import forms
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from school.models import School
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from .models import User

# Create your views here.

class LoginForm(forms.Form):
    username = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={
            'placeholder': _("Nom d'utilisateur ou adresse email"),
            'class': 'mt-1 block w-full rounded-lg border border-gray-300 bg-white/80 py-2 px-3 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label="",
        widget=forms.PasswordInput(attrs={
            'placeholder': _("Votre mot de passe"),
            'class': 'mt-1 block w-full rounded-lg border border-gray-300 bg-white/80 py-2 px-3 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm',
            'autocomplete': 'current-password',
        })
    )

def login_view(request):
    # Utiliser le logo statique
    from django.conf import settings
    from django.templatetags.static import static
    
    school_logo = static('images/logo.png')
    school_name = "Scolaris"
    
    try:
        # Récupérer le nom de l'école s'il existe
        school = School.objects.first()
        if school:
            school_name = school.name
    except:
        pass
    
    # Détecter la langue de la session ou utiliser le français par défaut
    language = request.session.get('django_language', 'fr')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Essayer de s'authentifier avec le nom d'utilisateur ou l'email
            user = None
            
            # D'abord, essayer avec le nom d'utilisateur
            user = authenticate(request, username=username_or_email, password=password)
            
            # Si ça ne marche pas, essayer avec l'email
            if user is None:
                try:
                    # Chercher l'utilisateur par email
                    user_obj = User.objects.get(email=username_or_email)
                    # Authentifier avec le nom d'utilisateur trouvé
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None:
                login(request, user)
                # Redirection selon l'existence de l'établissement
                if not School.objects.exists():
                    return redirect('school:config_school')
                return redirect(reverse('dashboard:dashboard'))
            else:
                messages.error(request, _("Nom d'utilisateur/email ou mot de passe incorrect."))
    else:
        form = LoginForm()
    
    context = {
        'form': form,
        'school_logo': school_logo,
        'school_name': school_name,
    }
    return render(request, 'authentication/login.html', context)

# Mixin pour vérifier le rôle
class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = []
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in self.allowed_roles
    def handle_no_permission(self):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette page.")

# Liste des utilisateurs (ADMIN/DIRECTION)
class UserListView(RoleRequiredMixin, LoginRequiredMixin, ListView):
    model = User
    template_name = 'authentication/user_list.html'
    context_object_name = 'users'
    allowed_roles = [User.Role.ADMIN, User.Role.DIRECTION]

# Détail d'un utilisateur (ADMIN/DIRECTION)
class UserDetailView(RoleRequiredMixin, LoginRequiredMixin, DetailView):
    model = User
    template_name = 'authentication/user_detail.html'
    context_object_name = 'user_obj'
    allowed_roles = [User.Role.ADMIN, User.Role.DIRECTION]

# Création d'utilisateur (ADMIN uniquement)
class UserCreateView(RoleRequiredMixin, LoginRequiredMixin, CreateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email', 'role', 'password']
    template_name = 'authentication/user_form.html'
    success_url = reverse_lazy('authentication:user_list')
    allowed_roles = [User.Role.ADMIN]
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        return super().form_valid(form)

# Modification d'utilisateur (ADMIN/DIRECTION)
class UserUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email', 'role']
    template_name = 'authentication/user_form.html'
    success_url = reverse_lazy('authentication:user_list')
    allowed_roles = [User.Role.ADMIN, User.Role.DIRECTION]

# Suppression d'utilisateur (ADMIN uniquement)
class UserDeleteView(RoleRequiredMixin, LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'authentication/user_confirm_delete.html'
    success_url = reverse_lazy('authentication:user_list')
    allowed_roles = [User.Role.ADMIN]

# Changement de rôle (ADMIN uniquement)
class UserRoleUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    model = User
    fields = ['role']
    template_name = 'authentication/user_role_form.html'
    success_url = reverse_lazy('authentication:user_list')
    allowed_roles = [User.Role.ADMIN]

# Décorateur pour FBV (exemple)
def is_admin_or_direction(user):
    return user.is_authenticated and user.role in [User.Role.ADMIN, User.Role.DIRECTION]

@login_required
@user_passes_test(is_admin_or_direction)
def user_list_view(request):
    users = User.objects.all()
    return render(request, 'authentication/user_list.html', {'users': users})
