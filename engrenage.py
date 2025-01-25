import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import math
import json

class GearCalculator:
    def __init__(self, master):
        self.master = master
        self.catalog = self.load_default_catalog()
        
        # Création du TabView
        self.tabview = ctk.CTkTabview(self.master)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        # Création des onglets
        self.tab1 = self.tabview.add("Calculs de base")
        self.tab2 = self.tabview.add("Catalogue")
        
        # Configuration des onglets
        self.setup_basic_calculations_tab()
        self.setup_catalog_tab()
        
    def load_default_catalog(self):
        return {
            "Engrenages droits": [
                {"nom": "ED-001", "module": 1, "nombre_dents": 20, "angle_pression": 20},
                {"nom": "ED-002", "module": 2, "nombre_dents": 30, "angle_pression": 20}
            ],
            "Engrenages hélicoïdaux": [
                {"nom": "EH-001", "module": 1.5, "nombre_dents": 25, "angle_pression": 20, "angle_helice": 15},
                {"nom": "EH-002", "module": 2.5, "nombre_dents": 35, "angle_pression": 20, "angle_helice": 20}
            ]
        }

    def setup_basic_calculations_tab(self):
        # Frame pour les entrées
        input_frame = ctk.CTkFrame(self.tab1)
        input_frame.pack(padx=10, pady=5, fill="x")

        # Création des champs d'entrée
        ctk.CTkLabel(input_frame, text="Module (mm):").pack(pady=5)
        self.module_entry = ctk.CTkEntry(input_frame)
        self.module_entry.pack(pady=5)

        ctk.CTkLabel(input_frame, text="Nombre de dents:").pack(pady=5)
        self.teeth_entry = ctk.CTkEntry(input_frame)
        self.teeth_entry.pack(pady=5)

        ctk.CTkLabel(input_frame, text="Angle de pression (°):").pack(pady=5)
        self.pressure_angle_entry = ctk.CTkEntry(input_frame)
        self.pressure_angle_entry.pack(pady=5)
        self.pressure_angle_entry.insert(0, "20")

        # Bouton de calcul
        calculate_button = ctk.CTkButton(input_frame, text="Calculer", command=self.calculate)
        calculate_button.pack(pady=10)

        # Frame pour les résultats
        results_frame = ctk.CTkFrame(self.tab1)
        results_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.results_text = ctk.CTkTextbox(results_frame, height=200)
        self.results_text.pack(padx=5, pady=5, fill="both", expand=True)

    def setup_catalog_tab(self):
        # Frame pour le catalogue
        catalog_frame = ctk.CTkFrame(self.tab2)
        catalog_frame.pack(padx=10, pady=5, fill="both", expand=True)

        # Style pour le Treeview
        style = ttk.Style()
        style.configure("Treeview", background="gray20", 
                       fieldbackground="gray20", foreground="white")

        # Treeview pour afficher le catalogue
        self.tree = ttk.Treeview(catalog_frame, columns=("Module", "Dents", "Angle"), show="headings")
        self.tree.heading("Module", text="Module")
        self.tree.heading("Dents", text="Nombre de dents")
        self.tree.heading("Angle", text="Angle de pression")
        self.tree.pack(fill="both", expand=True)

        # Boutons pour le catalogue
        button_frame = ctk.CTkFrame(self.tab2)
        button_frame.pack(pady=5)

        ctk.CTkButton(button_frame, text="Sauvegarder", command=self.save_catalog).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Charger", command=self.load_catalog).pack(side="left", padx=5)

        # Remplissage du catalogue
        self.populate_catalog()

    def calculate(self):
        try:
            module = float(self.module_entry.get())
            teeth = int(self.teeth_entry.get())
            pressure_angle = float(self.pressure_angle_entry.get())

            pitch_diameter = module * teeth
            base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
            addendum = module
            dedendum = 1.25 * module
            outside_diameter = pitch_diameter + (2 * addendum)
            root_diameter = pitch_diameter - (2 * dedendum)
            circular_pitch = math.pi * module
            base_pitch = circular_pitch * math.cos(math.radians(pressure_angle))

            self.results_text.delete("1.0", "end")
            results = f"""Résultats des calculs:
            
Diamètre primitif: {pitch_diameter:.2f} mm
Diamètre de base: {base_diameter:.2f} mm
Diamètre extérieur: {outside_diameter:.2f} mm
Diamètre de fond: {root_diameter:.2f} mm
Pas circulaire: {circular_pitch:.2f} mm
Pas de base: {base_pitch:.2f} mm
Saillie (addendum): {addendum:.2f} mm
Creux (dedendum): {dedendum:.2f} mm"""
            self.results_text.insert("1.0", results)

        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")

    def populate_catalog(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for category, items in self.catalog.items():
            category_id = self.tree.insert("", "end", text=category)
            for item in items:
                values = (item["module"], item["nombre_dents"], item["angle_pression"])
                self.tree.insert(category_id, "end", values=values)

    def save_catalog(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.catalog, f, indent=4)
                messagebox.showinfo("Succès", "Catalogue sauvegardé avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def load_catalog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.catalog = json.load(f)
                self.populate_catalog()
                messagebox.showinfo("Succès", "Catalogue chargé avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")

def main():
    # Configuration du thème
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Création de la fenêtre principale
    root = ctk.CTk()
    root.title("Calculateur d'engrenages")
    root.geometry("800x600")

    # Création de l'instance du calculateur
    calculator = GearCalculator(root)

    # Lancement de la boucle principale
    root.mainloop()

if __name__ == "__main__":
    main()
