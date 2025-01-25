# -*- coding: utf-8 -*-

# Imports système
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports bibliothèques standards
import yaml
import json
import math
from math import pi, cos, radians
import numpy as np
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

# Imports PyQt5
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QMessageBox,
    QSlider,
    QGridLayout,
    QTabWidget,
    QScrollArea,
    QToolBar,
    QAction,
    QComboBox,
    QFileDialog,
    QStatusBar
)
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QPainter, QFont, QIcon


# Imports OpenGL
import OpenGL.GL as GL
from OpenGL.GL import *
from OpenGL.GLU import *

# Imports locaux
from gear_calculator import GearCalculator
from project_manager import ProjectManager
from gl_widget import GLWidget
from gear_system import GearSystem

def calculate(self):
    try:
        # Récupération des valeurs
        module = self.module_input.value()
        teeth1 = self.teeth1_input.value()
        teeth2 = self.teeth2_input.value()
        pressure_angle = self.pressure_angle_input.value()

        # Récupération sécurisée des angles de repos
        try:
            stop_angle_start = float(self.stop_angle_start_input.text() or "0")
            stop_angle_end = float(self.stop_angle_end_input.text() or "0")
        except ValueError:
            stop_angle_start = 0
            stop_angle_end = 0

        # Calculs roue 1
        dp1 = module * teeth1
        da1 = dp1 + 2 * module
        df1 = dp1 - 2.5 * module
        cycle_angle1 = 360 / teeth1

        # Calculs roue 2
        dp2 = module * teeth2
        da2 = dp2 + 2 * module
        df2 = dp2 - 2.5 * module
        cycle_angle2 = 360 / teeth2

        # Calculs globaux
        entraxe = (dp1 + dp2) / 2
        rapport = teeth2 / teeth1

        # Mise à jour des résultats
        self.dp1_result.setText(f"{dp1:.2f}")
        self.da1_result.setText(f"{da1:.2f}")
        self.df1_result.setText(f"{df1:.2f}")
        self.cycle_angle1_result.setText(f"{cycle_angle1:.2f}")
        
        self.dp2_result.setText(f"{dp2:.2f}")
        self.da2_result.setText(f"{da2:.2f}")
        self.df2_result.setText(f"{df2:.2f}")
        self.cycle_angle2_result.setText(f"{cycle_angle2:.2f}")
        
        self.entraxe_result.setText(f"{entraxe:.2f}")
        self.rapport_result.setText(f"{rapport:.2f}")

        # Calcul des points des engrenages
        driver_points = self.calculate_gear_points(module, teeth1, pressure_angle)
        driven_points = self.calculate_gear_points(module, teeth2, pressure_angle)

        # Activation des contrôles de simulation
        self.start_button.setEnabled(True)
        self.reset_button.setEnabled(True)

    except Exception as e:
        QMessageBox.warning(self, "Erreur", f"Une erreur est survenue : {str(e)}")
        return


class ProjectManager:
    def __init__(self):
        self.current_project = None
        self.projects = []
        
    def new_project(self):
        """Crée un nouveau projet"""
        project = {
            'name': f'Projet_{len(self.projects) + 1}',
            'parameters': {},
            'results': {},
            'modified': False
        }
        self.projects.append(project)
        self.current_project = project
        return project
        
    def save_project(self, filepath):
        """Sauvegarde le projet actuel"""
        if self.current_project:
            # Logique de sauvegarde à implémenter
            self.current_project['modified'] = False
            return True
        return False
        
    def load_project(self, filepath):
        """Charge un projet depuis un fichier"""
        # Logique de chargement à implémenter
        pass
        
    def get_current_project(self):
        """Retourne le projet actuel"""
        return self.current_project
        
    def set_parameter(self, key, value):
        """Définit un paramètre dans le projet actuel"""
        if self.current_project:
            self.current_project['parameters'][key] = value
            self.current_project['modified'] = True
            
    def get_parameter(self, key, default=None):
        """Récupère un paramètre du projet actuel"""
        if self.current_project:
            return self.current_project['parameters'].get(key, default)
        return default


class AdvancedGearGLWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


