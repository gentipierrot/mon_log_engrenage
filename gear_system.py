class GearSystem:
    def __init__(self):
        self.current_gear = None
        self.settings = {}
        self.gear_data = {
            'module': 1.0,
            'teeth': 20,
            'pressure_angle': 20.0,
            'rotation': 0.0
        }

    def update_gear(self, parameters):
        """
        Met à jour les paramètres de l'engrenage
        """
        try:
            self.gear_data.update(parameters)
            self.calculate_geometry()
            return True
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'engrenage : {e}")
            return False

    def calculate_geometry(self):
        """
        Calcule la géométrie de l'engrenage
        """
        try:
            calculator = GearCalculator()
            self.current_gear = calculator.calculate(
                self.gear_data['module'],
                self.gear_data['teeth'],
                self.gear_data['pressure_angle']
            )
            return True
        except Exception as e:
            print(f"Erreur lors du calcul de la géométrie : {e}")
            return False

    def get_gear_data(self):
        """
        Retourne les données actuelles de l'engrenage
        """
        return self.gear_data

    def export_stl(self, filename):
        """
        Exporte l'engrenage au format STL
        """
        try:
            if self.current_gear:
                # Logique d'export STL à implémenter
                return True
            return False
        except Exception as e:
            print(f"Erreur lors de l'export STL : {e}")
            return False

class GearCalculator:
    def __init__(self):
        self.results = {}

    def calculate(self, module, teeth, pressure_angle):
        """
        Calcule les paramètres de l'engrenage
        """
        try:
            import math
            
            # Calculs de base
            pitch_diameter = module * teeth
            base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
            addendum = 1.0 * module
            dedendum = 1.25 * module
            outer_diameter = pitch_diameter + 2 * addendum
            root_diameter = pitch_diameter - 2 * dedendum
            
            # Stockage des résultats
            self.results = {
                'pitch_diameter': pitch_diameter,
                'base_diameter': base_diameter,
                'outer_diameter': outer_diameter,
                'root_diameter': root_diameter,
                'addendum': addendum,
                'dedendum': dedendum,
                'circular_pitch': math.pi * module,
                'base_pitch': math.pi * module * math.cos(math.radians(pressure_angle))
            }
            
            return self.results
            
        except Exception as e:
            print(f"Erreur lors des calculs : {e}")
            return None

    def get_results(self):
        """
        Retourne les résultats des calculs
        """
        return self.results

    @staticmethod
    def validate_parameters(module, teeth, pressure_angle):
        """
        Valide les paramètres d'entrée
        """
        if module <= 0:
            return False, "Le module doit être positif"
        if teeth < 5:
            return False, "Le nombre de dents doit être au moins 5"
        if pressure_angle <= 0 or pressure_angle >= 45:
            return False, "L'angle de pression doit être entre 0 et 45 degrés"
        return True, ""
