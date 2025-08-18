from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    """Permet d'accéder à une clé d'un dictionnaire dans un template : {{ mydict|dict_get:mykey }}"""
    if d is None:
        return None
    return d.get(key, [])

# 07/07/2025 - Filtre pour récupérer un objet par id dans une liste
@register.filter
def get_by_id(subjects, subject_id):
    """
    Récupère un objet Subject à partir d'une liste ou d'un dictionnaire de subjects et d'un id.
    """
    try:
        subject_id = int(subject_id)
    except (ValueError, TypeError):
        pass
    if isinstance(subjects, dict):
        return subjects.get(subject_id)
    try:
        # Si c'est une liste ou un QuerySet
        return next((s for s in subjects if getattr(s, 'id', None) == subject_id), None)
    except Exception:
        return None

# Filtres pour les couleurs des créneaux
@register.filter
def slot_color(subject_id):
    """Retourne une couleur de fond pour un créneau basée sur l'ID de la matière"""
    try:
        subject_id = int(subject_id)
        colors = [
            'blue', 'green', 'purple', 'pink', 'indigo', 'yellow', 'red', 'teal'
        ]
        return colors[subject_id % len(colors)]
    except (ValueError, TypeError):
        return 'blue'  # Couleur par défaut

@register.filter
def slot_text_color(subject_id):
    """Retourne une couleur de texte pour un créneau basée sur l'ID de la matière"""
    try:
        subject_id = int(subject_id)
        colors = [
            'blue', 'green', 'purple', 'pink', 'indigo', 'yellow', 'red', 'teal'
        ]
        return colors[subject_id % len(colors)]
    except (ValueError, TypeError):
        return 'blue'  # Couleur par défaut 