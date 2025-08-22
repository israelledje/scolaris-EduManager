from django.db import transaction
from django.core.exceptions import ValidationError
from .models import MatriculeSequence, SchoolYear
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MatriculeService:
    """
    Service pour gérer la génération automatique des matricules
    """
    
    @staticmethod
    def get_or_create_sequence(sequence_type):
        """
        Récupère ou crée une séquence pour un type donné
        
        Args:
            sequence_type (str): Type de séquence (STUDENT, TEACHER)
            
        Returns:
            MatriculeSequence: La séquence correspondante
        """
        # Récupérer l'année scolaire active
        current_year_obj = SchoolYear.objects.filter(statut='EN_COURS').first()
        if not current_year_obj:
            raise ValidationError("Aucune année scolaire active trouvée")
        # Extraire l'année de début depuis le format "2024-2025"
        year = int(current_year_obj.annee.split('-')[0])
        
        sequence, created = MatriculeSequence.objects.get_or_create(
            sequence_type=sequence_type,
            defaults={
                'prefix': MatriculeService._get_default_prefix(sequence_type),
                'format_pattern': MatriculeService._get_default_format(sequence_type),
                'current_year': year,
                'last_number': 0,
                'auto_generation': True
            }
        )
        
        if created:
            logger.info(f"Nouvelle séquence créée: {sequence}")
        
        return sequence
    
    @staticmethod
    def generate_matricule(sequence_type):
        """
        Génère un nouveau matricule pour le type spécifié si la génération automatique est activée
        
        Args:
            sequence_type (str): Type de séquence (STUDENT, TEACHER)
            
        Returns:
            str: Le matricule généré ou None si la génération automatique est désactivée
        """
        try:
            sequence = MatriculeSequence.objects.get(sequence_type=sequence_type)
            if not sequence.auto_generation:
                return None
                
            with transaction.atomic():
                matricule = sequence.generate_matricule()
                logger.info(f"Matricule généré: {matricule} pour {sequence_type}")
                return matricule
        except MatriculeSequence.DoesNotExist:
            # Créer la séquence par défaut
            with transaction.atomic():
                sequence = MatriculeService.get_or_create_sequence(sequence_type)
                matricule = sequence.generate_matricule()
                logger.info(f"Matricule généré: {matricule} pour {sequence_type}")
                return matricule
    
    @staticmethod
    def validate_matricule_uniqueness(matricule, model_class, exclude_id=None):
        """
        Valide l'unicité d'un matricule
        
        Args:
            matricule (str): Le matricule à valider
            model_class: La classe du modèle (Student, Teacher, etc.)
            exclude_id (int, optional): ID à exclure de la vérification (pour les mises à jour)
            
        Raises:
            ValidationError: Si le matricule existe déjà
        """
        queryset = model_class.objects.filter(matricule=matricule)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if queryset.exists():
            raise ValidationError(f"Le matricule '{matricule}' existe déjà")
    
    @staticmethod
    def _get_default_prefix(sequence_type):
        """Retourne le préfixe par défaut selon le type"""
        prefixes = {
            'STUDENT': 'STU',
            'TEACHER': 'TCH',
            'CLASS': 'CLS'
        }
        return prefixes.get(sequence_type, 'GEN')
    
    @staticmethod
    def _get_default_format(sequence_type):
        """Retourne le format par défaut selon le type"""
        formats = {
            'STUDENT': '{prefix}{year}{number:04d}',
            'TEACHER': '{prefix}{year}{number:03d}',
            'CLASS': '{prefix}{year}{number:02d}'
        }
        return formats.get(sequence_type, '{prefix}{year}{number:04d}')
    
    @staticmethod
    def reset_sequence(sequence_type, year):
        """
        Remet à zéro une séquence (utile pour une nouvelle année scolaire)
        
        Args:
            sequence_type (str): Type de séquence
            year (int): Année de la séquence
        """
        try:
            sequence = MatriculeSequence.objects.get(
                sequence_type=sequence_type,
                current_year=year
            )
            sequence.last_number = 0
            sequence.save()
            logger.info(f"Séquence {sequence_type} pour {year} remise à zéro")
        except MatriculeSequence.DoesNotExist:
            logger.warning(f"Séquence {sequence_type} pour {year} non trouvée")
    
    @staticmethod
    def get_sequence_info(sequence_type, year=None):
        """
        Retourne les informations sur une séquence
        
        Args:
            sequence_type (str): Type de séquence
            year (int, optional): Année
            
        Returns:
            dict: Informations sur la séquence
        """
        if year is None:
            current_year_obj = SchoolYear.objects.filter(statut='EN_COURS').first()
            if current_year_obj:
                # Extraire l'année de début depuis le format "2024-2025"
                year = int(current_year_obj.annee.split('-')[0])
        
        try:
            sequence = MatriculeSequence.objects.get(
                sequence_type=sequence_type,
                current_year=year
            )
            return {
                'prefix': sequence.prefix,
                'current_year': sequence.current_year,
                'last_number': sequence.last_number,
                'format_pattern': sequence.format_pattern,
                'is_active': sequence.is_active,
                'next_matricule': sequence.generate_matricule()
            }
        except MatriculeSequence.DoesNotExist:
            return None