class GearGLWidget(QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.gear_data_driver = None
        self.gear_data_driven = None
        self.rotation = 0
        # Ajout pour l'angle de repos
        self.stop_angle_start = 0
        self.stop_angle_end = 0
        self.is_in_stop_zone = False
        # Timer existant
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_rotation)
        self.timer.start(16)
        self.is_animating = False
        #
        self.parent = parent
        self.gear_data_driver = None
        self.gear_data_driven = None
        self.rotation = 0  # Angle de rotation actuel
        # Paramètres d'animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_rotation)
        self.timer.start(16)  # ~60 FPS
        self.is_animating = False
        # Couleur par défaut pour les engrenages
        self.gear_color = [0.8, 0.8, 0.8, 1.0]

    def initializeGL(self):
        print("Début initialisation OpenGL")
        try:
            glClearColor(0.0, 0.0, 0.0, 1.0)  # Fond noir
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, self.gear_color)
            print("Initialisation OpenGL réussie")
        except Exception as e:
            print(f"Erreur lors de l'initialisation OpenGL: {str(e)}")

    def resizeGL(self, w, h):
        print(f"Redimensionnement: {w}x{h}")
        try:
            glViewport(0, 0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            aspect = w / h if h != 0 else 1.0
            gluPerspective(45, aspect, 0.1, 100.0)
            glMatrixMode(GL_MODELVIEW)
        except Exception as e:
            print(f"Erreur lors du redimensionnement: {str(e)}")

    def paintGL_view1(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)

        print("Début paintGL")
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glTranslatef(0.0, 0.0, -20.0)

            if self.gear_data_driver and self.gear_data_driven:
                self.draw_gears()
            
        except Exception as e:
            print(f"Erreur lors du rendu: {str(e)}")

    def draw_gears(self):
        # Dessiner l'engrenage moteur
        glPushMatrix()
        glRotatef(self.rotation, 0, 0, 1)
        self.dessiner_engrenage(self.gear_data_driver, (0.0, 0.0, 1.0))  # Bleu
        glPopMatrix()

        # Dessiner l'engrenage entraîné
        if hasattr(self.parent, 'module') and hasattr(self.parent, 'teeth_driver') and hasattr(self.parent, 'teeth_driven'):
            center_distance = self.parent.module * (self.parent.teeth_driver + self.parent.teeth_driven) / 2
            glPushMatrix()
            glTranslatef(center_distance, 0, 0)
            ratio = -self.parent.teeth_driver / self.parent.teeth_driven
            glRotatef(self.rotation * ratio, 0, 0, 1)
            self.dessiner_engrenage(self.gear_data_driven, (1.0, 0.0, 0.0))  # Rouge
            glPopMatrix()

    def dessiner_engrenage(self, points, color):
        try:
            glColor3f(*color)
            glBegin(GL_LINE_LOOP)
            for point in points:
                glVertex3f(point[0], point[1], 0.0)
            glEnd()
            
            # Dessiner le cercle primitif
            glBegin(GL_LINE_LOOP)
            for i in range(360):
                angle = np.radians(i)
                radius = np.mean([np.sqrt(p[0]**2 + p[1]**2) for p in points])
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                glVertex3f(x, y, 0.0)
            glEnd()
        except Exception as e:
            print(f"Erreur lors du dessin de l'engrenage: {str(e)}")

    def update_gears(self, driver_points, driven_points):
        print("Mise à jour des données des engrenages")
        self.gear_data_driver = driver_points
        self.gear_data_driven = driven_points
        self.update()

        def update_rotation(self):
            if self.is_animating:
            # Vérifie si on est dans la zone d'arrêt
                if self.stop_angle_start <= self.rotation % 360 <= self.stop_angle_end:
                    if not self.is_in_stop_zone:
                        print(f"Entrée dans la zone d'arrêt: {self.rotation % 360}°")
                        self.is_in_stop_zone = True
                return  # Pas de rotation dans la zone d'arrêt
            
            self.is_in_stop_zone = False
            self.rotation += 1
            self.update()


    def start_animation(self):
        print("Démarrage de l'animation")
        self.is_animating = True

    def pause_animation(self):
        print("Pause de l'animation")
        self.is_animating = False

    def reset_animation(self):
        print("Réinitialisation de l'animation")
        self.is_animating = False
        self.rotation = 0
        self.update()
    def set_stop_angles(self, start_angle, end_angle):
        self.stop_angle_start = start_angle
        self.stop_angle_end = end_angle
        print(f"Angles de repos définis: {start_angle}° - {end_angle}°")

    def dessiner_engrenage(self, points, color):
        try:
            # Dessiner le contour de l'engrenage
            glColor3f(*color)
            glLineWidth(2.0)  # Ligne plus épaisse
            
            # Dessiner les dents
            glBegin(GL_LINE_LOOP)
            for point in points:
                glVertex3f(point[0], point[1], 0.0)
            glEnd()
            
            # Dessiner le cercle primitif
            radius = np.mean([np.sqrt(p[0]**2 + p[1]**2) for p in points])
            glBegin(GL_LINE_LOOP)
            for i in range(360):
                angle = np.radians(i)
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                glVertex3f(x, y, 0.0)
            glEnd()
            
            # Dessiner un point central pour référence
            glPointSize(5.0)
            glBegin(GL_POINTS)
            glVertex3f(0.0, 0.0, 0.0)
            glEnd()
            
        except Exception as e:
            print(f"Erreur lors du dessin de l'engrenage: {str(e)}")


class SequentialGear:
    def __init__(self, module, num_teeth, pressure_angle=20):
        self.module = module
        self.num_teeth = num_teeth
        self.pressure_angle = pressure_angle
        self.calculator = GearCalculator()
        self.parameters = self.calculator.calculate_base_parameters(
            module, num_teeth, pressure_angle
        )
        
        # Points du profil
        self.tooth_points = []
        self.generate_tooth_profile()
        
    def generate_tooth_profile(self):
        """Génère le profil d'une dent"""
        # Paramètres de base
        pd = self.parameters['pitch_diameter']
        bd = self.parameters['base_diameter']
        od = self.parameters['outside_diameter']
        rd = self.parameters['root_diameter']
        
        # Nombre de points pour le profil
        num_points = 20
        
        # Angle de base pour une dent
        tooth_angle = 2 * self.PI / self.num_teeth
        
        # Génération des points pour une dent
        for i in range(num_points):
            t = i / (num_points - 1)
            # Calcul de la courbe développante
            angle = t * tooth_angle / 2
            radius = math.sqrt(bd * bd / 4 + angle * bd * pd)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            self.tooth_points.append((x, y))

class SequentialGearSystem:
    def __init__(self):
        self.driver_gear = None
        self.driven_gear = None
        self.stop_angle_start = 0
        self.stop_angle_end = 0
        self.current_angle = 0
        
    def setup_gears(self, module, driver_teeth, driven_teeth, 
                   stop_start, stop_end):
        """Configure le système d'engrenages séquentiels"""
        self.driver_gear = SequentialGear(module, driver_teeth)
        self.driven_gear = SequentialGear(module, driven_teeth)
        self.stop_angle_start = stop_start
        self.stop_angle_end = stop_end
        
    def calculate_driven_position(self, driver_angle):
        """Calcule la position de l'engrenage entraîné"""
        # Conversion en radians
        angle_rad = math.radians(driver_angle)
        
        # Vérification si nous sommes dans la zone d'arrêt
        if self.stop_angle_start <= driver_angle <= self.stop_angle_end:
            return self.calculate_stop_position(driver_angle)
        
        # Calcul normal du rapport de transmission
        ratio = self.driver_gear.num_teeth / self.driven_gear.num_teeth
        return angle_rad * ratio
        
    def calculate_stop_position(self, driver_angle):
        """Calcule la position pendant la phase d'arrêt"""
        # Position fixe pendant l'arrêt
        if self.stop_angle_start < driver_angle < self.stop_angle_end:
            return self.last_position
            
        # Calcul de la transition progressive
        transition_zone = 10  # degrés
        
        if abs(driver_angle - self.stop_angle_start) < transition_zone:
            # Transition d'entrée
            t = (driver_angle - (self.stop_angle_start - transition_zone)) / transition_zone
            return self.smooth_transition(t, self.normal_position, self.stop_position)
            
        if abs(driver_angle - self.stop_angle_end) < transition_zone:
            # Transition de sortie
            t = (driver_angle - (self.stop_angle_end - transition_zone)) / transition_zone
            return self.smooth_transition(t, self.stop_position, self.normal_position)
            
    def smooth_transition(self, t, start_pos, end_pos):
        """Applique une fonction de lissage pour la transition"""
        # Utilisation d'une courbe de Bézier cubique pour le lissage
        t = max(0, min(1, t))  # Clamp entre 0 et 1
        return start_pos + (end_pos - start_pos) * (3 * t * t - 2 * t * t * t)
        
    def get_tooth_mesh_points(self, is_driver=True):
        """Retourne les points du maillage pour le rendu"""
        gear = self.driver_gear if is_driver else self.driven_gear
        points = []
        
        # Génération des points pour chaque dent
        for i in range(gear.num_teeth):
            angle = 2 * self.PI * i / gear.num_teeth
            for x, y in gear.tooth_points:
                # Rotation des points pour chaque dent
                rx = x * math.cos(angle) - y * math.sin(angle)
                ry = x * math.sin(angle) + y * math.cos(angle)
                points.append((rx, ry))
                
        return points


from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time

class GearRenderer:
    def __init__(self):
        self.display_list = None
        self.texture = None
        
    def create_gear_display_list(self, gear_points, color):
        """Crée une display list OpenGL pour l'engrenage"""
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        
        glColor3f(*color)
        glBegin(GL_TRIANGLE_FAN)
        # Centre de l'engrenage
        glVertex3f(0, 0, 0)
        
        # Dessiner les dents
        for point in gear_points:
            glVertex3f(point[0], point[1], 0)
            
        glEnd()
        glEndList()
        return display_list

class AnimationController:
    def __init__(self):
        self.animation_speed = 1.0
        self.current_angle = 0.0
        self.is_animating = False
        self.last_update = time.time()
        
    def update(self):
        """Met à jour l'animation"""
        if self.is_animating:
            current_time = time.time()
            delta_time = current_time - self.last_update
            self.current_angle += self.animation_speed * delta_time * 60
            self.last_update = current_time
            
            if self.current_angle >= 360:
                self.current_angle -= 360
                
        return self.current_angle

class GearGLWidget(QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.gear_system = None
        self.renderer = GearRenderer()
        self.animation = AnimationController()
        
        # Camera controls
        self.camera_distance = 15.0
        self.camera_rotation_x = 0.0
        self.camera_rotation_y = 0.0
        self.last_pos = QPoint()
        
        # Timer pour l'animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        
    def initializeGL(self):
        glClearColor(0.9, 0.9, 0.9, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        
        # Configuration de la lumière
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w/h, 0.1, 100.0)
        
    def paintGL_view2(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Position de la caméra
        glTranslatef(0, 0, -self.camera_distance)
        glRotatef(self.camera_rotation_x, 1, 0, 0)
        glRotatef(self.camera_rotation_y, 0, 1, 0)
        
        if self.gear_system:
            # Dessin de l'engrenage moteur
            glPushMatrix()
            glRotatef(self.animation.current_angle, 0, 0, 1)
            if self.renderer.display_list:
                glCallList(self.renderer.display_list)
            glPopMatrix()
            
            # Dessin de l'engrenage entraîné
            glPushMatrix()
            # Calcul de la position de l'engrenage entraîné
            driven_angle = self.gear_system.calculate_driven_position(
                self.animation.current_angle
            )
            center_distance = self.calculate_center_distance()
            glTranslatef(center_distance, 0, 0)
            glRotatef(math.degrees(driven_angle), 0, 0, 1)
            if self.renderer.display_list:
                glCallList(self.renderer.display_list + 1)
            glPopMatrix()
            
    def calculate_center_distance(self):
        """Calcule la distance entre les centres des engrenages"""
        if self.gear_system:
            return (self.gear_system.driver_gear.parameters['pitch_diameter'] +
                    self.gear_system.driven_gear.parameters['pitch_diameter']) / 2
        return 0
        
    def update_animation(self):
        """Met à jour l'animation et redessine"""
        if self.animation.is_animating:
            self.animation.update()
            self.update()
            
    def mousePressEvent(self, event):
        self.last_pos = event.pos()
        
    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_pos.x()
        dy = event.y() - self.last_pos.y()
        
        if event.buttons() & Qt.LeftButton:
            self.camera_rotation_y += dx
            self.camera_rotation_x += dy
            self.update()
            
        self.last_pos = event.pos()
        
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.camera_distance -= delta * 0.01
        self.camera_distance = max(5, min(self.camera_distance, 30))
        self.update()
        
    def set_gear_system(self, gear_system):
        """Configure le système d'engrenages à afficher"""
        self.gear_system = gear_system
        
        # Création des display lists pour les engrenages
        driver_points = gear_system.get_tooth_mesh_points(True)
        driven_points = gear_system.get_tooth_mesh_points(False)
        
        self.renderer.display_list = self.renderer.create_gear_display_list(
            driver_points, (0.2, 0.5, 0.8)
        )
        self.renderer.create_gear_display_list(
            driven_points, (0.8, 0.3, 0.2)
        )


# Dans la classe MainWindow, ajouter :
def create_animation_controls(self):
    """Crée les contrôles d'animation"""
    group = QGroupBox("Animation")
    layout = QVBoxLayout()
    
    # Bouton lecture/pause
    self.play_button = QPushButton("Lecture")
    self.play_button.setCheckable(True)
    self.play_button.clicked.connect(self.toggle_animation)
    layout.addWidget(self.play_button)
    
    # Contrôle de vitesse
    speed_layout = QHBoxLayout()
    speed_layout.addWidget(QLabel("Vitesse:"))
    self.speed_slider = QSlider(Qt.Horizontal)
    self.speed_slider.setRange(1, 200)
    self.speed_slider.setValue(100)
    self.speed_slider.valueChanged.connect(self.update_animation_speed)
    speed_layout.addWidget(self.speed_slider)
    layout.addLayout(speed_layout)
    
    group.setLayout(layout)
    return group


        
def calcul_clicked(self):
    print("Début des calculs")
    try:
        # Récupération des valeurs des champs
        module = float(self.module_edit.text())
        nb_dents_1 = int(self.nb_dents_1_edit.text())
        nb_dents_2 = int(self.nb_dents_2_edit.text())
        angle_pression = float(self.angle_pression_edit.text())

        # Effectuer vos calculs ici
        
        # Afficher les résultats
        self.afficher_resultats()
        
        print("Calculs terminés avec succès")
        
    except Exception as e:
        print(f"Erreur lors des calculs : {str(e)}")


    def toggle_animation(self, checked):
        self.gl_widget.animation.is_animating = checked
        
    def update_animation_speed(self, value):
        self.gl_widget.animation.animation_speed = value / 100.0


import json
import os
from datetime import datetime

class ProjectManager(QWidget):
    def __init__(self):
        super().__init__()
        
        # Layout principal qui va contenir les 3 parties
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # =============== PARTIE 1 : CHAMPS DE SAISIE ===============
        input_group = QGroupBox("Paramètres d'entrée")
        input_layout = QGridLayout()
        
        # Vos champs existants
        self.module_label = QLabel("Module (mm) :")
        self.module_edit = QLineEdit()
        self.nb_dents_1_label = QLabel("Nombre de dents roue 1 :")
        self.nb_dents_1_edit = QLineEdit()
        self.nb_dents_2_label = QLabel("Nombre de dents roue 2 :")
        self.nb_dents_2_edit = QLineEdit()
        self.angle_pression_label = QLabel("Angle de pression (°) :")
        self.angle_pression_edit = QLineEdit()

        # Ajout des widgets au layout
        input_layout.addWidget(self.module_label, 0, 0)
        input_layout.addWidget(self.module_edit, 0, 1)
        input_layout.addWidget(self.nb_dents_1_label, 1, 0)
        input_layout.addWidget(self.nb_dents_1_edit, 1, 1)
        input_layout.addWidget(self.nb_dents_2_label, 2, 0)
        input_layout.addWidget(self.nb_dents_2_edit, 2, 1)
        input_layout.addWidget(self.angle_pression_label, 3, 0)
        input_layout.addWidget(self.angle_pression_edit, 3, 1)

        input_group.setLayout(input_layout)
        
        # =============== PARTIE 2 : RÉSULTATS ===============
        results_group = QGroupBox("Résultats")
        results_layout = QVBoxLayout()
        
        # Création des labels pour les résultats
        self.rapport_transmission_label = QLabel("Rapport de transmission : ")
        self.diametre_primitif_1_label = QLabel("Diamètre primitif roue 1 : ")
        self.diametre_primitif_2_label = QLabel("Diamètre primitif roue 2 : ")
        self.diametre_tete_1_label = QLabel("Diamètre de tête roue 1 : ")
        self.diametre_tete_2_label = QLabel("Diamètre de tête roue 2 : ")
        self.diametre_pied_1_label = QLabel("Diamètre de pied roue 1 : ")
        self.diametre_pied_2_label = QLabel("Diamètre de pied roue 2 : ")
        self.entraxe_label = QLabel("Entraxe : ")

        # Ajout des labels au layout des résultats
        results_layout.addWidget(self.rapport_transmission_label)
        results_layout.addWidget(self.diametre_primitif_1_label)
        results_layout.addWidget(self.diametre_primitif_2_label)
        results_layout.addWidget(self.diametre_tete_1_label)
        results_layout.addWidget(self.diametre_tete_2_label)
        results_layout.addWidget(self.diametre_pied_1_label)
        results_layout.addWidget(self.diametre_pied_2_label)
        results_layout.addWidget(self.entraxe_label)

        results_group.setLayout(results_layout)

        # =============== PARTIE 3 : ANIMATION ===============
        animation_group = QGroupBox("Animation")
        animation_layout = QVBoxLayout()
        
        # Votre canvas existant
        self.figure = Figure(figsize=(8, 8))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        animation_layout.addWidget(self.canvas)

        # Boutons de contrôle
        self.play_button = QPushButton("Lecture")
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.toggle_animation)
        animation_layout.addWidget(self.play_button)

        animation_group.setLayout(animation_layout)

        # =============== ASSEMBLAGE FINAL ===============
        # Bouton de calcul
        self.bouton_calcul = QPushButton("Calculer")
        self.bouton_calcul.clicked.connect(self.calcul_clicked)

        # Ajout de toutes les parties au layout principal
        main_layout.addWidget(input_group)
        main_layout.addWidget(self.bouton_calcul)
        main_layout.addWidget(results_group)
        main_layout.addWidget(animation_group)

        # Configuration de la fenêtre
        self.setWindowTitle("Simulation d'engrenages")
        self.setGeometry(100, 100, 800, 1000)
        
        # Attributs de gestion de projet
        self.current_project = None
        self.project_path = None

    def save_project(self, gear_system, filename):
        """Sauvegarde le projet dans un fichier JSON"""
        project_data = {
            'driver_gear': {
                'module': gear_system.driver_gear.module,
                'num_teeth': gear_system.driver_gear.num_teeth,
                'pressure_angle': gear_system.driver_gear.pressure_angle
            },
            'driven_gear': {
                'module': gear_system.driven_gear.module,
                'num_teeth': gear_system.driven_gear.num_teeth,
                'pressure_angle': gear_system.driven_gear.pressure_angle
            },
            'stop_angle_start': gear_system.stop_angle_start,
            'stop_angle_end': gear_system.stop_angle_end,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(project_data, f, indent=4)
            
    def load_project(self, filename):
        """Charge un projet depuis un fichier JSON"""
        with open(filename, 'r') as f:
            project_data = json.load(f)
            
        return project_data


# Ajout des menus dans la classe MainWindow
    def create_menus(self):
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu('Fichier')
        
        new_action = QAction('Nouveau', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction('Ouvrir...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction('Enregistrer', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        export_action = QAction('Exporter STL...', self)
        export_action.triggered.connect(self.export_stl)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Quitter', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
    def new_project(self):
        self.project_manager = ProjectManager()
        self.reset_parameters()
        
    def open_project(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un projet",
            "",
            "Fichiers projet (*.json)"
        )
        if filename:
            try:
                project_data = self.project_manager.load_project(filename)
                self.load_project_data(project_data)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture : {str(e)}")
                
def save_project(self):
    """Sauvegarde du projet"""
    filename, _ = QFileDialog.getSaveFileName(
        self,  # Gardez self car nous sommes dans une classe Qt
        "Enregistrer le projet",
        "",
        "Fichiers projet (*.json)"
    )
    if filename:
        try:
            # Vérifiez que project_manager est bien initialisé dans __init__
            # et que gear_system existe
            ProjectManager.save_project(filename, self.gear_system)  # Utilisation directe de la classe
            self.statusBar().showMessage(f'Projet sauvegardé: {filename}')
            self.is_modified = False
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")

def export_stl(self):
    """Export du modèle en STL"""
    filename, _ = QFileDialog.getSaveFileName(
        self,
        "Exporter en STL",
        "",
        "Fichiers STL (*.stl)"
    )
    if filename:
        try:
            self.export_to_stl(filename)
            self.statusBar().showMessage(f'Modèle exporté en STL: {filename}')
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export : {str(e)}")


# Dépendances
build_exe_options = {
    "packages": ["PyQt5", "numpy", "OpenGL"],
    "includes": ["numpy.core._methods", "numpy.lib.format"],
    "include_files": [
        "icons/",  # Si vous avez des icônes
        "README.txt",
        "LICENSE.txt"
    ],
    "excludes": ["tkinter", "unittest"],
}

# Configuration de base
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Ajout des nouvelles importations
from PyQt5.QtGui import QPainter, QImage, QPdfWriter
from PyQt5.QtPrintSupport import QPrinter
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import dxfwrite
from dxfwrite import DXFEngine as dxf

class AdvancedGearParameters:
    """Classe pour gérer les paramètres avancés des engrenages"""
    def __init__(self):
        self.clearance = 0.25  # Jeu
        self.backlash = 0.0    # Jeu de fonctionnement
        self.fillet_radius = 0.0  # Rayon de raccordement
        self.surface_finish = 'N7'  # État de surface
        self.material = 'Steel'
        self.heat_treatment = None
        self.tolerance_class = 'IT7'
        self.surface_hardness = 0.0
        
class GearVisualizationSettings:
    """Classe pour gérer les paramètres visuels"""
    def __init__(self):
        self.show_pitch_circle = True
        self.show_base_circle = True
        self.show_root_circle = True
        self.show_outside_circle = True
        self.show_tooth_thickness = True
        self.show_pressure_angle = True
        self.show_dimensions = True
        self.show_center_lines = True
        
        # Couleurs personnalisables
        self.colors = {
            'background': (240, 240, 240),
            'gear_body': (200, 200, 200),
            'tooth': (180, 180, 180),
            'pitch_circle': (255, 0, 0),
            'base_circle': (0, 255, 0),
            'root_circle': (0, 0, 255),
            'dimensions': (0, 0, 0),
            'grid': (200, 200, 200)
        }
        
class ExportManager:
    """Classe pour gérer les différents formats d'export"""
    def __init__(self, gear_system, visualization_settings):
        self.gear_system = gear_system
        self.settings = visualization_settings
        
    def export_jpg(self, filename, resolution=(1920, 1080)):
        """Exporte la vue courante en JPEG"""
        image = QImage(resolution[0], resolution[1], QImage.Format_RGB32)
        painter = QPainter(image)
        self.render_gear_system(painter, resolution)
        image.save(filename, "JPEG", quality=100)
        painter.end()
        
    def export_pdf_technical(self, filename):
        """Exporte un PDF technique complet"""
        doc = canvas.Canvas(filename, pagesize=A4)
        
        # En-tête
        doc.setFont("Helvetica-Bold", 16)
        doc.drawString(50, 800, "Documentation Technique - Engrenage Séquentiel")
        
        # Informations générales
        doc.setFont("Helvetica", 12)
        y = 750
        doc.drawString(50, y, f"Module: {self.gear_system.driver_gear.module}")
        doc.drawString(50, y-20, f"Nombre de dents (moteur): {self.gear_system.driver_gear.num_teeth}")
        doc.drawString(50, y-40, f"Nombre de dents (entraîné): {self.gear_system.driven_gear.num_teeth}")
        
        # Paramètres techniques
        y = 650
        doc.setFont("Helvetica-Bold", 14)
        doc.drawString(50, y, "Paramètres techniques")
        
        # Tableaux des dimensions
        self.draw_dimension_table(doc, 550)
        
        # Vue technique
        self.draw_technical_view(doc, 300)
        
        # Notes et spécifications
        self.add_specifications(doc, 200)
        
        doc.save()
        
    def export_dxf(self, filename):
        """Exporte au format DXF"""
        drawing = dxf.drawing(filename)
        
        # Ajout des cercles de référence
        self.add_reference_circles(drawing)
        
        # Ajout du profil des dents
        self.add_tooth_profiles(drawing)
        
        # Ajout des cotations
        self.add_dimensions(drawing)
        
        drawing.save()
        
    def export_technical_package(self, base_filename):
        """Exporte un package technique complet"""
        # Création d'un dossier pour le package
        os.makedirs(f"{base_filename}_package", exist_ok=True)
        base_path = f"{base_filename}_package/"
        
        # Export de tous les formats
        self.export_jpg(f"{base_path}visualization.jpg")
        self.export_pdf_technical(f"{base_path}documentation.pdf")
        self.export_dxf(f"{base_path}technical_drawing.dxf")
        
        # Ajout d'un fichier README
        self.create_readme(base_path)
        
    def create_dimension_diagram(self, ax):
        """Crée un diagramme technique avec cotations"""
        # Dessin du profil de base
        self.draw_gear_profile(ax)
        
        # Ajout des lignes de cote
        self.add_dimension_lines(ax)
        
        # Ajout des textes de cotation
        self.add_dimension_texts(ax)
        
        # Configuration de l'apparence
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.5)
        
class AdvancedGearGLWidget(GearGLWidget):
    """Version améliorée du widget OpenGL"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.visualization_settings = GearVisualizationSettings()
        self.show_grid = True
        self.grid_size = 10
        self.grid_subdivisions = 10
        
    def paintGL_view3(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        super().paintGL()
        
        if self.show_grid:
            self.draw_grid()
            
        if self.visualization_settings.show_center_lines:
            self.draw_center_lines()
            
        if self.visualization_settings.show_dimensions:
            self.draw_dimensions()
            
    def draw_grid(self):
        """Dessine une grille de référence"""
        glBegin(GL_LINES)
        glColor3f(0.8, 0.8, 0.8)
        
        # Lignes horizontales et verticales
        for i in range(-self.grid_size, self.grid_size + 1):
            glVertex3f(i, -self.grid_size, 0)
            glVertex3f(i, self.grid_size, 0)
            glVertex3f(-self.grid_size, i, 0)
            glVertex3f(self.grid_size, i, 0)
            
        glEnd()

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                            QScrollArea, QGroupBox, QFormLayout, QLabel, 
                            QDoubleSpinBox, QSpinBox, QComboBox, QToolBar,
                            QMessageBox)
import math

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import QGLWidget
import sys
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

class GLWidget(QGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.setMinimumSize(300, 300)
        self.rotation = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateRotation)
        self.is_animating = False
        self.animation_speed = 1.0
        self.current_view = 1  # Pour suivre quelle vue est active

def paintGL_view4(self):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -5.0)
    glRotatef(self.rotation, 0.0, 1.0, 0.0)

    """Méthode principale qui appelle la vue appropriée"""
    if self.current_view == 1:
        self.paintGL_view1()
    elif self.current_view == 2:
        self.paintGL_view2()
    elif self.current_view == 3:
        self.paintGL_view3()
    elif self.current_view == 4:
        self.paintGL_view4()
    elif self.current_view == 5:
        self.paintGL_view5()

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLight(GL_LIGHT0, GL_POSITION, [5.0, 5.0, 5.0, 1.0])

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 0.1, 100.0)

    def paintGL_view5(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        
        # Dessiner un cube simple pour tester
        glBegin(GL_QUADS)
        # Face supérieure
        glColor3f(1.0, 0.0, 0.0)  # Rouge
        glVertex3f(1.0, 1.0, -1.0)
        glVertex3f(-1.0, 1.0, -1.0)
        glVertex3f(-1.0, 1.0, 1.0)
        glVertex3f(1.0, 1.0, 1.0)
        
        # Face avant
        glColor3f(0.0, 1.0, 0.0)  # Vert
        glVertex3f(1.0, 1.0, 1.0)
        glVertex3f(-1.0, 1.0, 1.0)
        glVertex3f(-1.0, -1.0, 1.0)
        glVertex3f(1.0, -1.0, 1.0)
        
        # Face droite
        glColor3f(0.0, 0.0, 1.0)  # Bleu
        glVertex3f(1.0, 1.0, -1.0)
        glVertex3f(1.0, 1.0, 1.0)
        glVertex3f(1.0, -1.0, 1.0)
        glVertex3f(1.0, -1.0, -1.0)
        glEnd()

    def updateRotation(self):
        self.rotation += 1.0
        self.update()

    def startAnimation(self):
        if not self.is_animating:
            self.timer.start(16)  # ~60 FPS
            self.is_animating = True

    def stopAnimation(self):
        if self.is_animating:
            self.timer.stop()
            self.is_animating = False

    def toggleAnimation(self):
        if self.is_animating:
            self.stopAnimation()
        else:
            self.startAnimation()

class GearViewer(QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.rotation = 0.0
        
        # Timer pour l'animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(16)  # ~60 FPS
        
    def initializeGL(self):
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        
    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        gluPerspective(45, width/height, 0.1, 100.0)
        
    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslatef(0.0, 0.0, -5.0)
        GL.glRotatef(self.rotation, 0.0, 0.0, 1.0)
        
        self.draw_gear()
        
    def draw_gear(self):
        # Code pour dessiner l'engrenage
        GL.glBegin(GL.GL_LINES)
        GL.glColor3f(1.0, 1.0, 1.0)
        # Dessiner les dents de l'engrenage ici
        GL.glEnd()
        
    def rotate(self):
        self.rotation += 1.0
        self.updateGL()

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                           QFormLayout, QLabel, QDoubleSpinBox, QSpinBox, QComboBox, 
                           QToolBar, QScrollArea, QTabWidget, QAction, QMessageBox)
from PyQt5.QtCore import Qt
import math
from gear_calculator import GearCalculator
from project_manager import ProjectManager
from gl_widget import GLWidget

import os
import yaml
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QFormLayout, QSpinBox, QDoubleSpinBox, QToolBar, QPushButton,
    QAction, QMessageBox, QFileDialog, QStatusBar
)
from PyQt5.QtCore import QTimer
from PyQt5.QtOpenGL import QGLWidget
from project_manager import ProjectManager
from gear_system import GearSystem
from gear_calculator import GearCalculator

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        
        # Initialisation des gestionnaires
        self.project_manager = ProjectManager()
        self.gear_system = GearSystem()
        self.gear_calculator = GearCalculator()
        
        # Initialisation des variables
        self.current_file = None
        self.is_modified = False
        
        # Configuration de la fenêtre
        self.setWindowTitle("Gear Box")
        self.setGeometry(100, 100, 1200, 800)
        
        # Timer pour l'animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        
        # Création de l'interface
        self.init_ui()
        
        # Chargement des paramètres
        self.load_settings()

    def create_menu_bar(self):
        """Création de la barre de menu"""
        menubar = self.menuBar()

        # Menu Fichier
        file_menu = menubar.addMenu('&Fichier')
        
        new_action = QAction(QIcon('icons/new.png'), '&Nouveau', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('Créer un nouveau projet')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        open_action = QAction(QIcon('icons/open.png'), '&Ouvrir', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Ouvrir un projet existant')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction(QIcon('icons/save.png'), '&Sauvegarder', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Sauvegarder le projet')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        export_action = QAction(QIcon('icons/export.png'), '&Exporter STL', self)
        export_action.setStatusTip('Exporter le modèle en STL')
        export_action.triggered.connect(self.export_model)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction(QIcon('icons/exit.png'), '&Quitter', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Quitter l\'application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Edition
        edit_menu = menubar.addMenu('&Edition')
        
        # Menu Affichage
        view_menu = menubar.addMenu('&Affichage')
        
        # Menu Aide
        help_menu = menubar.addMenu('&Aide')

    def create_tool_bar(self):
        """Création de la barre d'outils"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Ajout des actions principales
        new_tool = toolbar.addAction(QIcon('icons/new.png'), 'Nouveau')
        new_tool.triggered.connect(self.new_project)

        open_tool = toolbar.addAction(QIcon('icons/open.png'), 'Ouvrir')
        open_tool.triggered.connect(self.open_project)

        save_tool = toolbar.addAction(QIcon('icons/save.png'), 'Sauvegarder')
        save_tool.triggered.connect(self.save_project)

        toolbar.addSeparator()

        # Outils de visualisation
        view_tool = toolbar.addAction(QIcon('icons/view.png'), 'Vue 3D')
        view_tool.triggered.connect(self.toggle_3d_view)

    def create_status_bar(self):
        """Création de la barre de statut"""
        self.statusBar().showMessage('Prêt')

    def setup_main_widget(self):
        """Configuration du widget principal"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Création et ajout du TabWidget
        self.tab_control = QTabWidget()
        main_layout.addWidget(self.tab_control)
        
        # Création du premier onglet pour les contrôles principaux
        main_tab = QWidget()
        main_tab_layout = QHBoxLayout(main_tab)
        
        # Panneau de contrôle (gauche)
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # Groupe des paramètres de l'engrenage
        gear_params_group = QGroupBox("Paramètres de l'engrenage")
        params_layout = QFormLayout()
        
        # Spinboxes pour les paramètres
        self.module_spin = QDoubleSpinBox()
        self.module_spin.setRange(0.1, 50.0)
        self.module_spin.setValue(1.0)
        self.module_spin.setSingleStep(0.1)
        self.module_spin.valueChanged.connect(self.parameter_changed)
        params_layout.addRow("Module:", self.module_spin)
        
        self.teeth_spin = QSpinBox()
        self.teeth_spin.setRange(5, 200)
        self.teeth_spin.setValue(20)
        self.teeth_spin.valueChanged.connect(self.parameter_changed)
        params_layout.addRow("Nombre de dents:", self.teeth_spin)
        
        self.pressure_angle_spin = QDoubleSpinBox()
        self.pressure_angle_spin.setRange(14.5, 25.0)
        self.pressure_angle_spin.setValue(20.0)
        self.pressure_angle_spin.valueChanged.connect(self.parameter_changed)
        params_layout.addRow("Angle de pression (°):", self.pressure_angle_spin)
        
        gear_params_group.setLayout(params_layout)
        control_layout.addWidget(gear_params_group)
        
        # Vue 3D (droite)
        self.gl_widget = QGLWidget()
        
        # Ajout des widgets au layout de l'onglet principal
        main_tab_layout.addWidget(control_panel, 1)
        main_tab_layout.addWidget(self.gl_widget, 3)
        
        # Ajout de l'onglet principal au TabWidget
        self.tab_control.addTab(main_tab, "Paramètres principaux")
        
        # Ajout d'autres onglets si nécessaire
        settings_tab = QWidget()
        self.tab_control.addTab(settings_tab, "Paramètres avancés")
        
        visualization_tab = QWidget()
        self.tab_control.addTab(visualization_tab, "Visualisation")

    def init_ui(self):
        """Initialisation de l'interface utilisateur"""
        self.create_menu_bar()
        self.create_tool_bar()
        self.setup_main_widget()
        self.create_status_bar()

    def new_project(self):
        """Créer un nouveau projet"""
        if self.is_modified:
            reply = QMessageBox.question(self, 'Nouveau projet',
                "Voulez-vous sauvegarder les modifications?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Yes:
                self.save_project()
            elif reply == QMessageBox.Cancel:
                return
        
        self.project_manager.new_project()
        self.current_file = None
        self.is_modified = False
        self.update_ui()

    def open_project(self):
        """Ouvrir un projet existant"""
        if self.is_modified:
            reply = QMessageBox.question(self, 'Ouvrir projet',
                "Voulez-vous sauvegarder les modifications?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Yes:
                self.save_project()
            elif reply == QMessageBox.Cancel:
                return

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir projet",
            "",
            "Fichiers projet (*.gear);;Tous les fichiers (*.*)"
        )
        
        if filename:
            self.project_manager.load_project(filename)
            self.current_file = filename
            self.is_modified = False
            self.update_ui()

    def save_project(self):
        """Sauvegarder le projet"""
        if self.current_file is None:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder projet",
                "",
                "Fichiers projet (*.gear);;Tous les fichiers (*.*)"
            )
            
            if filename:
                self.current_file = filename
            else:
                return

        self.project_manager.save_project(self.current_file)
        self.is_modified = False
        self.statusBar().showMessage(f'Projet sauvegardé: {self.current_file}')

    def export_model(self):
        """Exporter le modèle"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter STL",
            "",
            "Fichiers STL (*.stl);;Tous les fichiers (*.*)"
        )
        
        if filename:
            self.export_to_stl(filename)

    def parameter_changed(self):
        """Gestion du changement des paramètres"""
        self.is_modified = True
        self.update_gear()

    def update_gear(self):
        """Mise à jour du modèle d'engrenage"""
        try:
            # Mise à jour des calculs
            self.gear_calculator.calculate(
                self.module_spin.value(),
                self.teeth_spin.value(),
                self.pressure_angle_spin.value()
            )
            
            # Mise à jour du modèle 3D
            self.gear_system.update(self.gear_calculator.get_parameters())
            
            # Rafraîchir l'affichage
            self.gl_widget.update()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erreur de calcul",
                f"Erreur lors de la mise à jour : {str(e)}"
            )

    def update_animation(self):
        """Mise à jour de l'animation"""
        if hasattr(self, 'gl_widget'):
            self.gl_widget.update()

    def toggle_3d_view(self):
        """Basculer la vue 3D"""
        # Implémentation de la bascule de vue 3D
        pass

    def load_settings(self):
        """Chargement des paramètres"""
        # Implémentation du chargement des paramètres
        pass

    def export_to_stl(self, filename):
        """Exporte le modèle en STL"""
        try:
            from stl import mesh
            import numpy as np
            
            # Créer les vertices du modèle
            vertices = self.gear_system.generate_vertices()
            faces = self.gear_system.generate_faces()
            
            # Créer le mesh
            gear_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
            for i, face in enumerate(faces):
                for j in range(3):
                    gear_mesh.vectors[i][j] = vertices[face[j]]
            
            # Sauvegarder le fichier STL
            gear_mesh.save(filename)
            self.statusBar().showMessage(f'Modèle exporté en STL: {filename}')
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur d'exportation",
                f"Impossible d'exporter le fichier STL : {str(e)}"
            )

    def update_ui(self):
        """Mise à jour de l'interface utilisateur"""
        # Mettre à jour les contrôles avec les valeurs du projet
        if self.project_manager.current_project:
            params = self.project_manager.current_project.get_parameters()
            self.module_spin.setValue(params.module)
            self.teeth_spin.setValue(params.teeth)
            self.pressure_angle_spin.setValue(params.pressure_angle)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())



class AnalysisModule:
    """Module d'analyse des engrenages"""
    def __init__(self, gear_system):
        self.gear_system = gear_system
        
    def calculate_stress_analysis(self):
        """Calcule les contraintes selon la méthode Lewis"""
        results = {
            'bending_stress': 0.0,
            'contact_stress': 0.0,
            'safety_factor': 0.0,
            'critical_points': []
        }
        # Implémentation des calculs...
        return results
        
    def calculate_kinematics(self):
        """Analyse cinématique du système"""
        return {
            'velocity_ratio': self.gear_system.get_velocity_ratio(),
            'angular_velocities': self.calculate_angular_velocities(),
            'acceleration_profile': self.calculate_acceleration_profile()
        }
        
    def generate_interference_report(self):
        """Vérifie les interférences potentielles"""
        return {
            'has_interference': False,
            'interference_points': [],
            'recommendations': []
        }

class TechnicalDocumentGenerator:
    """Générateur de documentation technique"""
    def __init__(self, gear_system, analysis_results):
        self.gear_system = gear_system
        self.analysis_results = analysis_results
        
    def generate_full_report(self, filename):
        """Génère un rapport technique complet"""
        doc = QPdfWriter(filename)
        painter = QPainter(doc)
        
        self.add_title_page(painter)
        self.add_technical_specifications(painter)
        self.add_analysis_results(painter)
        self.add_drawings(painter)
        self.add_manufacturing_instructions(painter)
        
        painter.end()
        
    def generate_3d_model(self):
        """Génère le modèle 3D pour différents formats"""
        return {
            'stl': self.export_stl(),
            'step': self.export_step(),
            'iges': self.export_iges()
        }

class ExportManagerAdvanced(ExportManager):
    """Version avancée du gestionnaire d'export"""
    def __init__(self, gear_system, visualization_settings):
        super().__init__(gear_system, visualization_settings)
        self.doc_generator = TechnicalDocumentGenerator(gear_system, None)
        
    def export_complete_package(self, base_path):
        """Exporte un package complet avec tous les formats"""
        os.makedirs(base_path, exist_ok=True)
        
        # Documentation
        self.doc_generator.generate_full_report(f"{base_path}/technical_report.pdf")
        
        # Dessins techniques
        self.export_technical_drawings(base_path)
        
        # Modèles 3D
        self.export_3d_models(base_path)
        
        # Animations
        self.export_animations(base_path)
        
        # Fichiers de fabrication
        self.export_manufacturing_files(base_path)

class MeasurementTool:
    """Outil de mesure interactif"""
    def __init__(self, gl_widget):
        self.gl_widget = gl_widget
        self.active = False
        self.start_point = None
        self.end_point = None
        self.measurements = []
        
    def start_measurement(self, point):
        self.start_point = point
        self.active = True
        
    def end_measurement(self, point):
        self.end_point = point
        self.calculate_measurement()
        self.active = False
        
    def calculate_measurement(self):
        if self.start_point and self.end_point:
            distance = np.linalg.norm(
                np.array(self.end_point) - np.array(self.start_point)
            )
            angle = self.calculate_angle()
            self.measurements.append({
                'distance': distance,
                'angle': angle,
                'points': (self.start_point, self.end_point)
            })

class AnimationController:
    """Contrôleur d'animation avancé"""
    def __init__(self, gl_widget):
        self.gl_widget = gl_widget
        self.timeline = QTimeLine(5000)  # 5 secondes par défaut
        self.keyframes = []
        self.current_frame = 0
        
    def add_keyframe(self, angle, position):
        self.keyframes.append({
            'angle': angle,
            'position': position,
            'time': len(self.keyframes) * 1000  # 1 seconde entre chaque keyframe
        })
        
    def start_animation(self):
        self.timeline.start()
        
    def pause_animation(self):
        self.timeline.setPaused(True)
        
    def resume_animation(self):
        self.timeline.setPaused(False)

class GLWidget(QGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.setMinimumSize(300, 300)
        self.rotation = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateRotation)
        self.is_animating = False
        self.animation_speed = 1.0  # Vitesse de rotation par défaut

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLight(GL_LIGHT0, GL_POSITION, [5.0, 5.0, 5.0, 1.0])

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 0.1, 100.0)

    def paintGL(self):  # Renommé de paintGL_view6 à paintGL
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        
        # Dessiner un cube simple pour tester
        glBegin(GL_QUADS)
        # Face supérieure
        glColor3f(1.0, 0.0, 0.0)  # Rouge
        glVertex3f(1.0, 1.0, -1.0)
        glVertex3f(-1.0, 1.0, -1.0)
        glVertex3f(-1.0, 1.0, 1.0)
        glVertex3f(1.0, 1.0, 1.0)
        
        # Face avant
        glColor3f(0.0, 1.0, 0.0)  # Vert
        glVertex3f(1.0, 1.0, 1.0)
        glVertex3f(-1.0, 1.0, 1.0)
        glVertex3f(-1.0, -1.0, 1.0)
        glVertex3f(1.0, -1.0, 1.0)
        
        # Face droite
        glColor3f(0.0, 0.0, 1.0)  # Bleu
        glVertex3f(1.0, 1.0, -1.0)
        glVertex3f(1.0, 1.0, 1.0)
        glVertex3f(1.0, -1.0, 1.0)
        glVertex3f(1.0, -1.0, -1.0)
        glEnd()

    def updateRotation(self):
        self.rotation += 2.0 * self.animation_speed
        if self.rotation >= 360.0:
            self.rotation -= 360.0
        self.updateGL()

    def startAnimation(self):
        if not self.is_animating:
            self.timer.start(16)  # ~60 FPS
            self.is_animating = True

    def stopAnimation(self):
        if self.is_animating:
            self.timer.stop()
            self.is_animating = False

    def setAnimationSpeed(self, speed):
        self.animation_speed = speed

    def toggleAnimation(self):
        if self.is_animating:
            self.stopAnimation()
        else:
            self.startAnimation()


