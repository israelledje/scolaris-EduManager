import logging
import requests
import json
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Service de notification pour l'envoi d'emails et SMS"""
    
    def __init__(self):
        self.sms_api_url = "https://smsvas.com/bulk/public/index.php/api/v1/sendsms"
        
        # Charger la configuration depuis config.py si disponible
        try:
            from config import SMS_CONFIG, EMAIL_CONFIG
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
    
    def send_payment_notification(self, payment_data: Dict) -> Dict[str, bool]:
        """
        Envoie une notification de paiement par email et SMS
        
        Args:
            payment_data: Dictionnaire contenant les informations du paiement
            
        Returns:
            Dict avec le statut d'envoi pour email et SMS
        """
        try:
            results = {
                'email_sent': False,
                'sms_sent': False,
                'errors': []
            }
            
            # Envoyer l'email
            try:
                email_sent = self._send_payment_email(payment_data)
                results['email_sent'] = email_sent
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email: {e}")
                results['errors'].append(f"Email: {str(e)}")
            
            # Envoyer le SMS
            try:
                sms_sent = self._send_payment_sms(payment_data)
                results['sms_sent'] = sms_sent
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du SMS: {e}")
                results['errors'].append(f"SMS: {str(e)}")
            
            logger.info(f"Notifications de paiement envoyées: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur générale dans le service de notification: {e}")
            return {
                'email_sent': False,
                'sms_sent': False,
                'errors': [f"Erreur générale: {str(e)}"]
            }
    
    def send_inscription_notification(self, inscription_data: Dict) -> Dict[str, bool]:
        """
        Envoie une notification d'inscription par email et SMS
        
        Args:
            inscription_data: Dictionnaire contenant les informations de l'inscription
            
        Returns:
            Dict avec le statut d'envoi pour email et SMS
        """
        try:
            results = {
                'email_sent': False,
                'sms_sent': False,
                'errors': []
            }
            
            # Envoyer l'email
            try:
                email_sent = self._send_inscription_email(inscription_data)
                results['email_sent'] = email_sent
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email d'inscription: {e}")
                results['errors'].append(f"Email: {str(e)}")
            
            # Envoyer le SMS
            try:
                sms_sent = self._send_inscription_sms(inscription_data)
                results['sms_sent'] = sms_sent
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du SMS d'inscription: {e}")
                results['errors'].append(f"SMS: {str(e)}")
            
            logger.info(f"Notifications d'inscription envoyées: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur générale dans le service de notification d'inscription: {e}")
            return {
                'email_sent': False,
                'sms_sent': False,
                'errors': [f"Erreur générale: {str(e)}"]
            }
    
    def _send_payment_email(self, payment_data: Dict) -> bool:
        """Envoie un email de notification de paiement"""
        if not self.notifications_enabled or not self.email_enabled:
            logger.info("Notifications email désactivées")
            return False
            
        try:
            subject = f"Confirmation de paiement - {payment_data.get('student_name', 'Élève')}"
            
            # Rendre le template HTML
            html_message = render_to_string('notifications/emails/payment_confirmation.html', {
                'payment': payment_data
            })
            
            # Rendre le template texte
            text_message = render_to_string('notifications/emails/payment_confirmation.txt', {
                'payment': payment_data
            })
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[payment_data.get('guardian_email')],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email de paiement envoyé à {payment_data.get('guardian_email')}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de paiement: {e}")
            return False
    
    def _send_payment_sms(self, payment_data: Dict) -> bool:
        """Envoie un SMS de notification de paiement"""
        if not self.notifications_enabled or not self.sms_enabled:
            logger.info("Notifications SMS désactivées")
            return False
            
        try:
            guardian_phone = payment_data.get('guardian_phone')
            if not guardian_phone:
                logger.warning("Aucun numéro de téléphone du tuteur trouvé")
                return False
            
            # Formater le numéro de téléphone
            formatted_phone = self._format_phone_number(guardian_phone)
            
            # Créer le message SMS
            message = self._create_payment_sms_message(payment_data)
            
            # Envoyer le SMS
            return self._send_sms(formatted_phone, message)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du SMS de paiement: {e}")
            return False
    
    def _send_inscription_email(self, inscription_data: Dict) -> bool:
        """Envoie un email de notification d'inscription"""
        if not self.notifications_enabled or not self.email_enabled:
            logger.info("Notifications email désactivées")
            return False
            
        try:
            subject = f"Confirmation d'inscription - {inscription_data.get('student_name', 'Élève')}"
            
            # Rendre le template HTML
            html_message = render_to_string('notifications/emails/inscription_confirmation.html', {
                'inscription': inscription_data
            })
            
            # Rendre le template texte
            text_message = render_to_string('notifications/emails/inscription_confirmation.txt', {
                'inscription': inscription_data
            })
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[inscription_data.get('guardian_email')],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email d'inscription envoyé à {inscription_data.get('guardian_email')}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'inscription: {e}")
            return False
    
    def _send_inscription_sms(self, inscription_data: Dict) -> bool:
        """Envoie un SMS de notification d'inscription"""
        if not self.notifications_enabled or not self.sms_enabled:
            logger.info("Notifications SMS désactivées")
            return False
            
        try:
            guardian_phone = inscription_data.get('guardian_phone')
            if not guardian_phone:
                logger.warning("Aucun numéro de téléphone du tuteur trouvé")
                return False
            
            # Formater le numéro de téléphone
            formatted_phone = self._format_phone_number(guardian_phone)
            
            # Créer le message SMS
            message = self._create_inscription_sms_message(inscription_data)
            
            # Envoyer le SMS
            return self._send_sms(formatted_phone, message)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du SMS d'inscription: {e}")
            return False
    
    def _send_sms(self, mobile: str, message: str) -> bool:
        """Envoie un SMS via l'API SMSVAS"""
        try:
            payload = {
                "user": self.sms_user,
                "password": self.sms_password,
                "senderid": self.sms_sender_id,
                "sms": message,
                "mobiles": mobile,
                "scheduletime": ""  # Envoi immédiat
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.sms_api_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('responsecode') == 1:
                    logger.info(f"SMS envoyé avec succès. Message ID: {response_data.get('sms', [{}])[0].get('messageid', 'N/A')}")
                    return True
                else:
                    logger.error(f"Erreur API SMS: {response_data.get('responsemessage', 'Erreur inconnue')}")
                    return False
            else:
                logger.error(f"Erreur HTTP lors de l'envoi du SMS: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion lors de l'envoi du SMS: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'envoi du SMS: {e}")
            return False
    
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
    
    def _create_payment_sms_message(self, payment_data: Dict) -> str:
        """Crée le message SMS pour la notification de paiement"""
        student_name = payment_data.get('student_name', 'Élève')
        amount = payment_data.get('amount', 0)
        tranche_number = payment_data.get('tranche_number', '')
        payment_date = payment_data.get('payment_date', '')
        receipt_number = payment_data.get('receipt_number', '')
        
        message = f"Paiement confirme pour {student_name}. "
        if tranche_number:
            message += f"Tranche {tranche_number}: {amount} FCFA. "
        else:
            message += f"Montant: {amount} FCFA. "
        
        message += f"Recu: {receipt_number}. Date: {payment_date}. "
        message += "Merci pour votre confiance."
        
        return message
    
    def _create_inscription_sms_message(self, inscription_data: Dict) -> str:
        """Crée le message SMS pour la notification d'inscription"""
        student_name = inscription_data.get('student_name', 'Élève')
        amount = inscription_data.get('amount', 0)
        class_name = inscription_data.get('class_name', '')
        receipt_number = inscription_data.get('receipt_number', '')
        payment_date = inscription_data.get('payment_date', '')
        
        message = f"Inscription confirmee pour {student_name}. "
        if class_name:
            message += f"Classe: {class_name}. "
        
        message += f"Frais: {amount} FCFA. "
        message += f"Recu: {receipt_number}. Date: {payment_date}. "
        message += "Bienvenue dans notre etablissement!"
        
        return message


# Instance globale du service de notification
notification_service = NotificationService()
