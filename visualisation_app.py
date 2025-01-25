import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, QAction, 
                            QToolBar, QStatusBar, QTextEdit, QDockWidget, 
                            QVBoxLayout, QWidget, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class VisualisationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualisation App")
        self.setGeometry(100, 100, 800, 600)
        self.check_icons()
        self.init_ui()
        self.current_file = None

    def check_icons(self):
        if not os.path.exists('icons'):
            os.makedirs('icons')
            print("Dossier 'icons' créé. Veuillez y ajouter vos icônes.")

    def init_ui(self):
        # Zone de texte centrale
        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)

        # Barre de menu
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu('Fichier')
        
        # Actions du menu Fichier
        new_action = self.create_action('Nouveau', 'icons/new.png', 'Ctrl+N', 
                                      'Créer un nouveau fichier')
        open_action = self.create_action('Ouvrir', 'icons/open.png', 'Ctrl+O', 
                                       'Ouvrir un fichier existant')
        save_action = self.create_action('Enregistrer', 'icons/save.png', 'Ctrl+S', 
                                       'Enregistrer le fichier')
        export_action = self.create_action('Exporter', 'icons/export.png', 'Ctrl+E', 
                                         'Exporter le fichier')
        exit_action = self.create_action('Quitter', 'icons/exit.png', 'Ctrl+Q', 
                                       'Quitter l\'application')
        
        # Ajout des actions au menu Fichier
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # Menu Affichage
        view_menu = menubar.addMenu('Affichage')
        view_action = self.create_action('Vue', 'icons/view.png', 'Ctrl+V', 
                                       'Changer la vue')
        view_menu.addAction(view_action)

        # Barre d'outils
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        toolbar.addAction(new_action)
        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addAction(export_action)

        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Prêt')

        # Panneau latéral
        dock = QDockWidget("Panneau latéral", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        dock_content = QWidget()
        dock_layout = QVBoxLayout()
        dock_content.setLayout(dock_layout)
        dock.setWidget(dock_content)

        # Raccourcis supplémentaires
        self.text_edit.setUndoRedoEnabled(True)

    def create_action(self, text, icon_path, shortcut=None, status_tip=None):
        action = QAction(QIcon(icon_path), text, self)
        if shortcut:
            action.setShortcut(shortcut)
        if status_tip:
            action.setStatusTip(status_tip)
        
        # Connecter les actions aux méthodes correspondantes
        if text == 'Nouveau':
            action.triggered.connect(self.new_file)
        elif text == 'Ouvrir':
            action.triggered.connect(self.open_file)
        elif text == 'Enregistrer':
            action.triggered.connect(self.save_file)
        elif text == 'Exporter':
            action.triggered.connect(self.export_file)
        elif text == 'Quitter':
            action.triggered.connect(self.close)
        elif text == 'Vue':
            action.triggered.connect(self.change_view)
        
        return action

    def new_file(self):
        try:
            if self.text_edit.document().isModified():
                reply = QMessageBox.question(self, 'Confirmation',
                                          'Voulez-vous sauvegarder les modifications ?',
                                          QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    self.save_file()
                elif reply == QMessageBox.Cancel:
                    return

            self.text_edit.clear()
            self.current_file = None
            self.status_bar.showMessage('Nouveau fichier créé')
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création : {str(e)}")

    def open_file(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier", "", 
                                                    "All Files (*);;Text Files (*.txt)")
            if filename:
                with open(filename, 'r') as f:
                    self.text_edit.setText(f.read())
                self.current_file = filename
                self.status_bar.showMessage(f'Fichier ouvert : {filename}')
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le fichier : {str(e)}")

    def save_file(self):
        try:
            if not self.current_file:
                filename, _ = QFileDialog.getSaveFileName(self, "Enregistrer le fichier", "", 
                                                        "All Files (*);;Text Files (*.txt)")
                if filename:
                    self.current_file = filename
            
            if self.current_file:
                with open(self.current_file, 'w') as f:
                    f.write(self.text_edit.toPlainText())
                self.status_bar.showMessage(f'Fichier sauvegardé : {self.current_file}')
                return True
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder : {str(e)}")
        return False

    def export_file(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Exporter le fichier", "", 
                                                    "CSV Files (*.csv);;Excel Files (*.xlsx)")
            if filename:
                # Logique d'export à implémenter selon vos besoins
                self.status_bar.showMessage(f'Fichier exporté : {filename}')
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export : {str(e)}")

    def change_view(self):
        # À implémenter selon vos besoins
        self.status_bar.showMessage('Changement de vue')

    def closeEvent(self, event):
        if self.text_edit.document().isModified():
            reply = QMessageBox.question(self, 'Confirmation',
                                       'Document non sauvegardé. Voulez-vous sauvegarder ?',
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                if not self.save_file():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Style moderne
    window = VisualisationApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
