from django.core.management.base import BaseCommand
import os
import sys

class Command(BaseCommand):
    help = 'Peuple la base de données avec des données scolaires complètes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirme que vous voulez peupler la base de données',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'Attention: Cette commande va créer de nombreuses données dans votre base de données.\n'
                    'Utilisez --confirm pour confirmer.'
                )
            )
            return

        # Importer et exécuter le script
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'scripts', 'populate_school_data.py'
        )
        
        # Ajouter le chemin du script au sys.path temporairement
        script_dir = os.path.dirname(script_path)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        try:
            # Importer et exécuter la fonction
            from populate_school_data import populate_all_data
            populate_all_data()
            self.stdout.write(
                self.style.SUCCESS('Données scolaires créées avec succès!')
            )
        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur d\'importation: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création des données: {e}')
            )
        finally:
            # Nettoyer sys.path
            if script_dir in sys.path:
                sys.path.remove(script_dir)
