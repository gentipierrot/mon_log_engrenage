# gear_calculator.py
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtCore import Qt  # Ajout de cet import crucial

class GearCalculator(QWidget):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent, flags)
        self.initUI()
    
    def initUI(self):
        # Création du layout principal
        layout = QVBoxLayout()
        
        # Création du TabWidget
        self.tab_widget = QTabWidget()
        
        # Création des onglets
        self.catalog_tab = QWidget()
        self.search_tab = QWidget()
        
        # Ajout des onglets au TabWidget
        self.tab_widget.addTab(self.catalog_tab, "Calculs de base")
        self.tab_widget.addTab(self.search_tab, "Catalogue")
        
        # Ajout du TabWidget au layout
        layout.addWidget(self.tab_widget)
        
        # Définition du layout pour le widget principal
        self.setLayout(layout)
        
        # Configuration de la fenêtre
        self.setWindowTitle("Calculateur d'engrenages")
        self.setGeometry(100, 100, 800, 600)
