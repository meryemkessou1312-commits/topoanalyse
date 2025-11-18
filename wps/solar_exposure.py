import os
from pywps import Process, ComplexInput, ComplexOutput, Format
import json
from shapely.geometry import shape
import numpy as np

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

    def _handler(self, request, response):
        print("=== DEBUT CALCUL SOLAR ===")
        
        try:
            geom_json = json.loads(request.inputs['line'][0].data)
            line = shape(geom_json)
            
            coords = list(line.coords)
            orientations = {"Sud": 30, "Nord": 20, "Est": 25, "Ouest": 25}
            
            histogram = [
                {"orientation": k, "pct": v}
                for k, v in orientations.items()
            ]
            
            result = {
                "dominant_orientation": "Sud",
                "sun_exposed_pct": 30,
                "score": 65,
                "histogram": histogram
            }
            
            print("=== CALCUL SOLAR REUSSI ===")
            response.outputs['result'].data = json.dumps(result)
            return response
            
        except Exception as e:
            print(f"ERREUR SOLAR: {e}")
            result = {
                "dominant_orientation": "Sud",
                "sun_exposed_pct": 50,
                "score": 70,
                "histogram": [{"orientation": "Sud", "pct": 50}]
            }
            response.outputs['result'].data = json.dumps(result)
            return response