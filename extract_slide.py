import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# ==============================================================================
# PARAMÈTRES DE CONFIGURATION
# ==============================================================================
# Intervalle d'analyse en secondes (1.0 = examine une image chaque seconde)
SAMPLE_INTERVAL_SEC: float = 1.0

# Pourcentage minimal de surface modifiée pour valider une nouvelle slide
# Ex: 0.015 = 1.5 % de pixels différents. Diminuer si des slides manquent.
DIFF_THRESHOLD: float = 0.015

# Tolérance d'intensité du pixel (0 à 255) pour ignorer les petits bruits
PIXEL_DIFF_INTENSITY: int = 25

# Dossiers d'entrée et de sortie
INPUT_DIR: Path = Path("input")
OUTPUT_DIR: Path = Path("output")
# ==============================================================================


def get_video_path() -> Path:
    """Récupère la vidéo passée en argument CLI ou la première trouvée dans input/."""
    if len(sys.argv) > 1:
        video_arg = Path(sys.argv[1])
        if video_arg.is_file():
            return video_arg

    valid_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
    if not INPUT_DIR.exists():
        INPUT_DIR.mkdir(parents=True, exist_ok=True)

    candidates = [p for p in INPUT_DIR.iterdir() if p.suffix.lower() in valid_exts]

    if not candidates:
        print("Erreur : Aucune vidéo trouvée dans le dossier 'input/'.")
        print("Placez une vidéo dans 'input/' ou indiquez son chemin en argument :")
        print("  python extract_slide.py input/ma_video.mp4")
        sys.exit(1)

    return candidates[0]


def is_new_slide(
    curr_gray: cv2.typing.MatLike,
    last_gray: cv2.typing.MatLike | None,
    diff_threshold: float,
    pixel_diff_intensity: int,
) -> tuple[bool, float]:
    """
    Compare deux images en niveaux de gris.
    Renvoie systématiquement un tuple : (détection: bool, ratio: float).
    """
    if last_gray is None:
        return True, 1.0

    # Différence absolue entre les deux matrices
    diff = cv2.absdiff(curr_gray, last_gray)

    # Détection des pixels ayant dépassé le seuil d'intensité
    changed_pixels = diff > pixel_diff_intensity
    change_ratio = float(np.mean(changed_pixels))

    return change_ratio >= diff_threshold, change_ratio


def extract_slides() -> None:
    video_path = get_video_path()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_output_path = OUTPUT_DIR / f"{video_path.stem}_slides.pdf"

    print(f"-> Ouverture de la vidéo : {video_path.name}")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Erreur : Impossible de lire le fichier {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0.0
    frame_step = max(1, int(fps * SAMPLE_INTERVAL_SEC))

    print(f"-> Durée : {duration_sec:.1f}s | FPS : {fps:.1f}")
    print(
        f"-> Échantillonnage : 1 image toutes les {SAMPLE_INTERVAL_SEC}s (pas de {frame_step} frames)"
    )

    saved_frames: list[Image.Image] = []
    last_slide_gray: cv2.typing.MatLike | None = None
    frame_idx = 0

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        # Redimensionnement optimisé pour accélérer le calcul matriciel
        h, w = frame.shape[:2]
        scaled_w = 640
        scaled_h = int(scaled_w * h / w)
        small_gray = cv2.cvtColor(
            cv2.resize(frame, (scaled_w, scaled_h)), cv2.COLOR_BGR2GRAY
        )

        # Filtre anti-bruit pour éliminer les artefacts de compression MPEG
        small_gray = cv2.GaussianBlur(small_gray, (5, 5), 0)

        detected, ratio = is_new_slide(
            small_gray,
            last_slide_gray,
            DIFF_THRESHOLD,
            PIXEL_DIFF_INTENSITY,
        )

        if detected:
            last_slide_gray = small_gray
            # Conversion en RGB haute résolution pour Pillow
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            saved_frames.append(Image.fromarray(rgb_frame))

            timestamp = frame_idx / fps
            mins = int(timestamp // 60)
            secs = int(timestamp % 60)
            print(
                f"  [+] Diapositive #{len(saved_frames):02d} détectée à {mins:02d}:{secs:02d} (variation: {ratio * 100:.2f}%)"
            )

        frame_idx += frame_step
        if frame_idx >= total_frames:
            break

    cap.release()

    if not saved_frames:
        print("Aucune diapositive n'a été détectée.")
        return

    print(
        f"\n-> Sauvegarde de {len(saved_frames)} diapositives dans {pdf_output_path}..."
    )
    saved_frames[0].save(
        pdf_output_path,
        save_all=True,
        append_images=saved_frames[1:],
        quality=95,
    )
    print(f"[OK] PDF généré avec succès : {pdf_output_path}")


if __name__ == "__main__":
    extract_slides()
