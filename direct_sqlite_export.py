#!/usr/bin/env python
"""
Script d'export direct depuis SQLite3 vers JSON
Contourne les problèmes de configuration Django
"""

import sqlite3
import json
import os
from datetime import datetime

def export_sqlite_to_json():
    """Exporte directement depuis SQLite3 vers JSON"""
    print("💾 Export direct depuis SQLite3...")
    
    if not os.path.exists('db.sqlite3'):
        print("❌ db.sqlite3 n'existe pas")
        return False
    
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Tables principales à exporter
        tables_to_export = [
            'authentication_user',
            'classes_schoolclass',
            'students_student',
            'subjects_subject',
            'teachers_teacher',
            'teachers_teachingassignment',
            'classes_timetable',
            'classes_timetableslot',
            'subjects_subject_program',
            'subjects_learning_unit',
            'subjects_lesson',
            'notes_trimester',
            'notes_evaluation',
            'notes_bulletin',
            'notes_bulletinline',
            'notes_studentgrade',
            'finances_feestructure',
            'finances_feetranche',
            'finances_feediscount',
            'finances_moratorium',
            'finances_tranchepayment',
            'finances_paymentrefund',
            'finances_inscriptionpayment',
            'finances_extrafeetype',
            'finances_extrafee',
            'finances_extrafeepayment',
            'documents_documentcategory',
            'documents_documenttemplate',
            'documents_studentdocument',
            'students_scholarship',
            'students_sanction',
            'students_payment',
            'students_guardian',
            'students_studentdocument',
            'students_subject',
            'students_attendance',
            'students_studentclasshistory',
            'students_evaluation'
        ]
        
        exported_data = []
        total_records = 0
        
        for table_name in tables_to_export:
            try:
                # Récupérer la structure de la table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                
                if not columns_info:
                    print(f"⚠️ Table {table_name} non trouvée, ignorée")
                    continue
                
                # Récupérer les données
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                if rows:
                    # Créer les objets Django
                    for row in rows:
                        # Créer un dictionnaire avec les noms de colonnes
                        row_data = {}
                        for i, col_info in enumerate(columns_info):
                            col_name = col_info[1]
                            col_type = col_info[2]
                            value = row[i]
                            
                            # Gérer les types de données
                            if value is None:
                                row_data[col_name] = None
                            elif col_type == 'INTEGER':
                                row_data[col_name] = int(value)
                            elif col_type == 'REAL':
                                row_data[col_name] = float(value)
                            elif col_type == 'TEXT':
                                row_data[col_name] = str(value)
                            elif col_type == 'BLOB':
                                row_data[col_name] = str(value) if value else None
                            else:
                                row_data[col_name] = value
                        
                        # Créer l'objet Django
                        django_obj = {
                            'model': table_name.replace('_', '.', 1),  # classes.schoolclass
                            'pk': row_data.get('id', row_data.get('pk')),
                            'fields': {k: v for k, v in row_data.items() if k not in ['id', 'pk']}
                        }
                        
                        exported_data.append(django_obj)
                    
                    print(f"✅ {table_name}: {len(rows)} enregistrements")
                    total_records += len(rows)
                else:
                    print(f"ℹ️ {table_name}: 0 enregistrements")
                    
            except Exception as e:
                print(f"❌ Erreur pour {table_name}: {e}")
                continue
        
        conn.close()
        
        # Sauvegarder en JSON
        output_file = 'temp_data_direct.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Export terminé : {total_records} enregistrements dans {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export : {e}")
        return False

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 EXPORT DIRECT SQLITE3 → JSON")
    print("=" * 60)
    
    if export_sqlite_to_json():
        print("\n✅ Export réussi !")
        print("💡 Vous pouvez maintenant utiliser temp_data_direct.json pour l'import")
    else:
        print("\n❌ Export échoué")

if __name__ == '__main__':
    main()
