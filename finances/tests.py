from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum

from .models import (
    FeeStructure, FeeTranche, TranchePayment, FeeDiscount, 
    Moratorium, PaymentRefund, ExtraFee
)
from school.models import School, SchoolYear
from classes.models import SchoolClass, SchoolLevel, EducationSystem
from students.models import Student

User = get_user_model()

class FinancesTestCase(TestCase):
    """Classe de base pour les tests de finances"""
    
    def setUp(self):
        """Configuration initiale pour tous les tests"""
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            role=User.Role.ADMIN
        )
        
        # Créer une école
        self.school = School.objects.create(
            nom="École Test",
            date_creation=date(2020, 1, 1),
            autorisation_ouverture="AUT-2020-001",
            type_etablissement="SECONDAIRE"
        )
        
        # Créer une année scolaire
        self.year = SchoolYear.objects.create(
            annee="2024-2025",
            statut="EN_COURS"
        )
        
        # Créer un système éducatif et niveau
        self.system = EducationSystem.objects.create(name="Francophone")
        self.level = SchoolLevel.objects.create(
            name="Secondaire",
            system=self.system
        )
        
        # Créer une classe
        self.school_class = SchoolClass.objects.create(
            name="6ème A",
            level=self.level,
            year=self.year,
            school=self.school,
            capacity=40
        )
        
        # Créer un étudiant
        self.student = Student.objects.create(
            matricule="STU001",
            first_name="Jean",
            last_name="Dupont",
            birth_date=date(2010, 5, 15),
            birth_place="Yaoundé",
            gender="M",
            current_class=self.school_class,
            year=self.year,
            school=self.school
        )
        
        # Créer une structure de frais
        self.fee_structure = FeeStructure.objects.create(
            school_class=self.school_class,
            year=self.year,
            inscription_fee=Decimal('50000'),
            tuition_total=Decimal('300000'),
            tranche_count=3
        )
        
        # Créer des tranches
        self.tranche1 = FeeTranche.objects.create(
            fee_structure=self.fee_structure,
            number=1,
            amount=Decimal('100000'),
            due_date=date(2024, 10, 15)
        )
        
        self.tranche2 = FeeTranche.objects.create(
            fee_structure=self.fee_structure,
            number=2,
            amount=Decimal('100000'),
            due_date=date(2024, 12, 15)
        )
        
        self.tranche3 = FeeTranche.objects.create(
            fee_structure=self.fee_structure,
            number=3,
            amount=Decimal('100000'),
            due_date=date(2025, 2, 15)
        )
        
        # Client de test
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

