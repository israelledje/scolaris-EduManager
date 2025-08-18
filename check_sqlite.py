#!/usr/bin/env python
"""
Script pour vérifier le contenu de la base SQLite
"""

import sqlite3
import os

def check_sqlite():
    """Vérifie le contenu de la base SQLite"""
    if not os.path.exists('db.sqlite3'):
        print("❌ db.sqlite3 n'existe pas")
        return
    
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Lister les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 Tables SQLite ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Compter les données dans les principales tables
        main_tables = [
            'classes_schoolclass',
            'students_student', 
            'subjects_subject',
            'teachers_teacher',
            'authentication_user'
        ]
        
        print("\n📊 Données dans les tables principales:")
        for table in main_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} enregistrements")
            except Exception as e:
                print(f"  - {table}: Erreur - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")

if __name__ == '__main__':
    check_sqlite()
