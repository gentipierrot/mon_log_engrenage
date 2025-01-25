import json
import os

class ProjectManager:
    @staticmethod
    def save_project(filename, data):
        """Sauvegarde les données du projet dans un fichier"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")
            return False

    @staticmethod
    def load_project(filename):
        """Charge les données d'un projet depuis un fichier"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Erreur lors du chargement : {e}")
            return None

    @staticmethod
    def save_settings(settings):
        """Sauvegarde les paramètres de l'application"""
        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres : {e}")
            return False

    @staticmethod
    def load_settings():
        """Charge les paramètres de l'application"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                return settings
            return None
        except Exception as e:
            print(f"Erreur lors du chargement des paramètres : {e}")
            return None

