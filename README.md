# 🎬 Media Toolkit

**Media Toolkit** est une boîte à outils de scripts Python conçue pour automatiser le traitement et la manipulation de fichiers multimédias (vidéos, images, PDF). 

Le projet fonctionne sur une **architecture en pipeline (sas)** : vous déposez vos fichiers sources dans un dossier `input/`, vous lancez un script, et le résultat propre est déversé dans un dossier spécifique `output_.../`. Vous pouvez ainsi facilement enchaîner les traitements sans mélanger vos fichiers !

---

## ⚙️ Prérequis et Installation

1. **FFmpeg** : Doit être installé sur votre machine et accessible dans votre variable d'environnement `PATH`.
2. **Python 3.12+**
3. **Dépendances Python** :
   Dans votre environnement virtuel (`.venv`), installez les paquets requis :
   ```powershell
   pip install -r requirements.txt
   pip install pymupdf  # Requis pour l'outil de filtrage de PDF
   ```

---

## 📁 Architecture des dossiers

* `input/` : **Votre dossier de travail principal.** Placez-y vos vidéos, PDF ou images sources avant de lancer un script.
* `output_audio/` : Sortie de l'extracteur audio.
* `output_video/` : Sortie de l'extracteur/remuxer vidéo.
* `output_slides/` : Sortie de l'extracteur de slides (PDF bruts).
* `output_slides_filtered/` : Sortie du nettoyeur de slides (PDF propres).
* `output_jpg/` : Sortie du compresseur d'images.
* `output_ico/` : Sortie du convertisseur d'icônes.

> 💡 **Note :** Tous les dossiers `output_*` sont ignorés par Git (via `.gitignore`) pour garder votre dépôt distant propre.

---

## 🚀 Guide d'utilisation des scripts

Tous les scripts peuvent être lancés de deux manières depuis le terminal :
- **Traitement en lot (Batch)** : `python nom_du_script.py` (traitera automatiquement *tous* les fichiers compatibles trouvés dans `input/`).
- **Traitement à l'unité** : `python nom_du_script.py input/mon_fichier.mp4` (traitera *uniquement* le fichier ciblé).

### 1. `process_all.py` (L'orchestrateur vidéo)
Extrait simultanément l'audio, la vidéo (remux) et les slides de toutes les vidéos de votre dossier source.
- **Entrée :** Fichiers vidéos (`.mp4`, `.mkv`, etc.) dans `input/`.
- **Sorties :** 
  - Audio extrait dans `output_audio/`
  - Vidéo extraite dans `output_video/`
  - PDF de slides dans `output_slides/`
- **Utilisation :** `python process_all.py`

### 2. `extract_audio.py`
Extrait uniquement la piste audio d'une vidéo. Format de sortie (mp3, aac, opus, flac, wav) et qualité (VBR) configurables en tête de script.
- **Entrée :** Vidéos dans `input/`.
- **Sortie :** Audio `.mp3` dans `output_audio/`.
- **Utilisation :** `python extract_audio.py`

### 3. `extract_video.py`
Extrait ou convertit uniquement la piste vidéo. Par défaut, utilise le codec `copy` pour un "remux" ultra-rapide sans réencodage. Choix des codecs (copy, libx264, libx265, NVENC GPU) modifiables dans le script.
- **Entrée :** Vidéos dans `input/`.
- **Sortie :** Vidéo `.mp4` dans `output_video/`.
- **Utilisation :** `python extract_video.py`

### 4. `extract_slide.py`
Analyse une vidéo frame par frame pour détecter les changements de scène majeurs et générer un document contenant toutes les diapositives d'un cours ou d'une présentation.
- **Entrée :** Vidéos dans `input/`.
- **Sortie :** Fichier `.pdf` brut dans `output_slides/`.
- **Utilisation :** `python extract_slide.py`

### 5. `filter_slides.py` ✨ (Le filtre intelligent)
Nettoie les PDF de slides générés. Utilise la **Computer Vision pure** (OpenCV, très rapide) pour détecter et rejeter les "faux slides" (captures du bureau, fenêtres pas en plein écran, barre des tâches) et un algorithme de hachage visuel (`dHash`) pour détecter et éliminer les doublons éloignés dans le temps.
- **Entrée :** Fichiers PDF bruts dans `input/` *(Prenez les PDF de output_slides/ et glissez-les ici pour les traiter)*.
- **Sortie :** Fichier `_filtered.pdf` final et propre dans `output_slides_filtered/`.
- **Utilisation :** `python filter_slides.py`

### 6. `compress_jpg.py`
Compresse fortement des images pour le web sans perte visuelle notable (qualité 80) et les redimensionne proportionnellement si elles dépassent une largeur maximale (ex: 1920px).
- **Entrée :** Images (`.jpg`, `.png`, `.webp`) dans `input/`.
- **Sortie :** Images allégées dans `output_jpg/`.
- **Utilisation :** `python compress_jpg.py`

### 7. `convert_to_ico.py`
Convertit des images matricielles ou vectorielles (SVG, PNG, JPG) en de véritables icônes multi-résolutions compatibles Windows (`.ico`). Nécessite `resvg_py` pour les vecteurs.
- **Entrée :** Images dans `input/`.
- **Sortie :** Fichier `.ico` dans `output_ico/`.
- **Utilisation :** `python convert_to_ico.py`

---

## 🛠️ Configuration avancée
Chaque programme a été pensé pour être facilement modifiable sans avoir à coder. Ouvrez n'importe quel fichier `.py` avec votre éditeur : vous y trouverez un bloc commenté **PARAMÈTRES** tout en haut du fichier pour ajuster très simplement la qualité, les formats, la tolérance des algorithmes de filtrage ou les noms des dossiers de sortie.