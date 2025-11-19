#!/bin/bash
set -e

GDRIVE_ID="14O2amG5AhvbpmICM_GFiExO44TPVlKj8"
OUTPUT="finale_optimized.tif"
TEMP="temp_download.tif"

echo "======================================"
echo "📥 TÉLÉCHARGEMENT DEPUIS GOOGLE DRIVE"
echo "======================================"

URL="https://drive.usercontent.google.com/download?id=${GDRIVE_ID}&export=download&confirm=t"

echo "🔗 URL: $URL"

for attempt in {1..3}; do
    echo "📥 Tentative $attempt/3..."
    
    if curl -L -o "$TEMP" \
        -H "User-Agent: Mozilla/5.0" \
        --progress-bar \
        --max-time 900 \
        --retry 3 \
        --retry-delay 10 \
        "$URL"; then
        
        SIZE=$(stat -c%s "$TEMP" 2>/dev/null || stat -f%z "$TEMP" 2>/dev/null)
        echo "📦 Téléchargé : $(echo "scale=2; $SIZE/1024/1024" | bc) MB"
        
        if file "$TEMP" | grep -q "HTML"; then
            echo "⚠️ Erreur : Google Drive a retourné une page HTML"
            head -20 "$TEMP"
            rm -f "$TEMP"
            continue
        fi
        
        if [ "$SIZE" -gt 50000000 ]; then
            echo "✅ Taille OK"
            break
        else
            echo "⚠️ Fichier trop petit, nouvelle tentative..."
            rm -f "$TEMP"
        fi
    fi
done

if [ ! -f "$TEMP" ] || [ $(stat -c%s "$TEMP" 2>/dev/null || stat -f%z "$TEMP" 2>/dev/null) -lt 50000000 ]; then
    echo "❌ ERREUR : Téléchargement échoué après 3 tentatives"
    echo ""
    echo "💡 SOLUTION : Utilisez gdown (plus fiable pour Google Drive)"
    pip install gdown
    gdown --id "$GDRIVE_ID" -O "$TEMP"
fi

echo "🔍 Vérification GDAL..."
if gdalinfo "$TEMP" > /tmp/gdalinfo.log 2>&1; then
    mv "$TEMP" "$OUTPUT"
    echo "✅ Fichier valide !"
    echo ""
    echo "📊 Informations :"
    head -15 /tmp/gdalinfo.log
else
    echo "⚠️ Fichier corrompu, tentative de réparation..."
    cat /tmp/gdalinfo.log
    
    if gdal_translate -co TILED=YES -co COMPRESS=LZW "$TEMP" "$OUTPUT" 2>&1; then
        rm -f "$TEMP"
        echo "✅ Fichier réparé !"
    else
        echo "❌ Impossible de réparer"
        exit 1
    fi
fi

echo ""
echo "✅ INSTALLATION TERMINÉE"