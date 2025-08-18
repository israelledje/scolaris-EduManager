#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Service de notification pour les bulletins
"""

import logging
from typing import Dict, List
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import requests
import json

logger = logging.getLogger(__name__)

class BulletinNotificationService:
    """Service de notification pour les bulletins"""
    
    def __init__(self):
        # Configuration SMS depuis config.py ou settings.py
        try:
            from config import SMS_CONFIG
            self.sms_user = SMS_CONFIG.get('USER', 'user')
            self.sms_password = SMS_CONFIG.get('PASSWORD', 'password')
            self.sms_sender_id = SMS_CONFIG.get('SENDER_ID', 'SCOLARIS')
        except ImportError:
            # Fallback vers settings.py
            self.sms_user = getattr(settings, 'SMS_USER', 'user')
            self.sms_password = getattr(settings, 'SMS_PASSWORD', 'password')
            self.sms_sender_id = getattr(settings, 'SMS_SENDER_ID', 'SCOLARIS')
        
        # Vérifier si les notifications sont activées
        try:
            from config import NOTIFICATIONS_CONFIG
            self.notifications_enabled = NOTIFICATIONS_CONFIG.get('ENABLED', True)
            self.sms_enabled = NOTIFICATIONS_CONFIG.get('SMS_ENABLED', True)
            self.email_enabled = NOTIFICATIONS_CONFIG.get('EMAIL_ENABLED', True)
        except ImportError:
            self.notifications_enabled = getattr(settings, 'NOTIFICATIONS_ENABLED', True)
            self.sms_enabled = getattr(settings, 'SMS_ENABLED', True)
            self.email_enabled = getattr(settings, 'EMAIL_ENABLED', True)
        
        # URL de l'API SMSVAS
        self.sms_api_url = "https://smsvas.com/bulk/public/index.php/api/v1/sendsms"
    
    def send_bulletin_notifications(self, bulletin_data: Dict) -> Dict[str, bool]:
        """
        Envoie les notifications de bulletin aux parents
        
        Args:
            bulletin_data: Dictionnaire contenant les informations du bulletin
            
        Returns:
            Dict avec le statut d'envoi pour email et SMS
        """
        try:
            results = {
                'email_sent': False,
                'sms_sent': False,
                'errors': []
            }
            
            # Récupérer les informations de l'étudiant et des parents
            student = bulletin_data['student']
            trimester = bulletin_data['trimester']
            
            # Récupérer les parents/tuteurs
            guardians = student.guardians.all()
            if not guardians.exists():
                logger.warning(f"Aucun parent/tuteur trouvé pour l'élève {student}")
                return results
            
            # Préparer les données de notification
            notification_data = {
                'student_name': f"{student.last_name} {student.first_name}",
                'student_matricule': student.matricule,
                'class_name': student.current_class.name if student.current_class else "Non assigné",
                'trimester_name': trimester.get_trimester_display(),
                'school_year': trimester.year.annee,
                'student_average': round(bulletin_data['moyenne_generale'], 2),
                'class_average': round(bulletin_data['class_average'], 2),
                'student_rank': bulletin_data['rank'],
                'class_size': bulletin_data['class_size'],
                'subjects_count': len(bulletin_data['subject_averages']),
                'trimester_date': trimester.end_date.strftime('%d/%m/%Y') if trimester.end_date else "N/A"
            }
            
            # Envoyer les notifications à chaque parent/tuteur
            for guardian in guardians:
                try:
                    # Envoyer l'email
                    if self.email_enabled and guardian.email:
                        email_sent = self._send_bulletin_email(guardian, notification_data)
                        results['email_sent'] = results['email_sent'] or email_sent
                    
                    # Envoyer le SMS
                    if self.sms_enabled and guardian.phone:
                        sms_sent = self._send_bulletin_sms(guardian, notification_data)
                        results['sms_sent'] = results['sms_sent'] or sms_sent
                        
                except Exception as e:
                    error_msg = f"Erreur notification pour {guardian.relation} de {student}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Notifications de bulletin envoyées pour {student}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur générale dans le service de notification de bulletin: {e}")
            return {
                'email_sent': False,
                'sms_sent': False,
                'errors': [f"Erreur générale: {str(e)}"]
            }
    
    def _send_bulletin_email(self, guardian, notification_data: Dict) -> bool:
        """Envoie l'email de notification de bulletin"""
        try:
            subject = f"Bulletin {notification_data['trimester_name']} - {notification_data['student_name']}"
            
            # Rendu du template email
            html_message = render_to_string('notes/emails/bulletin_notification.html', {
                'guardian': guardian,
                'data': notification_data
            })
            
            text_message = render_to_string('notes/emails/bulletin_notification.txt', {
                'guardian': guardian,
                'data': notification_data
            })
            
            # Envoi de l'email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[guardian.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email de bulletin envoyé à {guardian.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bulletin: {e}")
            return False
    
    def _send_bulletin_sms(self, guardian, notification_data: Dict) -> bool:
        """Envoie le SMS de notification de bulletin"""
        try:
            # Créer le message SMS
            message = self._create_bulletin_sms_message(notification_data)
            
            # Formater le numéro de téléphone
            phone = self._format_phone_number(guardian.phone)
            
            # Préparer le payload pour l'API SMSVAS
            payload = {
                "user": self.sms_user,
                "password": self.sms_password,
                "senderid": self.sms_sender_id,
                "sms": message,
                "mobiles": phone,
                "scheduletime": ""  # Envoi immédiat
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Envoi de la requête SMS
            response = requests.post(
                self.sms_api_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('responsecode') == 1:
                    logger.info(f"SMS de bulletin envoyé avec succès. Message ID: {response_data.get('sms', [{}])[0].get('messageid', 'N/A')}")
                    return True
                else:
                    logger.error(f"Erreur API SMS pour bulletin: {response_data.get('responsemessage', 'Erreur inconnue')}")
                    return False
            else:
                logger.error(f"Erreur HTTP lors de l'envoi du SMS de bulletin: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion lors de l'envoi du SMS de bulletin: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'envoi du SMS de bulletin: {e}")
            return False
    
    def _create_bulletin_sms_message(self, notification_data: Dict) -> str:
        """Crée le message SMS pour la notification de bulletin"""
        student_name = notification_data['student_name']
        trimester_name = notification_data['trimester_name']
        student_average = notification_data['student_average']
        class_average = notification_data['class_average']
        rank = notification_data['student_rank']
        class_size = notification_data['class_size']
        
        message = f"Bulletin {trimester_name} - {student_name}. "
        message += f"Moyenne: {student_average}/20. "
        message += f"Classe: {class_average}/20. "
        message += f"Rang: {rank}/{class_size}. "
        message += "Consultez le bulletin complet sur SCOLARIS."
        
        return message
    
    def _format_phone_number(self, phone: str) -> str:
        """Formate le numéro de téléphone pour l'API SMS"""
        # Supprimer les espaces et caractères spéciaux
        phone = ''.join(filter(str.isdigit, phone))
        
        # Ajouter l'indicatif du pays si absent
        if not phone.startswith('237'):
            if phone.startswith('0'):
                phone = '237' + phone[1:]
            else:
                phone = '237' + phone
        
        return phone

# Instance globale du service de notification de bulletin
bulletin_notification_service = BulletinNotificationService()
