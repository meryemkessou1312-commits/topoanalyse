# 🗺️ Analyse Topographique - Région Drâa-Tafilalet

Application web d'analyse topographique avec profil altimétrique, exposition solaire et statistiques avancées.

## 📦 Installation Locale

### Prérequis
- Python 3.10+
- pip

### Installation

1. **Cloner le repository**
```bash
git clone https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
cd VOTRE_REPO
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Lancer le serveur**
```bash
python server.py
```

Le MNT (248 MB) sera téléchargé automatiquement au premier lancement depuis Google Drive.

4. **Ouvrir l'application**
```
http://localhost:5000
```

## 🌐 Accès en ligne

**Lien de démonstration :** [À venir]

## 📂 Structure du projet
```
├── index.html                 # Interface web
├── server.py                  # Serveur Flask/PyWPS
├── profile_process.py         # Processus de profil topographique
├── solar_exposure.py          # Processus d'exposition solaire
├── pywps.cfg                  # Configuration PyWPS
├── requirements.txt           # Dépendances Python
├── DraaTafilalet.geojson     # Limites de la région
├── errachidia.jpg            # Image de fond
├── montagne.jpeg             # Image preloader
└── README.md                 # Ce fichier
```

## 🔗 Fichier MNT

Le fichier MNT (finale_optimized.tif - 248 MB) est hébergé sur Google Drive :

**Téléchargement manuel :** [Cliquez ici](https://drive.google.com/file/d/14O2amG5AhvbpmICM_GFiExO44TPVlKj8/view?usp=sharing)

Le téléchargement automatique se fait au premier lancement du serveur.

## ⚙️ Fonctionnalités

- ✅ Profil topographique interactif
- ✅ Analyse d'exposition solaire
- ✅ Calcul de pentes et orientations
- ✅ Statistiques détaillées (altitude, dénivelé, distance)
- ✅ Export CSV des données
- ✅ Interface moderne et responsive

## 🛠️ Technologies

- **Frontend:** HTML5, Tailwind CSS, Leaflet.js, Plotly.js
- **Backend:** Python, Flask, PyWPS
- **Données:** GDAL, Rasterio, Shapely

## 📧 Contact

Pour toute question : [votre.email@example.com]