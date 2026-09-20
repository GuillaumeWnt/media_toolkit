### Contexte de l'environnement de développement

**Système & Espace de travail :**
- OS : Windows 11 (Terminal : PowerShell dans VS Code)
- Projet : `media_toolkit` (dépôt Git local)
- Python : 3.12.10 exécuté dans un environnement virtuel local (`.venv`)

**Outils système & Multimédia :**
- FFmpeg : v9.0.1 (Full build de gyan.dev) accessible globalement dans le `PATH`.
  - Codecs inclus : prise en charge native intégrale (`libx264`, `libx265`, `libsvtav1`, `libmp3lame`, `libopus`, etc.).
  - Accélération matérielle disponible : CUDA / NVENC / NVDEC (Nvidia), D3D11VA / D3D12VA, AMF.
  - Fonctionnalités avancées intégrées : filtres de vision (`libplacebo`, `libvidstab`) et prise en charge de `libwhisper`.

**Bibliothèques Python disponibles dans le `.venv` :**
- `opencv-python-headless` (ou `opencv-python`)
- `pillow`
- `easyocr` (OCR / extraction et détection de texte sur images et slides)
- `faster-whisper` (Speech-to-Text / transcription vocale locale optimisée)
- Module standard Python : `subprocess`, `pathlib`, `os`, `argparse`

**Consignes pour le code généré :**
1. **Syntaxe shell :** Fournir des commandes compatibles **PowerShell** (attention aux guillemets, aux caractères d'échappement et aux chemins de fichiers Windows avec `Path` de `pathlib`).
2. **Pilotage FFmpeg :** Privilégier des appels via le module standard `subprocess.run(["ffmpeg", ...], check=True)` pour une portabilité maximale sans dépendance wrapper superflue.
3. **Optimisation :** Tirer parti du transcodage sans réencodage (`-c copy`) quand c'est possible, ou proposer les encodeurs accélérés par GPU (`-c:v h264_nvenc`) pour les traitements lourds.
4. **Traitement multimodal :**
   - Utiliser `faster-whisper` pour les transcriptions audio/vidéo locales (privilégier `device="cpu"` avec `compute_type="int8"` ou GPU CUDA si spécifié).
   - Utiliser `easyocr` couplé à OpenCV pour la reconnaissance et l'indexation de texte dans les diapositives.
5. **Style :** Scripts autonomes en ligne de commande (CLI), sans interface graphique (GUI), avec gestion d'arguments simples (`argparse`) ou variables d'entrée/sortie claires en début de script.