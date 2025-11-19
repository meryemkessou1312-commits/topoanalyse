from flask import Flask, request, jsonify
from pywps import Service
import os
import sys
from osgeo import gdal

sys.path.insert(0, os.path.dirname(__file__))

LOCAL_FILE_PATH = "finale_optimized.tif"

def verify_tiff():
    """Vérifie que le TIFF est valide au démarrage"""
    if not os.path.exists(LOCAL_FILE_PATH):
        print(f"❌ ERREUR FATALE : {LOCAL_FILE_PATH} introuvable")
        sys.exit(1)
    
    file_size = os.path.getsize(LOCAL_FILE_PATH)
    print(f"📁 Fichier trouvé : {LOCAL_FILE_PATH} ({file_size / (1024*1024):.2f} MB)")
    
    try:
        print("🔍 Vérification GDAL...")
        ds = gdal.Open(LOCAL_FILE_PATH, gdal.GA_ReadOnly)
        
        if ds is None:
            raise Exception("GDAL ne peut pas ouvrir le fichier")
        
        band = ds.GetRasterBand(1)
        stats = band.ComputeStatistics(False)
        
        print(f"✅ TIFF valide :")
        print(f"   - Dimensions : {ds.RasterXSize} x {ds.RasterYSize}")
        print(f"   - Altitude min/max : {stats[0]:.1f} / {stats[1]:.1f} m")
        
        ds = None
        return True
        
    except Exception as e:
        print(f"❌ ERREUR FATALE : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Créer les dossiers PyWPS
os.makedirs('/tmp/pywps', exist_ok=True)
os.makedirs('/tmp/outputs', exist_ok=True)
print("✓ Dossiers PyWPS créés")

# Vérifier le TIFF au démarrage
print("\n" + "="*60)
print("  VÉRIFICATION DU FICHIER TIFF")
print("="*60)
verify_tiff()
print("="*60 + "\n")

from wps.profile_process import ProfilTopo
from wps.solar_exposure import SolarExposure

app = Flask(__name__, static_folder='Web', static_url_path='')

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

processes = [ProfilTopo(), SolarExposure()]
service = Service(processes, ['pywps.cfg'])

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/wps', methods=['GET', 'POST', 'OPTIONS'])
def wps():
    if request.method == 'OPTIONS':
        return '', 200
    return service

@app.route('/health')
def health():
    file_exists = os.path.exists(LOCAL_FILE_PATH)
    file_size = os.path.getsize(LOCAL_FILE_PATH) if file_exists else 0
    return jsonify({
        "status": "ok",
        "tiff_file_exists": file_exists,
        "tiff_file_size_mb": round(file_size / (1024*1024), 2)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
```

### **3️⃣ Vérifier requirements.txt**

Vérifiez que `requirements.txt` contient bien :
```
Flask==3.0.0
gunicorn==21.2.0
pywps==4.5.2
rasterio==1.3.9
shapely==2.0.2
numpy==1.26.2