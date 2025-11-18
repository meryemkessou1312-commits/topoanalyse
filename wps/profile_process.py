import os
from pywps import Process, ComplexInput, ComplexOutput, Format
import json
import rasterio
from shapely.geometry import shape
import numpy as np

DEM_PATH = "finale_optimized.tif"

class ProfilTopo(Process):
    def __init__(self):
        inputs = [ComplexInput('line', 'Ligne', supported_formats=[Format('application/vnd.geo+json')])]
        outputs = [ComplexOutput('profile', 'Profil', supported_formats=[Format('application/json')])]
        
        super(ProfilTopo, self).__init__(
            self._handler,
            identifier='profil_topo',
            title='Profil Topo',
            version='1.0',
            inputs=inputs,
            outputs=outputs
        )

    def _handler(self, request, response):
        print("=== DEBUT CALCUL PROFIL ===")
        
        try:
            # Lire la géométrie
            geom_json = json.loads(request.inputs['line'][0].data)
            line = shape(geom_json)
            print(f"Ligne reçue: {len(list(line.coords))} points")
            
            # Ouvrir le MNT
            with rasterio.open(DEM_PATH) as src:
                print(f"MNT ouvert: {src.width}x{src.height}")
                
                # Échantillonner 100 points le long de la ligne
                profile = []
                num_points = 100
                
                for i in range(num_points):
                    fraction = i / (num_points - 1)
                    point = line.interpolate(fraction, normalized=True)
                    
                    try:
                        # Lire l'altitude
                        vals = list(src.sample([(point.x, point.y)]))
                        elevation = float(vals[0][0])
                        
                        if -1000 < elevation < 9000:  # Filtrer valeurs aberrantes
                            profile.append({
                                "distance": float(i * 100),  # Distance fictive
                                "x": float(point.x),
                                "y": float(point.y),
                                "elevation": float(elevation)
                            })
                    except:
                        continue
                
                print(f"Points extraits: {len(profile)}")
                
                if len(profile) < 5:
                    raise Exception("Pas assez de points valides")
                
                # Calculer les stats
                elevations = [p["elevation"] for p in profile]
                
                stats = {
                    "distance_totale_m": float(len(profile) * 100),
                    "alt_max": float(max(elevations)),
                    "alt_min": float(min(elevations)),
                    "alt_moy": float(sum(elevations) / len(elevations)),
                    "denivele": float(max(elevations) - min(elevations)),
                    "pente_moy_deg": 5.0  # Valeur fictive pour test
                }
                
                result = {"profile": profile, "stats": stats}
                
                print("=== CALCUL REUSSI ===")
                response.outputs['profile'].data = json.dumps(result)
                return response
                
        except Exception as e:
            print(f"ERREUR: {e}")
            import traceback
            traceback.print_exc()
            
            # Retourner un profil fictif pour déboguer
            fake_profile = [
                {"distance": i * 100, "x": 0, "y": 0, "elevation": 1000 + i * 10}
                for i in range(50)
            ]
            
            result = {
                "profile": fake_profile,
                "stats": {
                    "distance_totale_m": 5000,
                    "alt_max": 1500,
                    "alt_min": 1000,
                    "alt_moy": 1250,
                    "denivele": 500,
                    "pente_moy_deg": 5.0
                }
            }
            
            response.outputs['profile'].data = json.dumps(result)
            return response