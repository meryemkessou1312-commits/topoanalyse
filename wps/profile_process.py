import os
from pywps import Process, ComplexInput, ComplexOutput, Format
import json
import rasterio
from shapely.geometry import shape, LineString
import numpy as np
from math import sqrt

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
            # Vérifier que le fichier existe
            if not os.path.exists(DEM_PATH):
                raise Exception(f"Fichier TIFF introuvable : {DEM_PATH}")
            
            file_size = os.path.getsize(DEM_PATH) / (1024*1024)
            print(f"Fichier TIFF : {DEM_PATH} ({file_size:.2f} MB)")
            
            # Lire la géométrie
            geom_json = json.loads(request.inputs['line'][0].data)
            print(f"GeoJSON reçu : {geom_json}")
            
            line = shape(geom_json)
            coords = list(line.coords)
            print(f"Ligne : {len(coords)} points")
            print(f"Premier point : {coords[0]}")
            print(f"Dernier point : {coords[-1]}")
            
            # Ouvrir le MNT
            with rasterio.open(DEM_PATH) as src:
                print(f"MNT ouvert : {src.width}x{src.height}")
                print(f"CRS : {src.crs}")
                print(f"Bounds : {src.bounds}")
                
                # Vérifier que la ligne est dans les limites du TIFF
                bounds = src.bounds
                for coord in coords:
                    if not (bounds.left <= coord[0] <= bounds.right and 
                           bounds.bottom <= coord[1] <= bounds.top):
                        print(f"⚠️ ATTENTION : Point {coord} est en dehors des limites du TIFF")
                        print(f"   Limites : X[{bounds.left}, {bounds.right}], Y[{bounds.bottom}, {bounds.top}]")
                
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
                        
                        # Filtrer les valeurs NoData (souvent -9999 ou très négatives)
                        if elevation > -1000 and elevation < 9000:
                            # Calculer la distance réelle
                            if i == 0:
                                distance = 0.0
                            else:
                                prev_point = line.interpolate((i-1) / (num_points - 1), normalized=True)
                                dx = point.x - prev_point.x
                                dy = point.y - prev_point.y
                                distance = profile[-1]["distance"] + sqrt(dx*dx + dy*dy) * 111320  # approximation m
                            
                            profile.append({
                                "distance": float(distance),
                                "x": float(point.x),
                                "y": float(point.y),
                                "elevation": float(elevation)
                            })
                        else:
                            print(f"⚠️ Valeur aberrante ignorée : {elevation} au point {i}")
                            
                    except Exception as e:
                        print(f"Erreur lecture point {i} : {e}")
                        continue
                
                print(f"Points extraits : {len(profile)}")
                
                if len(profile) < 5:
                    raise Exception(f"Pas assez de points valides extraits ({len(profile)}). La ligne est probablement en dehors de la zone couverte par le TIFF.")
                
                # Calculer les stats
                elevations = [p["elevation"] for p in profile]
                distances = [p["distance"] for p in profile]
                
                # Calculer la pente moyenne
                if len(profile) > 1:
                    total_elevation_change = abs(elevations[-1] - elevations[0])
                    horizontal_distance = distances[-1]
                    pente_moy_deg = np.degrees(np.arctan(total_elevation_change / max(horizontal_distance, 1)))
                else:
                    pente_moy_deg = 0.0
                
                stats = {
                    "distance_totale_m": float(distances[-1]),
                    "alt_max": float(max(elevations)),
                    "alt_min": float(min(elevations)),
                    "alt_moy": float(sum(elevations) / len(elevations)),
                    "denivele": float(max(elevations) - min(elevations)),
                    "pente_moy_deg": float(pente_moy_deg)
                }
                
                result = {"profile": profile, "stats": stats}
                
                print("=== CALCUL REUSSI ===")
                print(f"Stats : {stats}")
                
                response.outputs['profile'].data = json.dumps(result)
                return response
                
        except Exception as e:
            print(f"ERREUR CRITIQUE : {e}")
            import traceback
            traceback.print_exc()
            
            # NE RETOURNEZ JAMAIS DE FAUSSES DONNÉES
            # Retournez une vraie erreur
            error_result = {
                "error": str(e),
                "profile": [],
                "stats": {
                    "distance_totale_m": 0,
                    "alt_max": 0,
                    "alt_min": 0,
                    "alt_moy": 0,
                    "denivele": 0,
                    "pente_moy_deg": 0
                }
            }
            
            response.outputs['profile'].data = json.dumps(error_result)
            return response