class ModernUIStyles:
    """Définition des styles modernes pour l'interface"""
    MAIN_STYLE = """
        QMainWindow {
            background-color: #2b2b2b;
        }
        QGroupBox {
            background-color: #333333;
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 1em;
            color: #ffffff;
            font-weight: bold;
        }
        QLabel {
            color: #ffffff;
            font-size: 12px;
        }
        QPushButton {
            background-color: #0d47a1;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #1565c0;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
            background: #333333;
        }
        QTabBar::tab {
            background: #424242;
            color: white;
            padding: 8px 20px;
        }
        QTabBar::tab:selected {
            background: #0d47a1;
        }
    """

class HighResolutionDisplay:
    """Gestion de l'affichage haute résolution"""
    def __init__(self):
        self.screen = QApplication.primaryScreen()
        self.dpi = self.screen.physicalDotsPerInch()
        self.scale_factor = self.dpi / 96.0  # Base DPI

    def scale_size(self, size):
        return int(size * self.scale_factor)

class EnhancedMainWindow(MainWindow):
    def __init__(self):
        super().__init__()
        self.display = HighResolutionDisplay()
        self.setup_enhanced_ui()
        self.apply_styles()

    def setup_enhanced_ui(self):
        """Configuration de l'interface améliorée"""
        # Layout principal en trois colonnes
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Panneau de gauche (20% de la largeur)
        left_panel = self.create_parameters_panel()
        layout.addWidget(left_panel, 20)

        # Zone centrale (60% de la largeur)
        central_panel = self.create_visualization_panel()
        layout.addWidget(central_panel, 60)

        # Panneau de droite (20% de la largeur)
        right_panel = self.create_analysis_panel()
        layout.addWidget(right_panel, 20)

    def create_visualization_panel(self):
        """Création du panneau de visualisation central"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Barre d'outils de visualisation
        toolbar = self.create_enhanced_toolbar()
        layout.addWidget(toolbar)

        # Zone de visualisation principale
        viz_container = QWidget()
        viz_layout = QGridLayout(viz_container)

        # Widget OpenGL principal (70% de la hauteur)
        self.gl_widget = AdvancedGearGLWidget(self)
        viz_layout.addWidget(self.gl_widget, 0, 0, 7, 12)

        # Graphiques d'analyse en temps réel (30% de la hauteur)
        self.realtime_plots = self.create_realtime_plots()
        viz_layout.addWidget(self.realtime_plots, 7, 0, 3, 12)

        layout.addWidget(viz_container)

        return panel

    def create_realtime_plots(self):
        """Création des graphiques en temps réel"""
        plots_widget = QWidget()
        layout = QHBoxLayout(plots_widget)

        # Graphique de vitesse
        self.velocity_plot = self.create_plot("Vitesse angulaire", "Temps", "rad/s")
        layout.addWidget(self.velocity_plot)

        # Graphique de couple
        self.torque_plot = self.create_plot("Couple", "Temps", "N·m")
        layout.addWidget(self.torque_plot)

        # Graphique de contraintes
        self.stress_plot = self.create_plot("Contraintes", "Position", "MPa")
        layout.addWidget(self.stress_plot)

        return plots_widget

    def create_plot(self, title, x_label, y_label):
        """Création d'un graphique matplotlib personnalisé"""
        fig = Figure(figsize=(5, 4), dpi=100)
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        ax.set_title(title, color='white')
        ax.set_xlabel(x_label, color='white')
        ax.set_ylabel(y_label, color='white')
        
        # Style sombre pour les graphiques
        ax.set_facecolor('#333333')
        fig.patch.set_facecolor('#333333')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.tick_params(colors='white')
        
        return canvas

    def create_dynamic_simulation_controls(self):
        """Contrôles pour la simulation dynamique"""
        controls = QWidget()
        layout = QHBoxLayout(controls)

        # Contrôle de vitesse
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(50)
        layout.addWidget(QLabel("Vitesse:"))
        layout.addWidget(self.speed_slider)

        # Boutons de contrôle
        self.play_button = QPushButton("?")
        self.pause_button = QPushButton("?")
        self.stop_button = QPushButton("?")
        
        for btn in [self.play_button, self.pause_button, self.stop_button]:
            btn.setFixedSize(40, 40)
            layout.addWidget(btn)

        return controls

    def create_data_display(self):
        """Affichage des données en temps réel"""
        display = QWidget()
        layout = QGridLayout(display)

        # Création des indicateurs de données
        self.data_indicators = {
            'vitesse': self.create_data_indicator("Vitesse", "rad/s"),
            'couple': self.create_data_indicator("Couple", "N·m"),
            'angle': self.create_data_indicator("Angle", "deg"),
            'contrainte': self.create_data_indicator("Contrainte", "MPa")
        }

        # Disposition en grille 2x2
        positions = [(i, j) for i in range(2) for j in range(2)]
        for (key, indicator), (i, j) in zip(self.data_indicators.items(), positions):
            layout.addWidget(indicator, i, j)

        return display

    def create_data_indicator(self, label, unit):
        """Création d'un indicateur de données individuel"""
        indicator = QFrame()
        indicator.setFrameStyle(QFrame.Panel | QFrame.Raised)
        indicator.setStyleSheet("""
            QFrame {
                background-color: #424242;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(indicator)
        
        title = QLabel(label)
        title.setStyleSheet("color: #90caf9; font-size: 14px;")
        layout.addWidget(title)

        value = QLabel("0.00")
        value.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(value)

        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #78909c; font-size: 12px;")
        layout.addWidget(unit_label)

        return indicator

    def update_display(self):
        """Mise à jour des affichages en temps réel"""
        # Mise à jour des graphiques
        self.update_plots()
        
        # Mise à jour des indicateurs
        self.update_indicators()
        
        # Mise à jour de la visualisation 3D
        self.gl_widget.update()

    def update_plots(self):
        """Mise à jour des graphiques en temps réel"""
        for plot in [self.velocity_plot, self.torque_plot, self.stress_plot]:
            plot.draw()


class AnimationEngine:
    """Moteur d'animation avancé pour les engrenages"""
    def __init__(self, gl_widget):
        self.gl_widget = gl_widget
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.fps = 60
        self.time_step = 1000 / self.fps
        
        # États d'animation
        self.current_angle = 0.0
        self.angular_velocity = 0.0
        self.acceleration = 0.0
        self.is_running = False
        
        # Effets visuels
        self.motion_blur = False
        self.smooth_rotation = True
        self.particle_effects = False
        
    def start_animation(self):
        self.animation_timer.start(self.time_step)
        self.is_running = True
        
    def update_animation(self):
        if self.smooth_rotation:
            self.current_angle += self.angular_velocity * self.time_step / 1000
            if self.motion_blur:
                self.apply_motion_blur()
            if self.particle_effects:
                self.update_particles()
        self.gl_widget.update()

class ParticleSystem:
    """Système de particules pour effets visuels"""
    def __init__(self):
        self.particles = []
        self.max_particles = 1000
        
    def emit_particles(self, position, direction, speed):
        if len(self.particles) < self.max_particles:
            particle = {
                'position': position,
                'direction': direction,
                'speed': speed,
                'life': 1.0
            }
            self.particles.append(particle)
            
    def update_particles(self):
        for particle in self.particles[:]:
            particle['life'] -= 0.01
            if particle['life'] <= 0:
                self.particles.remove(particle)

class RealisticRenderer:
    """Rendu réaliste des engrenages"""
    def __init__(self):
        self.shader_program = None
        self.setup_shaders()
        self.textures = self.load_textures()
        self.lighting = self.setup_lighting()
        
    def setup_shaders(self):
        vertex_shader = """
        #version 330
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec3 normal;
        layout(location = 2) in vec2 texCoord;
        
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        
        out vec3 FragPos;
        out vec3 Normal;
        out vec2 TexCoord;
        
        void main() {
            FragPos = vec3(model * vec4(position, 1.0));
            Normal = mat3(transpose(inverse(model))) * normal;
            TexCoord = texCoord;
            gl_Position = projection * view * model * vec4(position, 1.0);
        }
        """
        
        fragment_shader = """
        #version 330
        in vec3 FragPos;
        in vec3 Normal;
        in vec2 TexCoord;
        
        uniform vec3 lightPos;
        uniform vec3 viewPos;
        uniform sampler2D diffuseMap;
        uniform sampler2D normalMap;
        uniform sampler2D metallicMap;
        
        out vec4 FragColor;
        
        void main() {
            // Calculs PBR ici...
        }
        """

class InteractionHandler:
    """Gestionnaire d'interactions avancées"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.drag_mode = False
        self.last_pos = None
        self.selection = None
        self.gesture_recognizer = self.setup_gesture_recognition()
        
    def setup_gesture_recognition(self):
        recognizer = QGestureRecognizer()
        # Configuration des gestes personnalisés
        return recognizer
        
    def handle_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.start_drag(event.pos())
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.pos())
            
    def handle_gesture(self, gesture):
        if isinstance(gesture, QPinchGesture):
            self.handle_pinch(gesture)
        elif isinstance(gesture, QSwipeGesture):
            self.handle_swipe(gesture)

class EnhancedUIControls:
    """Contrôles d'interface utilisateur améliorés"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_enhanced_controls()
        
    def setup_enhanced_controls(self):
        """Configuration des contrôles avancés"""
        # Création du panneau de contrôle flottant
        control_panel = QWidget(self.main_window)
        layout = QVBoxLayout(control_panel)
        
        # Contrôles de visualisation
        viz_controls = self.create_visualization_controls()
        layout.addWidget(viz_controls)
        
        # Contrôles de simulation
        sim_controls = self.create_simulation_controls()
        layout.addWidget(sim_controls)
        
        # Indicateurs en temps réel
        realtime_indicators = self.create_realtime_indicators()
        layout.addWidget(realtime_indicators)
        
    def create_visualization_controls(self):
        """Création des contrôles de visualisation"""
        controls = QGroupBox("Visualisation")
        layout = QGridLayout(controls)
        
        # Boutons de vue rapide
        view_buttons = {
            'front': QPushButton("Face"),
            'top': QPushButton("Dessus"),
            'side': QPushButton("Côté"),
            'iso': QPushButton("Isométrique")
        }
        
        # Style moderne pour les boutons
        for btn in view_buttons.values():
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            
        # Disposition des boutons
        positions = [(i, j) for i in range(2) for j in range(2)]
        for (key, btn), pos in zip(view_buttons.items(), positions):
            layout.addWidget(btn, *pos)
            
        return controls

    def create_realtime_indicators(self):
        """Création des indicateurs en temps réel"""
        indicators = QGroupBox("Mesures en temps réel")
        layout = QVBoxLayout(indicators)
        
        # Création des jauges circulaires
        gauges = {
            'speed': self.create_circular_gauge("Vitesse", 0, 100, "RPM"),
            'torque': self.create_circular_gauge("Couple", 0, 1000, "N·m"),
            'temp': self.create_circular_gauge("Température", 0, 200, "°C")
        }
        
        for gauge in gauges.values():
            layout.addWidget(gauge)
            
        return indicators

    def create_circular_gauge(self, title, min_val, max_val, unit):
        """Création d'une jauge circulaire"""
        gauge = QWidget()
        gauge.setMinimumHeight(150)
        gauge.setMinimumWidth(150)
        
        # Implémentation du dessin de la jauge circulaire
        # avec QPainter et QConicalGradient
        
        return gauge


class GearSystemConfiguration:
    """Gestionnaire de configuration du système d'engrenages"""
    def __init__(self):
        self.config = {
            'gear_parameters': {},
            'visualization_settings': {},
            'analysis_settings': {}
        }

    def save_configuration(self, filepath):
        """Sauvegarde la configuration actuelle"""
        gear_data = {
            'gear_parameters': {
                'module': self.current_module,
                'teeth_numbers': self.teeth_numbers,
                'pressure_angle': self.pressure_angle,
                'gear_positions': self.gear_positions
            },
            'material_properties': {
                'material_type': self.material_type,
                'yield_strength': self.yield_strength,
                'hardness': self.hardness
            }
        }
        with open(filepath, 'w') as f:
            json.dump(gear_data, f, indent=4)

    def load_configuration(self, filepath):
        """Charge une configuration existante"""
        with open(filepath, 'r') as f:
            gear_data = json.load(f)
            return gear_data

class GearSimulation:
    """Simulation basique du mouvement des engrenages"""
    def __init__(self, gear_system):
        self.gear_system = gear_system
        self.rotation_speed = 0
        self.contact_points = []
        
    def update_rotation(self, time_step):
        """Mise à jour de la rotation des engrenages"""
        angular_displacement = self.rotation_speed * time_step
        for gear in self.gear_system.gears:
            gear.rotate(angular_displacement)
        self.update_contact_points()

    def calculate_transmission_ratio(self):
        """Calcul du rapport de transmission"""
        return self.gear_system.gears[1].teeth_number / self.gear_system.gears[0].teeth_number

class BasicAnalysisReport:
    """Génération de rapport d'analyse basique"""
    def __init__(self, gear_system, simulation_results):
        self.gear_system = gear_system
        self.simulation_results = simulation_results

    def generate_basic_report(self):
        """Génère un rapport technique simple"""
        try:
            report = {
                'gear_specifications': {
                    'module': self.gear_system.module,
                    'teeth_numbers': [gear.teeth_number for gear in self.gear_system.gears],
                    'transmission_ratio': self.gear_system.calculate_ratio()
                },
                'performance_data': {
                    'max_speed': self.simulation_results.max_speed,
                    'efficiency': self.simulation_results.efficiency,
                    'contact_ratio': self.simulation_results.contact_ratio
                }
            }
            return report
        except AttributeError as e:
            print(f"Erreur lors de la génération du rapport: {e}")
            return None

# Utilisation :
# gear_system = GearSystem()  # Votre système d'engrenages
# simulation_results = SimulationResults()  # Vos résultats de simulation
# report_generator = BasicAnalysisReport(gear_system, simulation_results)
# report = report_generator.generate_basic_report()

# Classe pour le système d'engrenages
class GearSystem:
    def __init__(self, module, gears):
        self.module = module
        self.gears = gears
    
    def calculate_ratio(self):
        # Calcul du rapport de transmission
        if len(self.gears) >= 2:
            return self.gears[0].teeth_number / self.gears[1].teeth_number
        return 0

# Classe pour les engrenages individuels
class Gear:
    def __init__(self, teeth_number):
        self.teeth_number = teeth_number

# Classe pour les résultats de simulation
class SimulationResults:
    def __init__(self, max_speed, efficiency, contact_ratio):
        self.max_speed = max_speed
        self.efficiency = efficiency
        self.contact_ratio = contact_ratio

# Utilisation :
def main():
    # Création des engrenages
    gear1 = Gear(teeth_number=20)
    gear2 = Gear(teeth_number=40)
    
    # Création du système d'engrenages
    gear_system = GearSystem(module=2.0, gears=[gear1, gear2])
    
    # Création des résultats de simulation
    simulation_results = SimulationResults(
        max_speed=1000,
        efficiency=0.95,
        contact_ratio=1.6
    )
    
    # Création du rapport
    report_generator = BasicAnalysisReport(gear_system, simulation_results)
    report = report_generator.generate_basic_report()
    
    # Affichage du rapport
    print("Rapport d'analyse:")
    print(f"Module: {report['gear_specifications']['module']}")
    print(f"Nombres de dents: {report['gear_specifications']['teeth_numbers']}")
    print(f"Rapport de transmission: {report['gear_specifications']['transmission_ratio']}")
    print(f"Vitesse maximale: {report['performance_data']['max_speed']}")
    print(f"Rendement: {report['performance_data']['efficiency']}")
    print(f"Rapport de conduite: {report['performance_data']['contact_ratio']}")

if __name__ == "__main__":
    main()


class GearVisualizationManager:
    """Gestionnaire de visualisation amélioré"""
    def __init__(self, gl_widget):
        self.gl_widget = gl_widget
        self.view_modes = {
            'normal': self.set_normal_view,
            'wireframe': self.set_wireframe_view,
            'contact_points': self.set_contact_points_view
        }
        
    def set_normal_view(self):
        """Vue normale des engrenages"""
        self.gl_widget.wireframe_mode = False
        self.gl_widget.show_contact_points = False
        
    def set_wireframe_view(self):
        """Vue filaire pour analyse"""
        self.gl_widget.wireframe_mode = True
        
    def set_contact_points_view(self):
        """Affichage des points de contact"""
        self.gl_widget.show_contact_points = True

class GearAnalyzer:
    """Analyseur basique des engrenages"""
    def __init__(self, gear_system):
        self.gear_system = gear_system

    def analyze_basic_parameters(self):
        """Analyse des paramètres de base"""
        return {
            'pitch_diameter': self.calculate_pitch_diameter(),
            'base_circle': self.calculate_base_circle(),
            'contact_ratio': self.calculate_contact_ratio(),
            'center_distance': self.calculate_center_distance()
        }

    def calculate_pitch_diameter(self):
        """Calcul du diamètre primitif"""
        return self.gear_system.module * self.gear_system.gears[0].teeth_number

    def calculate_contact_ratio(self):
        """Calcul du rapport de conduite"""
        # Implémentation du calcul du rapport de conduite
        pass


class GearParameterController:
    """Contrôleur amélioré des paramètres d'engrenages"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_parameter_controls()
        self.validation_active = True

    def setup_parameter_controls(self):
        """Configuration des contrôles de paramètres avec validation"""
        self.controls = {
            'module': QDoubleSpinBox(
                minimum=0.1,
                maximum=50.0,
                decimals=2,
                singleStep=0.5,
                value=1.0,
                valueChanged=self.on_parameter_changed
            ),
            'teeth_number': QSpinBox(
                minimum=5,
                maximum=200,
                singleStep=1,
                value=20,
                valueChanged=self.on_parameter_changed
            ),
            'pressure_angle': QDoubleSpinBox(
                minimum=14.5,
                maximum=25.0,
                decimals=1,
                singleStep=0.5,
                value=20.0,
                valueChanged=self.on_parameter_changed
            )
        }

    def on_parameter_changed(self):
        """Gestion des changements de paramètres avec validation"""
        if self.validation_active:
            try:
                self.validate_parameters()
                self.update_visualization()
                self.main_window.statusBar().showMessage("Paramètres valides", 2000)
            except ValueError as e:
                QMessageBox.warning(self.main_window, "Erreur de paramètre", str(e))
                self.restore_last_valid_parameters()

    def validate_parameters(self):
        """Validation des paramètres critiques"""
        module = self.controls['module'].value()
        teeth = self.controls['teeth_number'].value()
        angle = self.controls['pressure_angle'].value()

        # Vérifications critiques
        if module * teeth < 10:  # Diamètre primitif trop petit
            raise ValueError("Combinaison module/dents invalide")
        if teeth < 17 and angle > 20:  # Risque d'interférence
            raise ValueError("Risque d'interférence - Ajustez les paramètres")

class RealTimeVisualization:
    """Visualisation améliorée en temps réel"""
    def __init__(self, gl_widget):
        self.gl_widget = gl_widget
        self.highlight_critical_points = True
        self.show_pressure_line = True
        self.setup_visual_indicators()

    def setup_visual_indicators(self):
        """Configuration des indicateurs visuels"""
        self.indicators = {
            'contact_point': {'color': (1.0, 0.0, 0.0, 1.0), 'size': 5.0},
            'pitch_point': {'color': (0.0, 1.0, 0.0, 1.0), 'size': 5.0},
            'pressure_line': {'color': (0.0, 0.8, 0.8, 0.5), 'width': 2.0}
        }

    def update_display(self, gear_data):
        """Mise à jour de l'affichage avec points critiques"""
        self.gl_widget.makeCurrent()
        # Mise à jour du rendu principal
        self.draw_gears(gear_data)
        
        if self.highlight_critical_points:
            self.draw_critical_points(gear_data)
        
        if self.show_pressure_line:
            self.draw_pressure_line(gear_data)
            
        self.gl_widget.update()

    def draw_critical_points(self, gear_data):
        """Dessin des points critiques"""
        # Points de contact
        for point in gear_data.contact_points:
            self.draw_point(point, self.indicators['contact_point'])
        
        # Point primitif
        self.draw_point(gear_data.pitch_point, self.indicators['pitch_point'])

    def draw_pressure_line(self, gear_data):
        """Dessin de la ligne de pression"""
        if gear_data.pressure_line:
            start, end = gear_data.pressure_line
            self.draw_line(start, end, self.indicators['pressure_line'])


class GearMotionControlSolutions:
    """Catalogue des solutions d'arrêt et de reprise de mouvement"""
    
    class InternalSolutions:
        """Solutions intégrées dans l'épaisseur des roues"""
        
        @staticmethod
        def get_geneva_mechanism():
            """Mécanisme de Genève (Croix de Malte)"""
            return {
                'name': 'Mécanisme de Genève',
                'description': 'Transformation de rotation continue en rotation intermittente',
                'characteristics': {
                    'precision_stop': 'Très précis',
                    'shock_level': 'Faible à modéré',
                    'complexity': 'Moyenne',
                    'maintenance': 'Faible'
                },
                'applications': [
                    'Indexation précise',
                    'Mouvement séquentiel',
                    'Arrêts positionnés'
                ]
            }

        @staticmethod
        def get_internal_ratchet():
            """Cliquet interne"""
            return {
                'name': 'Cliquet interne',
                'description': 'Système anti-retour avec reprise progressive',
                'characteristics': {
                    'precision_stop': 'Moyenne',
                    'shock_level': 'Faible',
                    'complexity': 'Simple',
                    'maintenance': 'Moyenne'
                },
                'applications': [
                    'Anti-retour',
                    'Reprise progressive',
                    'Sécurité'
                ]
            }

        @staticmethod
        def get_eccentric_cam():
            """Came excentrique intégrée"""
            return {
                'name': 'Came excentrique intégrée',
                'description': 'Arrêt progressif par came intégrée',
                'characteristics': {
                    'precision_stop': 'Haute',
                    'shock_level': 'Très faible',
                    'complexity': 'Moyenne à élevée',
                    'maintenance': 'Faible'
                },
                'applications': [
                    'Arrêt progressif',
                    'Positionnement précis',
                    'Mouvements complexes'
                ]
            }

    class ExternalSolutions:
        """Solutions externes aux roues"""
        
        @staticmethod
        def get_progressive_finger():
            """Doigt progressif avec plot"""
            return {
                'name': 'Doigt progressif',
                'description': 'Système de doigt avec profil étudié et plot récepteur',
                'characteristics': {
                    'precision_stop': 'Bonne',
                    'shock_level': 'Très faible',
                    'profile_types': [
                        'Profil sinusoïdal',
                        'Profil polynomial',
                        'Profil cycloïdal'
                    ],
                    'advantages': [
                        'Reprise progressive',
                        'Réduction des chocs',
                        'Facilité de maintenance'
                    ]
                },
                'design_parameters': {
                    'finger_length': 'Calculé selon vitesse',
                    'contact_angle': '15-30 degrés',
                    'material': 'Acier traité ou composite'
                }
            }

        @staticmethod
        def get_magnetic_damper():
            """Amortisseur magnétique"""
            return {
                'name': 'Amortisseur magnétique',
                'description': 'Système de freinage par courants de Foucault',
                'characteristics': {
                    'precision_stop': 'Moyenne à haute',
                    'shock_level': 'Nul',
                    'complexity': 'Moyenne',
                    'maintenance': 'Très faible'
                },
                'advantages': [
                    'Sans contact',
                    'Usure nulle',
                    'Force réglable'
                ]
            }

    class HybridSolutions:
        """Solutions combinées"""
        
        @staticmethod
        def get_ratchet_damper():
            """Cliquet avec amortissement"""
            return {
                'name': 'Cliquet amorti',
                'description': 'Système combinant cliquet et amortissement',
                'components': {
                    'ratchet': 'Cliquet de précision',
                    'damper': 'Amortisseur hydraulique ou élastomère',
                    'spring': 'Ressort de rappel calibré'
                },
                'characteristics': {
                    'precision_stop': 'Haute',
                    'shock_level': 'Très faible',
                    'complexity': 'Moyenne',
                    'maintenance': 'Périodique'
                }
            }

        @staticmethod
        def get_smart_indexing():
            """Indexage intelligent"""
            return {
                'name': 'Indexage intelligent',
                'description': 'Système combinant détection et actionnement',
                'components': {
                    'sensor': 'Capteur de position',
                    'actuator': 'Frein électromagnétique',
                    'controller': 'Microcontrôleur'
                },
                'characteristics': {
                    'precision_stop': 'Très haute',
                    'shock_level': 'Nul',
                    'complexity': 'Élevée',
                    'maintenance': 'Moyenne'
                }
            }


class ProgressiveMechanicalSolutions:
    """Solutions mécaniques progressives pour contrôle du mouvement"""

    class CurveProfiles:
        """Profils de courbes pour contrôle progressif"""
        
        @staticmethod
        def get_spiral_lock():
            """Système de verrouillage à spirale progressive"""
            return {
                'name': 'Verrou spiralé',
                'profile_type': 'Spirale logarithmique',
                'parameters': {
                    'angle_initial': 15,  # degrés
                    'rayon_base': 10,     # mm
                    'pas_spiral': 1.5,    # coefficient de progression
                    'angle_total': 270    # degrés
                },
                'manufacturing': {
                    '3D_printing': {
                        'resolution_min': 0.1,  # mm
                        'material': 'PETG ou ABS+',
                        'infill': '80-100%',
                        'layer_height': 0.12    # mm
                    },
                    'machining': {
                        'tool_diameter': 3,     # mm
                        'cutting_speed': 120,   # m/min
                        'material': 'Aluminium 7075 ou Delrin'
                    }
                },
                'curve_equation': 'r = a * e^(b*?)'
            }

        @staticmethod
        def get_heart_cam():
            """Came en forme de cœur pour mouvement cyclique doux"""
            return {
                'name': 'Came cœur',
                'profile_type': 'Courbe composée',
                'parameters': {
                    'base_radius': 15,    # mm
                    'lift': 8,            # mm
                    'dwell_angle': 60,    # degrés
                    'transition_angle': 30 # degrés
                },
                'manufacturing': {
                    '3D_printing': {
                        'resolution_min': 0.08, # mm
                        'material': 'PLA+',
                        'infill': '100%',
                        'support': 'Requis pour surplombs'
                    },
                    'machining': {
                        'tool_diameter': 2,     # mm
                        'steps': 0.5,           # mm
                        'material': 'Bronze ou Acétal'
                    }
                }
            }

    class EnvelopingSolutions:
        """Solutions à enveloppe progressive"""
        
        @staticmethod
        def get_hook_release():
            """Crochet à libération progressive"""
            return {
                'name': 'Crochet progressif',
                'profile_type': 'Courbe de Bézier composite',
                'components': {
                    'hook_profile': {
                        'entry_angle': 25,      # degrés
                        'holding_radius': 12,   # mm
                        'release_curve': 'Polynomiale 3ème degré',
                        'thickness': 4          # mm
                    },
                    'receptor': {
                        'pin_diameter': 6,      # mm
                        'surface_finish': 'Poli',
                        'material': 'Acier trempé ou Bronze'
                    }
                },
                'manufacturing': {
                    '3D_printing': {
                        'orientation': 'À plat',
                        'material': 'PETG renforcé',
                        'layer_height': 0.16,   # mm
                        'perimeters': 4
                    },
                    'machining': {
                        'method': 'EDM fil ou fraisage 5 axes',
                        'precision': 0.02       # mm
                    }
                }
            }

        @staticmethod
        def get_sliding_wedge():
            """Coin coulissant à engagement progressif"""
            return {
                'name': 'Coin progressif',
                'profile_type': 'Rampe polynomiale',
                'parameters': {
                    'entry_angle': 12,    # degrés
                    'exit_angle': 18,     # degrés
                    'length': 30,         # mm
                    'width': 8            # mm
                },
                'curve_characteristics': {
                    'entry': 'Courbe douce cubique',
                    'holding': 'Section plane',
                    'release': 'Courbe exponentielle'
                },
                'manufacturing': {
                    '3D_printing': {
                        'material': 'ABS renforcé fibre',
                        'layer_height': 0.12,
                        'orientation': 'Verticale'
                    },
                    'machining': {
                        'material': 'Aluminium anodisé dur',
                        'surface_finish': 'Ra 0.8'
                    }
                }
            }

    class CompoundMechanisms:
        """Mécanismes composés pour contrôle avancé"""
        
        @staticmethod
        def get_double_curve_lock():
            """Système à double courbe pour verrouillage/déverrouillage progressif"""
            return {
                'name': 'Verrou à double courbe',
                'mechanism_type': 'Courbes conjuguées',
                'profiles': {
                    'primary_curve': {
                        'type': 'Spirale d\'Archimède modifiée',
                        'angle_total': 180,     # degrés
                        'progression': 1.2      # coefficient
                    },
                    'secondary_curve': {
                        'type': 'Cycloïde raccourcie',
                        'amplitude': 6,         # mm
                        'période': 90           # degrés
                    }
                },
                'interaction': {
                    'engagement_sequence': [
                        'Approche douce',
                        'Verrouillage progressif',
                        'Maintien stable',
                        'Libération contrôlée'
                    ],
                    'timing': {
                        'engagement': 45,       # degrés
                        'holding': 90,          # degrés
                        'release': 45           # degrés
                    }
                },
                'manufacturing': {
                    '3D_printing': {
                        'material': 'Nylon renforcé',
                        'precision': 0.1,       # mm
                        'post_processing': 'Polissage mécanique'
                    },
                    'machining': {
                        'method': 'Fraisage CNC',
                        'material': 'Acétal ou Bronze',
                        'finishing': 'Rectification'
                    }
                }
            }


class AdvancedMechanicalSolutions:
    """Solutions mécaniques avancées et combinées"""

    class InnovativeSolutions:
        """Solutions émergentes et optimisées"""
        
        @staticmethod
        def get_wave_profile_lock():
            """Système de verrouillage à profil ondulé adaptatif"""
            return {
                'name': 'Verrou à onde adaptative',
                'profile_type': 'Multi-sinusoïdal composite',
                'parameters': {
                    'base_wave': {
                        'amplitude': [3, 2, 1],  # mm (décroissant)
                        'frequency': [2, 4, 8],  # cycles/révolution
                        'phase_shift': 30        # degrés
                    },
                    'engagement_depth': 4.5,     # mm
                    'progressive_ratio': 1.2     # coefficient d'amortissement
                },
                'advantages': [
                    'Auto-centrage',
                    'Amortissement progressif',
                    'Distribution des forces'
                ],
                'manufacturing': {
                    '3D_printing': {
                        'material': 'TPU/PETG composite',
                        'layer_height': 0.08,
                        'orientation': 'Radiale'
                    }
                }
            }

        @staticmethod
        def get_flex_grip_mechanism():
            """Mécanisme à griffes flexibles"""
            return {
                'name': 'Griffes flexibles',
                'mechanism_type': 'Lames élastiques courbes',
                'design': {
                    'fingers': {
                        'count': 6,
                        'length': 15,           # mm
                        'thickness': [0.8, 1.2],# mm (variable)
                        'curve_radius': 40      # mm
                    },
                    'flex_characteristics': {
                        'max_deflection': 2,    # mm
                        'spring_back': 0.5      # mm
                    }
                },
                'manufacturing': {
                    'material': 'PLA-CF ou PETG-CF',
                    'print_settings': {
                        'layer_height': 0.12,
                        'wall_thickness': 1.2,
                        'infill_pattern': 'Triangular'
                    }
                }
            }

    class CombinedSolutions:
        """Gestionnaire de combinaisons de mécanismes"""
        
        def __init__(self):
            self.compatible_combinations = {
                'edge_face': self._get_edge_face_combinations(),
                'dual_edge': self._get_dual_edge_combinations(),
                'face_face': self._get_face_face_combinations()
            }

        def _get_edge_face_combinations(self):
            """Combinaisons tranche/face des roues"""
            return {
                'spiral_wave': {
                    'edge_mechanism': 'spiral_lock',
                    'face_mechanism': 'wave_profile',
                    'sync_parameters': {
                        'phase_relationship': 90,    # degrés
                        'timing_ratio': 2,          # rapport de synchronisation
                        'clearance': 0.3            # mm
                    },
                    'interaction_points': [
                        {'angle': 0, 'action': 'primary_lock'},
                        {'angle': 45, 'action': 'secondary_engage'},
                        {'angle': 90, 'action': 'full_lock'}
                    ]
                },
                'heart_flex': {
                    'edge_mechanism': 'heart_cam',
                    'face_mechanism': 'flex_grip',
                    'sync_parameters': {
                        'engagement_sequence': [
                            'cam_lift',
                            'grip_close',
                            'hold_position',
                            'sequential_release'
                        ],
                        'timing_diagram': {
                            0: 'start_cam',
                            45: 'grip_initiate',
                            90: 'full_engage',
                            135: 'start_release'
                        }
                    }
                }
            }

        def generate_combined_solution(self, primary_mech, secondary_mech):
            """Générateur de solution combinée"""
            return {
                'combination_type': self._determine_combination_type(primary_mech, secondary_mech),
                'primary_mechanism': primary_mech,
                'secondary_mechanism': secondary_mech,
                'interface_requirements': self._calculate_interface_requirements(
                    primary_mech, secondary_mech
                ),
                'synchronization': self._generate_sync_profile(
                    primary_mech, secondary_mech
                ),
                'manufacturing_constraints': self._get_manufacturing_constraints(
                    primary_mech, secondary_mech
                )
            }

    class MultiFaceMechanism:
        """Mécanisme utilisant plusieurs faces de la roue"""
        
        @staticmethod
        def get_distributed_lock():
            """Système de verrouillage distribué"""
            return {
                'name': 'Verrou distribué',
                'components': {
                    'edge': {
                        'mechanism': 'spiral_lock',
                        'position': 'peripheral',
                        'action': 'primary_control'
                    },
                    'face_1': {
                        'mechanism': 'flex_grip',
                        'position': 'lateral_1',
                        'action': 'secondary_control'
                    },
                    'face_2': {
                        'mechanism': 'wave_profile',
                        'position': 'lateral_2',
                        'action': 'stabilization'
                    }
                },
                'synchronization': {
                    'sequence': [
                        {'phase': 0, 'action': 'edge_engage'},
                        {'phase': 30, 'action': 'face1_grip'},
                        {'phase': 60, 'action': 'face2_stabilize'},
                        {'phase': 90, 'action': 'full_lock'}
                    ],
                    'release_sequence': 'reverse'
                },
                'manufacturing': {
                    'assembly_method': 'Modular',
                    'alignment_features': 'Keyed interfaces',
                    'material_combinations': [
                        {'edge': 'PETG', 'faces': 'TPU'},
                        {'edge': 'PLA', 'faces': 'PETG'}
                    ]
                }
            }


class SolutionsCatalog:
    """Catalogue illustré des solutions mécaniques"""

    def generate_catalog_entry(self, solution_name: str, illustration: str, details: dict) -> dict:
        """
        Format standard pour chaque entrée du catalogue
        ----------------------------------------------
        [Représentation 3D oblique]
           ?     ?
            \ ?  |
             •   ?
        ----------------------------------------------
        Nom : {solution_name}
        Type : {type}
        Description : {description}
        Caractéristiques principales : {specs}
        Avantages/Inconvénients : {pros_cons}
        Notes de fabrication : {manufacturing_notes}
        """
        return {
            "name": solution_name,
            "illustration": illustration,
            "details": details
        }

    class EdgeSolutions:
        """Solutions sur la tranche"""
        
        @staticmethod
        def spiral_lock_catalog() -> dict:
            return {
                'name': 'Verrou Spiralé Progressif',
                'illustration': """
                    ? Z      ? Vue isométrique
                    ?     ?
                    ?   ?   [Représentation du profil spiralé]
                    ????????? X    
                      Y      
                    
                    Détails:
                    A - Entrée progressive (?=15°)
                    B - Zone de maintien
                    C - Sortie contrôlée
                """,
                'specifications': {
                    'angle_travail': '270°',
                    'profondeur': '8-12mm', 
                    'matériaux': 'PETG/PLA renforcé'
                },
                'manufacturing_notes': 'Impression 3D : orientation verticale recommandée'
            }


    class FaceSolutions:
        """Solutions sur les faces latérales"""
        
        @staticmethod
        def wave_grip_catalog():
            return {
                'name': 'Préhenseur à Onde',
                'illustration': """
                    ?     ?  [Vue en coupe]
                     \  ?    ~~~~~~~~
                      ?      | A | B |
                     ?  \    ~~~~~~~~
                    ?     ?  
                    
                    Sections:
                    A - Profil ondulé
                    B - Zone de contact
                    C - Rampe de dégagement
                    """,
                'specs': {
                    'ondulations': '3-5 par quadrant',
                    'profondeur': '2-3mm'
                }
            }

    class HybridSolutions:
        """Solutions combinées"""
        
        @staticmethod
        def edge_face_combo_catalog():
            return {
                'name': 'Système Hybride Tranche-Face',
                'illustration': """
                    ? Z     ?Y
                    ?    ?
                    ?  ?     [Vue éclatée]
                    ????????? X
                    
                    ????????????????
                    ? Vue composée ?
                    ????????????????
                    1 - Mécanisme de tranche
                    2 - Système facial
                    3 - Zone d'interaction
                    """,
                'interaction_notes': 'Synchronisation à 90° entre mécanismes'
            }

def display_full_catalog():
    """
    Affiche le catalogue complet avec navigation
    ------------------------------------------
    1. Solutions de Tranche
       1.1 Verrou Spiralé
       1.2 Came Progressive
       ...
    
    2. Solutions de Face
       2.1 Préhenseur à Onde
       2.2 Griffes Flexibles
       ...
    
    3. Solutions Hybrides
       3.1 Combo Tranche-Face
       3.2 Système Multi-faces
       ...
    """
    pass


from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import os

# Configuration du logging
logging.basicConfig(
    filename='mechanical_solutions.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@dataclass
class MechanicalSolution:
    """Structure de données sécurisée pour les solutions mécaniques"""
    id: str
    name: str
    category: str
    description: str
    specifications: Dict
    manufacturing: Dict
    illustration: str
    version: float = 1.0

class SolutionValidator:
    """Validateur pour les solutions mécaniques"""
    
    @staticmethod
    def validate_solution(solution: MechanicalSolution) -> bool:
        """Vérifie la validité d'une solution"""
        try:
            required_fields = ['id', 'name', 'category', 'description', 
                             'specifications', 'manufacturing']
            
            for field in required_fields:
                if not hasattr(solution, field) or getattr(solution, field) is None:
                    logging.error(f"Champ requis manquant: {field}")
                    return False
                    
            return True
        except Exception as e:
            logging.error(f"Erreur de validation: {str(e)}")
            return False

class SolutionDatabase:
    """Gestionnaire de base de données des solutions"""
    
    def __init__(self, database_path: str = "solutions_db.json"):
        self.database_path = Path(database_path)
        self.solutions: Dict[str, MechanicalSolution] = {}
        self._load_database()

    def _load_database(self) -> None:
        """Charge la base de données depuis le fichier"""
        try:
            if self.database_path.exists():
                with open(self.database_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.solutions = {
                        k: MechanicalSolution(**v) for k, v in data.items()
                    }
                logging.info("Base de données chargée avec succès")
        except Exception as e:
            logging.error(f"Erreur de chargement de la base: {str(e)}")
            self.solutions = {}

    def _save_database(self) -> None:
        """Sauvegarde la base de données"""
        try:
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump({k: vars(v) for k, v in self.solutions.items()}, 
                         f, indent=4)
            logging.info("Base de données sauvegardée avec succès")
        except Exception as e:
            logging.error(f"Erreur de sauvegarde: {str(e)}")
            raise

class MechanicalSolutionsLibrary:
    """Gestionnaire principal de la bibliothèque"""
    
    def __init__(self):
        self.db = SolutionDatabase()
        self.validator = SolutionValidator()
        
    def add_solution(self, solution: MechanicalSolution) -> bool:
        """Ajoute une nouvelle solution à la bibliothèque"""
        try:
            if self.validator.validate_solution(solution):
                self.db.solutions[solution.id] = solution
                self.db._save_database()
                logging.info(f"Solution ajoutée: {solution.id}")
                return True
            return False
        except Exception as e:
            logging.error(f"Erreur d'ajout de solution: {str(e)}")
            return False

    def get_solution(self, solution_id: str) -> Optional[MechanicalSolution]:
        """Récupère une solution par son ID"""
        return self.db.solutions.get(solution_id)

    def list_solutions(self, category: Optional[str] = None) -> List[MechanicalSolution]:
        """Liste les solutions, optionnellement filtrées par catégorie"""
        try:
            if category:
                return [s for s in self.db.solutions.values() 
                       if s.category == category]
            return list(self.db.solutions.values())
        except Exception as e:
            logging.error(f"Erreur de listage: {str(e)}")
            return []

class SolutionCatalogUI:
    """Interface utilisateur du catalogue"""
    
    def __init__(self, library: MechanicalSolutionsLibrary):
        self.library = library

    def display_catalog(self) -> None:
        """Affiche le catalogue complet"""
        try:
            print("\n=== Catalogue des Solutions Mécaniques ===\n")
            categories = set(s.category for s in self.library.list_solutions())
            
            for category in sorted(categories):
                print(f"\n{category.upper()}:")
                solutions = self.library.list_solutions(category)
                for solution in solutions:
                    print(f"\n  - {solution.name}")
                    print(f"    {solution.description[:100]}...")
        except Exception as e:
            logging.error(f"Erreur d'affichage: {str(e)}")
            print("Erreur d'affichage du catalogue")

class SolutionContributor:
    """Interface pour l'ajout de nouvelles solutions"""
    
    def __init__(self, library: MechanicalSolutionsLibrary):
        self.library = library

    def contribute_solution(self, solution_data: Dict) -> bool:
        """Ajoute une nouvelle solution à la bibliothèque"""
        try:
            solution = MechanicalSolution(**solution_data)
            return self.library.add_solution(solution)
        except Exception as e:
            logging.error(f"Erreur de contribution: {str(e)}")
            return False

def main():
    """Point d'entrée principal du programme"""
    try:
        # Initialisation
        library = MechanicalSolutionsLibrary()
        catalog_ui = SolutionCatalogUI(library)
        contributor = SolutionContributor(library)

        # Menu principal
        while True:
            print("\n=== Menu Principal ===")
            print("1. Afficher le catalogue")
            print("2. Ajouter une solution")
            print("3. Quitter")
            
            choice = input("\nChoix: ").strip()
            
            if choice == "1":
                catalog_ui.display_catalog()
            elif choice == "2":
                # Interface d'ajout de solution
                pass
            elif choice == "3":
                break
            else:
                print("Choix invalide")

    except Exception as e:
        logging.critical(f"Erreur critique: {str(e)}")
        print("Une erreur critique est survenue. Consultez les logs pour plus de détails.")

if __name__ == "__main__":
    main()


# Interface graphique avec tkinter (natif Windows) et customtkinter pour un look moderne
import tkinter as tk
from customtkinter import *
import vtk  # Pour la visualisation 3D
from tkinter import ttk
import sqlite3  # Pour une base de données plus robuste
import yaml  # Pour l'import/export

import customtkinter as ctk

class ModernGUI(ctk.CTk):
    """Interface graphique moderne"""
    
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre principale
        self.title("Catalogue Solutions Mécaniques")
        self.geometry("1200x800")
        
        # Style moderne
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Organisation en onglets
# Remplacer ctk.CTkTabview par QTabWidget
from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout

self.tab_control = QTabWidget(self)
self.tab_control.setStyleSheet("QTabWidget::pane { border: 1px solid #444; }")  # Style optionnel

# Création des onglets avec QWidget
self.catalog_tab = QWidget()
self.catalog_tab.setLayout(QVBoxLayout())

self.viewer_tab = QWidget()
self.viewer_tab.setLayout(QVBoxLayout())

self.search_tab = QWidget()
self.search_tab.setLayout(QVBoxLayout())

self.import_export_tab = QWidget()
self.import_export_tab.setLayout(QVBoxLayout())

# Ajout des onglets au QTabWidget
self.tab_control.addTab(self.catalog_tab, "Catalogue")
self.tab_control.addTab(self.viewer_tab, "Visualisation 3D")
self.tab_control.addTab(self.search_tab, "Recherche")
self.tab_control.addTab(self.import_export_tab, "Import/Export")

# Au lieu de pack, utilisez le système de layout de Qt
layout = QVBoxLayout(self)
layout.addWidget(self.tab_control)
self.setLayout(layout)

# Initialisation du calculateur d'engrenages
self.gear_calculator = GearCalculator(parent=self.catalog_tab)
self.catalog_tab.layout().addWidget(self.gear_calculator)

# Setup des autres fonctionnalités
self._setup_3d_viewer()
self._setup_import_export()

def _setup_3d_viewer(self):
        """Configuration de l'onglet visualisation 3D"""
        viewer_frame = ctk.CTkFrame(self.viewer_tab)
        viewer_frame.pack(padx=10, pady=10, fill="both", expand=True)

def _setup_import_export(self):
        """Configuration de l'onglet import/export"""
        import_export_frame = ctk.CTkFrame(self.import_export_tab)
        import_export_frame.pack(padx=10, pady=10, fill="both", expand=True)

class VersionControl:
    """Gestionnaire de versions des solutions"""
    
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.setup_database()
    
    def setup_database(self):
        """Création du schéma de base de données"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS solution_versions (
                    id INTEGER PRIMARY KEY,
                    solution_id TEXT,
                    version_number REAL,
                    changes TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    data BLOB
                )
            """)
    
    def create_version(self, solution_id: str, data: dict, changes: str):
        """Crée une nouvelle version d'une solution"""
        try:
            current_version = self.get_latest_version(solution_id)
            new_version = current_version + 0.1
            
            with self.conn:
                self.conn.execute("""
                    INSERT INTO solution_versions 
                    (solution_id, version_number, changes, data)
                    VALUES (?, ?, ?, ?)
                """, (solution_id, new_version, changes, str(data)))
            
            return True
        except Exception as e:
            logging.error(f"Erreur de versioning: {str(e)}")
            return False

class ImportExportManager:
    """Gestionnaire d'import/export"""
    
    @staticmethod
    def export_solution(solution: MechanicalSolution, format: str = "yaml"):
        """Exporte une solution dans différents formats"""
        try:
            data = vars(solution)
            
            if format == "yaml":
                return yaml.dump(data, default_flow_style=False)
            elif format == "json":
                return json.dumps(data, indent=4)
            else:
                raise ValueError(f"Format non supporté: {format}")
                
        except Exception as e:
            logging.error(f"Erreur d'export: {str(e)}")
            return None

    @staticmethod
    def import_solution(data: str, format: str = "yaml") -> Optional[MechanicalSolution]:
        """Importe une solution depuis différents formats"""
        try:
            if format == "yaml":
                solution_data = yaml.safe_load(data)
            elif format == "json":
                solution_data = json.loads(data)
            else:
                raise ValueError(f"Format non supporté: {format}")
                
            return MechanicalSolution(**solution_data)
            
        except Exception as e:
            logging.error(f"Erreur d'import: {str(e)}")
            return None

class SearchEngine:
    """Moteur de recherche avancé"""
    
    def __init__(self, library: MechanicalSolutionsLibrary):
        self.library = library
        self.index = self._build_search_index()
    
    def _build_search_index(self):
        """Construit un index de recherche"""
        index = {}
        for solution in self.library.list_solutions():
            # Indexation du texte
            text = f"{solution.name} {solution.description}"
            words = set(text.lower().split())
            
            # Indexation des tags
            tags = solution.specifications.get('tags', [])
            
            # Stockage dans l'index
            index[solution.id] = {
                'words': words,
                'tags': set(tags),
                'solution': solution
            }
        return index
    
    def search(self, query: str, tags: List[str] = None) -> List[MechanicalSolution]:
        """Recherche des solutions"""
        try:
            query_words = set(query.lower().split())
            results = []
            
            for solution_id, data in self.index.items():
                # Score basé sur les correspondances de mots
                word_matches = len(query_words & data['words'])
                
                # Score basé sur les tags
                tag_matches = 0
                if tags:
                    tag_matches = len(set(tags) & data['tags'])
                
                # Score total
                score = word_matches + (tag_matches * 2)
                
                if score > 0:
                    results.append((score, data['solution']))
            
            # Tri par score décroissant
            results.sort(reverse=True, key=lambda x: x[0])
            return [r[1] for r in results]
            
        except Exception as e:
            logging.error(f"Erreur de recherche: {str(e)}")
            return []

def main():
    """Point d'entrée principal avec interface graphique"""
    app = ModernGUI()
    app.mainloop()

if __name__ == "__main__":
    main()

# Ajout du système d'info-bulles
from tkinter import messagebox

class ToolTipManager:
    """Gestionnaire d'info-bulles"""
    
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.id = None
        self.x = self.y = 0

    def show_tip(self, text):
        """Affiche l'info-bulle"""
        if self.tip_window or not text:
            return
            
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack()

    def hide_tip(self):
        """Cache l'info-bulle"""
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# Dictionnaire des info-bulles
TOOLTIPS = {
    "module": "Le module est le rapport entre le diamètre primitif et le nombre de dents",
    "angle_pression": "Angle entre la ligne d'action et la tangente au cercle primitif",
    "nombre_dents": "Nombre total de dents de l'engrenage",
    "largeur": "Largeur de la denture",
    "qualite": "Qualité de fabrication selon normes ISO",
    "materiau": "Matériau de l'engrenage (acier, bronze, plastique...)",
    "traitement": "Traitement thermique ou de surface",
    "lubrification": "Type et méthode de lubrification recommandée"
}


# Guide Rapide d'Utilisation - Catalogue Solutions Mécaniques

## 1. Démarrage
#- Double-cliquer Catalogue Mecanique.exe
#- Attendez le chargement de l'interface

## 2. Navigation Principale
#- Catalogue : Base de donnees des solutions
#- Visualisation : Vue "3D" des pieces
#- Recherche : Recherche par critères
#- Gestion : Import/Export des donnees

## 3. Utilisation du Catalogue
### Consultation
#1. Sélectionnez une categorie
#2. Parcourez les solutions
#3. Cliquez pour les details

### Ajout d'une solution
#1. Bouton "+" en haut
#2. Remplissez les champs obligatoires (*)
#3. Ajoutez documentation/modèles
#4. Validez

## 4. Calculs et Paramétrage
### Engrenages
#1. Entrez les paramètres de base
#2. Utilisez les assistants de calcul
#3. Vérifiez les résultats
#4. Exportez les données

### Visualisation
#- Rotation : Clic gauche + déplacer
#- Zoom : Molette souris
#- Déplacement : Clic droit + déplacer

## 5. Export/Import
### Exporter
#1. Sélectionnez les éléments
#2. Choisissez le format
#3. Définissez destination
#4. Validez

#### Importer
#1. Sélectionnez source
#2. Vérifiez compatibilité
#3. Validez importation

## 6. Aide et Support
#- F1 : Aide contextuelle
#- ? : Info-bulles
#Menu Aide : Documentation complète



import tkinter as tk
from tkinter import ttk, messagebox
import math
import json
from tkinter import filedialog
import os

import customtkinter as ctk
from customtkinter import *
import math
import json
from tkinter import messagebox, filedialog
import ttk

import customtkinter as ctk
from math import pi, cos, radians

class ModernGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Modern LogicielEngrenage")
        self.geometry("800x600")
        
        # Créer les onglets
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(expand=True, fill="both")
        
        # Ajouter les onglets
        self.tab1 = self.tabview.add("Calculs de base")
        self.tab2 = self.tabview.add("Catalogue")
        
        # Initialiser le calculateur d'engrenages
        self.gear_calculator = GearCalculator(self.tab1, self.tab2)

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import json
import math

class LogicielEngrenage:
    def __init__(self, catalog_tab, search_tab):
        self.tab1 = catalog_tab
        self.tab2 = search_tab
        self.catalog = self.load_default_catalog()
        
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
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Création des champs d'entrée
        ctk.CTkLabel(input_frame, text="Module (mm):").grid(row=0, column=0, padx=5, pady=5)
        self.module_entry = ctk.CTkEntry(input_frame)
        self.module_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Nombre de dents:").grid(row=1, column=0, padx=5, pady=5)
        self.teeth_entry = ctk.CTkEntry(input_frame)
        self.teeth_entry.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Angle de pression (°):").grid(row=2, column=0, padx=5, pady=5)
        self.pressure_angle_entry = ctk.CTkEntry(input_frame)
        self.pressure_angle_entry.grid(row=2, column=1, padx=5, pady=5)
        self.pressure_angle_entry.insert(0, "20")

        # Bouton de calcul
        calculate_button = ctk.CTkButton(input_frame, text="Calculer", command=self.calculate)
        calculate_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Frame pour les résultats
        results_frame = ctk.CTkFrame(self.tab1)
        results_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.results_text = ctk.CTkTextbox(results_frame, height=200, width=400)
        self.results_text.grid(row=0, column=0, padx=5, pady=5)

    def setup_catalog_tab(self):
        # Frame pour le catalogue
        catalog_frame = ctk.CTkFrame(self.tab2)
        catalog_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Treeview pour afficher le catalogue
        self.tree = ttk.Treeview(catalog_frame, columns=("Module", "Dents", "Angle"), show="headings")
        self.tree.heading("Module", text="Module")
        self.tree.heading("Dents", text="Nombre de dents")
        self.tree.heading("Angle", text="Angle de pression")
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Boutons pour le catalogue
        button_frame = ctk.CTkFrame(self.tab2)
        button_frame.grid(row=1, column=0, pady=5)

        ctk.CTkButton(button_frame, text="Sauvegarder", command=self.save_catalog).grid(row=0, column=0, padx=5)
        ctk.CTkButton(button_frame, text="Charger", command=self.load_catalog).grid(row=0, column=1, padx=5)

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
    app = QApplication(sys.argv)
    calculator = GearCalculator()
    calculator.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
