# gear_calculator.py
from PyQt5.QtWidgets import (QWidget, QTabWidget, QVBoxLayout, QGridLayout,
                           QLabel, QLineEdit, QPushButton, QFrame)
from PyQt5.QtCore import Qt

class GearCalculator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        # Création du layout principal
        layout = QVBoxLayout()
        
        # Création du TabWidget
        self.tab_widget = QTabWidget()
        
        # Création des onglets
        self.calc_tab = QWidget()
        self.catalog_tab = QWidget()
        
        # Initialisation des contenus des onglets
        self.init_calc_tab()
        self.init_catalog_tab()
        
        # Ajout des onglets au TabWidget
        self.tab_widget.addTab(self.calc_tab, "Calculs de base")
        self.tab_widget.addTab(self.catalog_tab, "Catalogue")
        
        # Ajout du TabWidget au layout
        layout.addWidget(self.tab_widget)
        
        # Définition du layout pour le widget principal
        self.setLayout(layout)

    def init_calc_tab(self):
        layout = QGridLayout()
        
        # Création des widgets pour les calculs de base
        labels = ["Module:", "Nombre de dents:", "Angle de pression:", "Diamètre primitif:"]
        self.inputs = {}
        
        for i, label in enumerate(labels):
            layout.addWidget(QLabel(label), i, 0)
            self.inputs[label] = QLineEdit()
            layout.addWidget(self.inputs[label], i, 1)
        
        # Bouton de calcul
        calc_button = QPushButton("Calculer")
        calc_button.clicked.connect(self.calculate)
        layout.addWidget(calc_button, len(labels), 0, 1, 2)
        
        # Zone de résultats
        self.results_frame = QFrame()
        self.results_frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.results_layout = QVBoxLayout(self.results_frame)
        self.results_label = QLabel("Résultats apparaîtront ici")
        self.results_layout.addWidget(self.results_label)
        
        layout.addWidget(self.results_frame, len(labels)+1, 0, 1, 2)
        
        self.calc_tab.setLayout(layout)

    def init_catalog_tab(self):
        layout = QVBoxLayout()
        
        # Ajout des widgets pour la recherche dans le catalogue
        search_label = QLabel("Recherche dans le catalogue:")
        search_input = QLineEdit()
        
        layout.addWidget(search_label)
        layout.addWidget(search_input)
        
        self.catalog_tab.setLayout(layout)

    def calculate(self):
        try:
            # Récupération des valeurs
            module = float(self.inputs["Module:"].text())
            teeth = float(self.inputs["Nombre de dents:"].text())
            pressure_angle = float(self.inputs["Angle de pression:"].text())
            pitch_diameter = float(self.inputs["Diamètre primitif:"].text())
            
            # Calculs (à adapter selon vos besoins)
            results = f"""
            Module: {module}
            Nombre de dents: {teeth}
            Angle de pression: {pressure_angle}°
            Diamètre primitif: {pitch_diameter} mm
            """
            
            self.results_label.setText(results)
            
        except ValueError:
            self.results_label.setText("Erreur: Veuillez entrer des valeurs numériques valides")
