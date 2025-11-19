import os
from pywps import Process, ComplexInput, ComplexOutput, Format
import json
from shapely.geometry import shape
import numpy as np
from math import degrees, atan2

DEM_PATH = "finale_optimized.tif"

class SolarExposure(Process):
    def __init__(self):
        inputs = [ComplexInput('line', 'Ligne', supported_formats=[Format('application/vnd.geo+json')])]
        outputs = [ComplexOutput('result', 'Result', supported_formats=[Format('application/json')])]
        
        super(SolarExposure, self).__init__(
            self._handler,
            identifier='solar_exposure',
            title='Solar',
            version='1.0',
            inputs=inputs,
            outputs=outputs
        )

    def calculate_orientation(self, coords):
        """Calcule l'orientation dominante de la ligne"""
        if len(coords) < 2:
            return "Sud", {"Sud": 100}
        
        # Calculer les segments et leurs orientations
        orientations = {"Nord": 0, "Sud": 0, "Est": 0, "Ouest": 0}
        total_length = 0
        
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            
            # Calculer la longueur du segment
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx**2 + dy**2)
            
            if length < 0.00001:  # Éviter division par zéro
                continue
            
            # Calculer l'angle en degrés (0° = Est, 90° = Nord)
            angle = degrees(atan2(dy, dx))
            
            # Normaliser l'angle entre 0 et 360
            if angle < 0:
                angle += 360
            
            # Classer par orientation
            if 45 <= angle < 135:
                orientations["Nord"] += length
            elif 135 <= angle < 225:
                orientations["Ouest"] += length
            elif 225 <= angle < 315:
                orientations["Sud"] += length
            else:
                orientations["Est"] += length
            
            total_length += length
        
        # Calculer les pourcentages
        if total_length > 0:
            for key in orientations:
                orientations[key] = round((orientations[key] / total_length) * 100, 1)
        
        # Trouver l'orientation dominante
        dominant = max(orientations.items(), key=lambda x: x[1])
        
        return dominant[0], orientations

    def calculate_sun_exposure(self, dominant_orientation):
        """Calcule le score d'ensoleillement selon l'orientation"""
        # Bonus d'ensoleillement par orientation (Maroc = hémisphère nord)
        exposure_scores = {
            "Sud": 100,   # Meilleure exposition
            "Sud-Est": 90,
            "Sud-Ouest": 90,
            "Est": 75,
            "Ouest": 75,
            "Nord-Est": 50,
            "Nord-Ouest": 50,
            "Nord": 40    # Moins bonne exposition
        }
        
        return exposure_scores.get(dominant_orientation, 70)

    def _handler(self, request, response):
        print("=== DEBUT CALCUL SOLAR ===")
        
        try:
            geom_json = json.loads(request.inputs['line'][0].data)
            line = shape(geom_json)
            coords = list(line.coords)
            
            print(f"Ligne avec {len(coords)} points")
            
            # Calculer l'orientation réelle
            dominant_orientation, orientations = self.calculate_orientation(coords)
            sun_exposed_pct = round(orientations.get(dominant_orientation, 0), 1)
            
            # Calculer le score d'ensoleillement
            base_score = self.calculate_sun_exposure(dominant_orientation)
            
            # Ajuster le score selon le pourcentage de l'orientation dominante
            final_score = round((base_score * sun_exposed_pct / 100) * 0.7 + base_score * 0.3)
            
            # Créer l'histogramme
            histogram = [
                {"orientation": k, "pct": v}
                for k, v in orientations.items()
                if v > 0  # N'afficher que les orientations présentes
            ]
            
            result = {
                "dominant_orientation": dominant_orientation,
                "sun_exposed_pct": sun_exposed_pct,
                "score": final_score,
                "histogram": histogram
            }
            
            print(f"=== CALCUL SOLAR REUSSI ===")
            print(f"Orientation dominante : {dominant_orientation}")
            print(f"Pourcentages : {orientations}")
            print(f"Score : {final_score}")
            
            response.outputs['result'].data = json.dumps(result)
            return response
            
        except Exception as e:
            print(f"ERREUR SOLAR: {e}")
            import traceback
            traceback.print_exc()
            
            # Valeurs par défaut en cas d'erreur
            result = {
                "dominant_orientation": "Sud",
                "sun_exposed_pct": 50,
                "score": 70,
                "histogram": [{"orientation": "Sud", "pct": 50}]
            }
            response.outputs['result'].data = json.dumps(result)
            return response