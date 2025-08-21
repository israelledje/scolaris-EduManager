from django.shortcuts import render, redirect
from django import forms
from .models import School, SchoolYear, SchoolType, EducationSystem, Ministry, RegionalDelegation, DocumentHeader, SchoolLevel
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import json

class SchoolConfigForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['name', 'code', 'type', 'education_system', 'levels', 'ministry', 'regional_delegation', 
                 'authorization_number', 'creation_date', 'address', 'phone', 'email', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'code': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'type': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'education_system': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'levels': forms.SelectMultiple(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'ministry': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'regional_delegation': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'authorization_number': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'creation_date': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'address': forms.Textarea(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
            'website': forms.URLInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 py-2 px-3 mb-2 focus:ring-blue-500 focus:border-blue-500'}),
        }

@login_required
def config_school_view(request):
    # Récupérer l'étape actuelle depuis la session ou par défaut 1
    current_step = request.session.get('config_step', 1)
    
    # Récupérer les données système
    education_systems = list(EducationSystem.objects.all())
    school_types = list(SchoolType.objects.all())
    ministries = list(Ministry.objects.all())
    regional_delegations = list(RegionalDelegation.objects.all())
    
    # Récupérer l'établissement existant
    school = School.objects.first()
    school_exists = school is not None
    
    if request.method == 'POST':
        if 'next_step' in request.POST:
            # Traitement de l'étape actuelle
            if current_step == 1:
                # Étape 1: Configuration du système
                try:
                    # Créer les systèmes éducatifs sélectionnés
                    education_systems_selected = request.POST.getlist('education_systems')
                    for system_name in education_systems_selected:
                        if system_name == 'francophone':
                            EducationSystem.objects.get_or_create(name="Francophone", defaults={'code': 'FR'})
                        elif system_name == 'anglophone':
                            EducationSystem.objects.get_or_create(name="Anglophone", defaults={'code': 'EN'})
                    
                    # Créer les types d'établissements sélectionnés
                    school_types_selected = request.POST.getlist('school_types')
                    for type_name in school_types_selected:
                        if type_name == 'public':
                            SchoolType.objects.get_or_create(name="Public", defaults={'code': 'PUB'})
                        elif type_name == 'prive':
                            SchoolType.objects.get_or_create(name="Privé", defaults={'code': 'PRIV'})
                        elif type_name == 'confessionnel':
                            SchoolType.objects.get_or_create(name="Confessionnel", defaults={'code': 'CONF'})
                    
                    # Créer le ministère
                    ministry_name = request.POST.get('ministry_name')
                    if ministry_name:
                        ministry, created = Ministry.objects.get_or_create(
                            name=ministry_name,
                            defaults={
                                'code': request.POST.get('ministry_code', 'MIN'),
                                'address': request.POST.get('ministry_address', ''),
                                'phone': request.POST.get('ministry_phone', ''),
                                'email': request.POST.get('ministry_email', '')
                            }
                        )
                        
                        # Créer la délégation régionale
                        delegation_name = request.POST.get('delegation_name')
                        delegation_region = request.POST.get('delegation_region')
                        if delegation_name and delegation_region:
                            RegionalDelegation.objects.get_or_create(
                                name=delegation_name,
                                region=delegation_region,
                                defaults={
                                    'ministry': ministry,
                                    'address': request.POST.get('delegation_address', ''),
                                    'phone': request.POST.get('delegation_phone', ''),
                                    'email': request.POST.get('delegation_email', '')
                                }
                            )
                    
                    # Créer les niveaux scolaires sélectionnés
                    school_levels_selected = request.POST.getlist('school_levels')
                    francophone_system = EducationSystem.objects.filter(name="Francophone").first()
                    if francophone_system:
                        for i, level_name in enumerate(school_levels_selected):
                            if level_name == 'maternelle':
                                SchoolLevel.objects.get_or_create(name="Maternelle", system=francophone_system, defaults={'order': 1})
                            elif level_name == 'primaire':
                                SchoolLevel.objects.get_or_create(name="Primaire", system=francophone_system, defaults={'order': 2})
                            elif level_name == 'secondaire':
                                SchoolLevel.objects.get_or_create(name="Secondaire", system=francophone_system, defaults={'order': 3})
                    
                    messages.success(request, "Configuration du système enregistrée avec succès.")
                    request.session['config_step'] = 2
                    current_step = 2
                    
                except Exception as e:
                    messages.error(request, f"Erreur lors de la configuration du système : {str(e)}")
                    return render(request, 'school/config_school.html', context)
                
            elif current_step == 2:
                # Étape 2: Configuration de l'établissement
                if 'name' in request.POST:
                    # Créer ou mettre à jour l'établissement
                    school_data = {
                        'name': request.POST.get('name'),
                        'code': request.POST.get('code'),
                        'type': SchoolType.objects.get(id=request.POST.get('type')),
                        'education_system': EducationSystem.objects.get(id=request.POST.get('education_system')),
                        'ministry': Ministry.objects.get(id=request.POST.get('ministry')),
                        'regional_delegation': RegionalDelegation.objects.get(id=request.POST.get('regional_delegation')),
                        'authorization_number': request.POST.get('authorization_number'),
                        'creation_date': request.POST.get('creation_date'),
                        'address': request.POST.get('address'),
                        'phone': request.POST.get('phone'),
                        'email': request.POST.get('email'),
                        'website': request.POST.get('website'),
                    }
                    
                    if school_exists:
                        # Mettre à jour l'établissement existant
                        for field, value in school_data.items():
                            setattr(school, field, value)
                        school.save()
                    else:
                        # Créer un nouvel établissement
                        school = School.objects.create(**school_data)
                    
                    # Gérer les niveaux
                    level_ids = request.POST.getlist('levels')
                    if level_ids:
                        levels = SchoolLevel.objects.filter(id__in=level_ids)
                        school.levels.set(levels)
                    
                    messages.success(request, "Établissement configuré avec succès.")
                    request.session['config_step'] = 3
                    current_step = 3
                    
            elif current_step == 3:
                # Étape 3: Configuration de l'en-tête
                if 'header_name' in request.POST:
                    header = DocumentHeader.objects.create(
                        name=request.POST.get('header_name'),
                        school_name=request.POST.get('school_name', ''),
                        school_motto=request.POST.get('school_motto', ''),
                        school_address=request.POST.get('school_address', ''),
                        school_phone=request.POST.get('school_phone', ''),
                        school_email=request.POST.get('school_email', ''),
                        school_website=request.POST.get('school_website', ''),
                        director_name=request.POST.get('director_name', ''),
                        director_title=request.POST.get('director_title', ''),
                        is_default=True
                    )
                    messages.success(request, "En-tête configuré avec succès.")
                    request.session['config_step'] = 4
                    current_step = 4
                    
            elif current_step == 4:
                # Étape 4: Configuration de l'année scolaire
                if 'annee' in request.POST:
                    annee = request.POST.get('annee')
                    statut = request.POST.get('statut', 'EN_COURS')
                    if annee:
                        if not SchoolYear.objects.filter(annee=annee).exists():
                            SchoolYear.objects.create(annee=annee, statut=statut)
                            messages.success(request, "Configuration terminée avec succès !")
                            
                            # Vérifier si l'établissement existe déjà
                            if school_exists:
                                # Si l'établissement existe, rediriger vers le dashboard
                                request.session['config_step'] = 1  # Réinitialiser l'étape
                                return redirect('dashboard:dashboard')  # Redirection vers le dashboard
                            else:
                                # Si c'est un nouvel établissement, rester sur la page de configuration
                                request.session['config_step'] = 1
                                current_step = 1
                        else:
                            messages.error(request, "Cette année scolaire existe déjà.")
                    else:
                        messages.error(request, "Veuillez renseigner l'année scolaire.")
                        
        elif 'prev_step' in request.POST:
            # Revenir à l'étape précédente
            if current_step > 1:
                request.session['config_step'] = current_step - 1
                current_step = current_step - 1
    
    # Préparer le contexte selon l'étape
    context = {
        'current_step': current_step,
        'school': school,
        'school_exists': school_exists,
        'education_systems': education_systems,
        'school_types': school_types,
        'ministries': ministries,
        'regional_delegations': regional_delegations,
        'total_steps': 4,
    }
    
    return render(request, 'school/config_school.html', context)

@login_required
def init_system_view(request):
    """Vue pour afficher la page d'initialisation du système"""
    return render(request, 'school/init_system.html')

def init_system_data(request):
    """Vue pour initialiser les données système par défaut"""
    try:
        # Créer le système éducatif francophone
        francophone, created = EducationSystem.objects.get_or_create(
            name="Francophone",
            defaults={'code': 'FR'}
        )
        
        # Créer le système éducatif anglophone
        anglophone, created = EducationSystem.objects.get_or_create(
            name="Anglophone",
            defaults={'code': 'EN'}
        )
        
        # Créer les TYPES d'établissements (Public, Privé, Confessionnel)
        public, created = SchoolType.objects.get_or_create(
            name="Public",
            defaults={'code': 'PUB'}
        )
        
        prive, created = SchoolType.objects.get_or_create(
            name="Privé",
            defaults={'code': 'PRIV'}
        )
        
        confessionnel, created = SchoolType.objects.get_or_create(
            name="Confessionnel",
            defaults={'code': 'CONF'}
        )
        
        # Créer le ministère de l'éducation
        ministere, created = Ministry.objects.get_or_create(
            name="Ministère de l'Éducation de Base",
            defaults={
                'code': 'MINEDUB',
                'address': 'Yaoundé, Cameroun',
                'phone': '+237 XXX XXX XXX',
                'email': 'contact@minedub.cm'
            }
        )
        
        # Créer la délégation régionale
        delegation, created = RegionalDelegation.objects.get_or_create(
            name="Délégation Régionale de l'Éducation",
            region="Centre",
            defaults={
                'ministry': ministere,
                'address': 'Yaoundé, Région du Centre',
                'phone': '+237 XXX XXX XXX',
                'email': 'delegation.centre@minedub.cm'
            }
        )
        
        # Créer les NIVEAUX scolaires (Maternelle, Primaire, Secondaire)
        niveaux = [
            ("Maternelle", 1),
            ("Primaire", 2),
            ("Secondaire", 3),
        ]
        
        for nom, ordre in niveaux:
            SchoolLevel.objects.get_or_create(
                name=nom,
                system=francophone,
                defaults={'order': ordre}
            )
        
        messages.success(request, "Données système initialisées avec succès !")
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'initialisation : {str(e)}")
    
    return redirect('school:config_school')
