from students.models import Student
from teachers.models import Teacher
from classes.models import SchoolClass

def global_stats(request):
    """
    Ajoute automatiquement les statistiques globales dans le contexte de toutes les pages
    """
    try:
        # Compteurs en temps réel
        students_count = Student.objects.filter(is_active=True).count()
        teachers_count = Teacher.objects.filter(is_active=True).count()
        classes_count = SchoolClass.objects.filter(is_active=True).count()
        
        return {
            'students_count': students_count,
            'teachers_count': teachers_count,
            'classes_count': classes_count,
        }
    except Exception:
        # En cas d'erreur (base de données non accessible, migrations en cours, etc.)
        return {
            'students_count': 0,
            'teachers_count': 0,
            'classes_count': 0,
        }
