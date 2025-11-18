from flask import Flask, request
from pywps import Service
import os
import sys
import requests

sys.path.insert(0, os.path.dirname(__file__))

# ===== CONFIGURATION GOOGLE DRIVE =====
GDRIVE_FILE_ID = "14O2amG5AhvbpmICM_GFiExO44TPVlKj8"
LOCAL_FILE_PATH = "finale_optimized.tif"

def download_from_gdrive(file_id, destination):
    """Télécharge un fichier depuis Google Drive"""
    if os.path.exists(destination):
        print(f"✓ Le fichier {destination} existe déjà")
        return True
    
    print(f"⏳ Téléchargement du fichier depuis Google Drive...")
    URL = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        session = requests.Session()
        response = session.get(URL, stream=True)
        
        # Gestion des fichiers volumineux avec confirmation
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                params = {'id': file_id, 'confirm': value}
                response = session.get(URL, params=params, stream=True)
        
        # Téléchargement avec barre de progression
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"  Progression: {progress:.1f}%", end='\r')
        
        print(f"\n✓ Téléchargement terminé : {destination}")
        print(f"  Taille du fichier : {os.path.getsize(destination) / (1024*1024):.2f} MB")
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors du téléchargement : {e}")
        return False

# Télécharger le fichier TIFF au démarrage de l'application
print("\n" + "="*60)
print("  INITIALISATION DE L'APPLICATION")
print("="*60)
download_from_gdrive(GDRIVE_FILE_ID, LOCAL_FILE_PATH)
print("="*60 + "\n")

# ===== SUITE DU CODE ORIGINAL =====
from wps.profile_process import ProfilTopo
from wps.solar_exposure import SolarExposure

# IMPORTANT : Pointer vers le dossier Web
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

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Interface web : http://localhost:5000")
    print("  Service WPS   : http://localhost:5000/wps")
    print("="*60 + "\n")
    
    # Pour Render, utiliser le port fourni par la variable d'environnement
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)