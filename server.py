from flask import Flask, request, jsonify
from pywps import Service
import os
import sys
import requests
import re

sys.path.insert(0, os.path.dirname(__file__))

# ===== CONFIGURATION GOOGLE DRIVE =====
GDRIVE_FILE_ID = "14O2amG5AhvbpmICM_GFiExO44TPVlKj8"
LOCAL_FILE_PATH = "finale_optimized.tif"

def download_from_gdrive(file_id, destination):
    """Télécharge un fichier depuis Google Drive (gère les gros fichiers)"""
    if os.path.exists(destination) and os.path.getsize(destination) > 1000000:
        file_size = os.path.getsize(destination) / (1024*1024)
        print(f"✓ Le fichier {destination} existe déjà ({file_size:.2f} MB)")
        return True
    
    print(f"⏳ Téléchargement du fichier depuis Google Drive...")
    
    try:
        session = requests.Session()
        
        # Première requête pour obtenir le token de confirmation
        URL = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = session.get(URL, stream=True, timeout=60)
        
        # Chercher le token de confirmation dans la réponse
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        
        # Si pas de token dans les cookies, chercher dans le HTML
        if token is None:
            content = response.text
            match = re.search(r'confirm=([0-9A-Za-z_]+)', content)
            if match:
                token = match.group(1)
        
        # Télécharger avec le token
        if token:
            URL = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={token}"
        else:
            # Essayer l'API alternative
            URL = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
        
        print(f"  URL de téléchargement : {URL[:80]}...")
        response = session.get(URL, stream=True, timeout=300)
        
        if response.status_code != 200:
            print(f"✗ Erreur HTTP {response.status_code}")
            return False
        
        # Vérifier si c'est bien un fichier binaire
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type:
            print(f"✗ Erreur : Google Drive a retourné du HTML au lieu du fichier")
            print(f"  Content-Type: {content_type}")
            return False
        
        # Téléchargement avec progression
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        chunk_size = 32768  # 32 KB par chunk
        
        print(f"  Taille attendue : {total_size / (1024*1024):.2f} MB")
        
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and downloaded % (chunk_size * 100) == 0:  # Afficher tous les ~3 MB
                        progress = (downloaded / total_size) * 100
                        print(f"  Progression: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)", flush=True)
        
        file_size = os.path.getsize(destination)
        print(f"\n✓ Téléchargement terminé : {destination}")
        print(f"  Taille du fichier : {file_size / (1024*1024):.2f} MB")
        
        if file_size < 1000000:  # Moins de 1 MB = problème
            print(f"⚠️ ATTENTION : Le fichier est trop petit ({file_size} octets)")
            # Lire les premiers octets pour déboguer
            with open(destination, 'rb') as f:
                first_bytes = f.read(200)
                print(f"  Premiers octets : {first_bytes[:100]}")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors du téléchargement : {e}")
        import traceback
        traceback.print_exc()
        return False

# Créer les dossiers nécessaires pour PyWPS
os.makedirs('/tmp/pywps', exist_ok=True)
os.makedirs('/tmp/outputs', exist_ok=True)
print("✓ Dossiers PyWPS créés : /tmp/pywps et /tmp/outputs")

# Télécharger le fichier TIFF au démarrage de l'application
print("\n" + "="*60)
print("  INITIALISATION DE L'APPLICATION")
print("="*60)
success = download_from_gdrive(GDRIVE_FILE_ID, LOCAL_FILE_PATH)
if not success:
    print("⚠️ ATTENTION : Le fichier n'a pas pu être téléchargé correctement")
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

@app.route('/health')
def health():
    """Endpoint pour vérifier que l'app fonctionne"""
    file_exists = os.path.exists(LOCAL_FILE_PATH)
    file_size = os.path.getsize(LOCAL_FILE_PATH) if file_exists else 0
    return jsonify({
        "status": "ok",
        "tiff_file_exists": file_exists,
        "tiff_file_size_mb": round(file_size / (1024*1024), 2)
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Interface web : http://localhost:5000")
    print("  Service WPS   : http://localhost:5000/wps")
    print("="*60 + "\n")
    
    # Pour Railway, utiliser le port fourni par la variable d'environnement
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)