class FeeStructureTests(FinancesTestCase):
    """Tests pour les structures de frais"""
    
    def test_fee_structure_creation(self):
        """Test de création d'une structure de frais"""
        self.assertEqual(self.fee_structure.school_class, self.school_class)
        self.assertEqual(self.fee_structure.year, self.year)
        self.assertEqual(self.fee_structure.inscription_fee, Decimal('50000'))
        self.assertEqual(self.fee_structure.tuition_total, Decimal('300000'))
        self.assertEqual(self.fee_structure.tranche_count, 3)
    
    def test_fee_structure_str(self):
        """Test de la méthode __str__"""
        expected = f"{self.school_class} - {self.year}"
        self.assertEqual(str(self.fee_structure), expected)
    
    def test_fee_structure_list_view(self):
        """Test de la vue liste des structures de frais"""
        response = self.client.get(reverse('finances:fee_structure_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Structures de Frais")
    
    def test_fee_structure_create_view(self):
        """Test de la vue création de structure de frais"""
        response = self.client.get(reverse('finances:fee_structure_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Créer une structure de frais")
    
    def test_fee_structure_detail_view(self):
        """Test de la vue détail de structure de frais"""
        response = self.client.get(reverse('finances:fee_structure_detail', args=[self.fee_structure.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.school_class.name)

class FeeTrancheTests(FinancesTestCase):
    """Tests pour les tranches de paiement"""
    
    def test_tranche_creation(self):
        """Test de création d'une tranche"""
        self.assertEqual(self.tranche1.fee_structure, self.fee_structure)
        self.assertEqual(self.tranche1.number, 1)
        self.assertEqual(self.tranche1.amount, Decimal('100000'))
        self.assertEqual(self.tranche1.due_date, date(2024, 10, 15))
    
    def test_tranche_str(self):
        """Test de la méthode __str__"""
        expected = f"Tranche 1 - {self.fee_structure}"
        self.assertEqual(str(self.tranche1), expected)
    
    def test_tranche_ordering(self):
        """Test de l'ordre des tranches"""
        tranches = FeeTranche.objects.filter(fee_structure=self.fee_structure)
        self.assertEqual(tranches[0].number, 1)
        self.assertEqual(tranches[1].number, 2)
        self.assertEqual(tranches[2].number, 3)

class TranchePaymentTests(FinancesTestCase):
    """Tests pour les paiements de tranches"""
    
    def setUp(self):
        super().setUp()
        self.payment = TranchePayment.objects.create(
            student=self.student,
            tranche=self.tranche1,
            amount=Decimal('100000'),
            mode='cash',
            receipt='REC-20241201-001',
            created_by=self.user
        )
    
    def test_payment_creation(self):
        """Test de création d'un paiement"""
        self.assertEqual(self.payment.student, self.student)
        self.assertEqual(self.payment.tranche, self.tranche1)
        self.assertEqual(self.payment.amount, Decimal('100000'))
        self.assertEqual(self.payment.mode, 'cash')
        self.assertEqual(self.payment.receipt, 'REC-20241201-001')
        self.assertEqual(self.payment.created_by, self.user)
    
    def test_payment_str(self):
        """Test de la méthode __str__"""
        expected = f"{self.student} - {self.tranche1} (100000 FCFA)"
        self.assertEqual(str(self.payment), expected)
    
    def test_payment_list_view(self):
        """Test de la vue liste des paiements"""
        response = self.client.get(reverse('finances:payment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Liste des Paiements")
    
    def test_payment_create_view(self):
        """Test de la vue création de paiement"""
        response = self.client.get(reverse('finances:payment_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enregistrer un paiement")
    
    def test_payment_detail_view(self):
        """Test de la vue détail de paiement"""
        response = self.client.get(reverse('finances:payment_detail', args=[self.payment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.payment.receipt)
    
    def test_payment_receipt_view(self):
        """Test de la vue reçu de paiement"""
        response = self.client.get(reverse('finances:payment_receipt', args=[self.payment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "REÇU DE PAIEMENT")

class FeeDiscountTests(FinancesTestCase):
    """Tests pour les remises"""
    
    def setUp(self):
        super().setUp()
        self.discount = FeeDiscount.objects.create(
            student=self.student,
            tranche=self.tranche1,
            amount=Decimal('20000'),
            reason="Bourse d'excellence",
            created_by=self.user
        )
    
    def test_discount_creation(self):
        """Test de création d'une remise"""
        self.assertEqual(self.discount.student, self.student)
        self.assertEqual(self.discount.tranche, self.tranche1)
        self.assertEqual(self.discount.amount, Decimal('20000'))
        self.assertEqual(self.discount.reason, "Bourse d'excellence")
        self.assertEqual(self.discount.created_by, self.user)
    
    def test_discount_str(self):
        """Test de la méthode __str__"""
        expected = f"Remise 20000 - {self.student} ({self.tranche1})"
        self.assertEqual(str(self.discount), expected)
    
    def test_discount_list_view(self):
        """Test de la vue liste des remises"""
        response = self.client.get(reverse('finances:discount_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Liste des Remises")

class MoratoriumTests(FinancesTestCase):
    """Tests pour les moratoires"""
    
    def setUp(self):
        super().setUp()
        self.moratorium = Moratorium.objects.create(
            student=self.student,
            tranche=self.tranche1,
            amount=Decimal('50000'),
            new_due_date=date(2024, 12, 15),
            reason="Difficultés financières"
        )
    
    def test_moratorium_creation(self):
        """Test de création d'un moratoire"""
        self.assertEqual(self.moratorium.student, self.student)
        self.assertEqual(self.moratorium.tranche, self.tranche1)
        self.assertEqual(self.moratorium.amount, Decimal('50000'))
        self.assertEqual(self.moratorium.new_due_date, date(2024, 12, 15))
        self.assertEqual(self.moratorium.reason, "Difficultés financières")
        self.assertFalse(self.moratorium.is_approved)
    
    def test_moratorium_str(self):
        """Test de la méthode __str__"""
        expected = f"Moratoire {self.student} - {self.tranche1} (50000 FCFA)"
        self.assertEqual(str(self.moratorium), expected)
    
    def test_moratorium_approval(self):
        """Test d'approbation d'un moratoire"""
        self.moratorium.is_approved = True
        self.moratorium.approved_at = timezone.now()
        self.moratorium.save()
        
        self.assertTrue(self.moratorium.is_approved)
        self.assertIsNotNone(self.moratorium.approved_at)
    
    def test_moratorium_list_view(self):
        """Test de la vue liste des moratoires"""
        response = self.client.get(reverse('finances:moratorium_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Liste des Moratoires")

class PaymentRefundTests(FinancesTestCase):
    """Tests pour les remboursements"""
    
    def setUp(self):
        super().setUp()
        self.payment = TranchePayment.objects.create(
            student=self.student,
            tranche=self.tranche1,
            amount=Decimal('100000'),
            mode='cash',
            receipt='REC-20241201-001',
            created_by=self.user
        )
        self.refund = PaymentRefund.objects.create(
            payment=self.payment,
            amount=Decimal('50000'),
            reason="Erreur de saisie",
            created_by=self.user
        )
    
    def test_refund_creation(self):
        """Test de création d'un remboursement"""
        self.assertEqual(self.refund.payment, self.payment)
        self.assertEqual(self.refund.amount, Decimal('50000'))
        self.assertEqual(self.refund.reason, "Erreur de saisie")
        self.assertEqual(self.refund.created_by, self.user)
    
    def test_refund_str(self):
        """Test de la méthode __str__"""
        expected = f"Remboursement 50000 - {self.payment}"
        self.assertEqual(str(self.refund), expected)
    
    def test_refund_list_view(self):
        """Test de la vue liste des remboursements"""
        response = self.client.get(reverse('finances:refund_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Liste des Remboursements")

class ExtraFeeTests(FinancesTestCase):
    """Tests pour les frais annexes"""
    
    def setUp(self):
        super().setUp()
        self.extra_fee = ExtraFee.objects.create(
            name="Frais d'examen",
            amount=Decimal('15000'),
            year=self.year,
            school_class=self.school_class,
            due_date=date(2024, 11, 30),
            created_by=self.user
        )
    
    def test_extra_fee_creation(self):
        """Test de création d'un frais annexe"""
        self.assertEqual(self.extra_fee.name, "Frais d'examen")
        self.assertEqual(self.extra_fee.amount, Decimal('15000'))
        self.assertEqual(self.extra_fee.year, self.year)
        self.assertEqual(self.extra_fee.school_class, self.school_class)
        self.assertEqual(self.extra_fee.due_date, date(2024, 11, 30))
        self.assertEqual(self.extra_fee.created_by, self.user)
    
    def test_extra_fee_str(self):
        """Test de la méthode __str__"""
        expected = "Frais d'examen - 15000 FCFA"
        self.assertEqual(str(self.extra_fee), expected)
    
    def test_extra_fee_list_view(self):
        """Test de la vue liste des frais annexes"""
        response = self.client.get(reverse('finances:extra_fee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Liste des Frais Annexes")

class FinancialDashboardTests(FinancesTestCase):
    """Tests pour le tableau de bord financier"""
    
    def test_financial_dashboard_view(self):
        """Test de la vue tableau de bord financier"""
        response = self.client.get(reverse('finances:financial_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tableau de Bord Financier")
    
    def test_student_financial_status_view(self):
        """Test de la vue statut financier étudiant"""
        response = self.client.get(reverse('finances:student_financial_status', args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Statut Financier")

class FormTests(FinancesTestCase):
    """Tests pour les formulaires"""
    
    def test_fee_structure_form_valid(self):
        """Test de validation du formulaire de structure de frais"""
        from .forms import FeeStructureForm
        
        form_data = {
            'school_class': self.school_class.pk,
            'year': self.year.pk,
            'inscription_fee': '50000',
            'tuition_total': '300000',
            'tranche_count': '3'
        }
        
        form = FeeStructureForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_payment_form_valid(self):
        """Test de validation du formulaire de paiement"""
        from .forms import TranchePaymentForm
        
        form_data = {
            'student': self.student.pk,
            'tranche': self.tranche1.pk,
            'amount': '100000',
            'mode': 'cash',
            'receipt': 'REC-20241201-001'
        }
        
        form = TranchePaymentForm(data=form_data)
        self.assertTrue(form.is_valid())

class IntegrationTests(FinancesTestCase):
    """Tests d'intégration"""
    
    def test_complete_payment_workflow(self):
        """Test du workflow complet de paiement"""
        # 1. Créer un paiement
        payment = TranchePayment.objects.create(
            student=self.student,
            tranche=self.tranche1,
            amount=Decimal('100000'),
            mode='cash',
            receipt='REC-20241201-001',
            created_by=self.user
        )
        
        # 2. Vérifier que le paiement existe
        self.assertTrue(TranchePayment.objects.filter(pk=payment.pk).exists())
        
        # 3. Créer une remise
        discount = FeeDiscount.objects.create(
            student=self.student,
            tranche=self.tranche1,
            amount=Decimal('20000'),
            reason="Bourse",
            created_by=self.user
        )
        
        # 4. Vérifier le calcul du reste à payer
        total_paid = TranchePayment.objects.filter(tranche=self.tranche1).aggregate(
            total=Sum('amount'))['total'] or 0
        total_discounts = FeeDiscount.objects.filter(tranche=self.tranche1).aggregate(
            total=Sum('amount'))['total'] or 0
        remaining = self.tranche1.amount - total_paid - total_discounts
        
        self.assertEqual(remaining, Decimal('-20000'))  # Trop payé à cause de la remise
    
    def test_moratorium_workflow(self):
        """Test du workflow de moratoire"""
        # 1. Créer un moratoire
        moratorium = Moratorium.objects.create(
            student=self.student,
            tranche=self.tranche1,
            amount=Decimal('50000'),
            new_due_date=date(2024, 12, 15),
            reason="Difficultés"
        )
        
        # 2. Vérifier qu'il n'est pas approuvé
        self.assertFalse(moratorium.is_approved)
        
        # 3. Approuver le moratoire
        moratorium.is_approved = True
        moratorium.approved_at = timezone.now()
        moratorium.save()
        
        # 4. Vérifier qu'il est approuvé
        self.assertTrue(moratorium.is_approved)
        self.assertIsNotNone(moratorium.approved_at)
