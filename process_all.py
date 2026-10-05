"""
process_all.py
==============
Traite toutes les vidéos du dossier input/ et produit pour chacune :
  - <nom>_audio.mp3   → piste audio extraite
  - <nom>_video.mp4   → vidéo remuxée (sans réencodage)
  - <nom>_slides.pdf  → diapositives détectées par comparaison de frames

Usage :
  python process_all.py
  python process_all.py input/BDD_v1.mp4   ← traite une seule vidéo
"""

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# Force UTF-8 sur Windows pour éviter les erreurs d'encodage cp1252
import io
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")

# ==============================================================================
# PARAMÈTRES
# ==============================================================================
INPUT_DIR: Path = Path("input")
OUT_AUDIO: Path = Path("output_audio")
OUT_VIDEO: Path = Path("output_video")
OUT_SLIDES: Path = Path("output_slides")

# --- Audio ---
AUDIO_FORMAT: str = "mp3"          # mp3 | aac | opus | flac | wav
AUDIO_QUALITY: int = 2             # VBR pour mp3 (0 = meilleure qualité)

# --- Vidéo ---
VIDEO_CODEC: str = "copy"          # copy | libx264 | libx265 | h264_nvenc
AUDIO_CODEC_VIDEO: str = "copy"    # copy | aac | none

# --- Slides ---
SAMPLE_INTERVAL_SEC: float = 1.0   # intervalle d'analyse (secondes)
DIFF_THRESHOLD: float = 0.050      # % pixels différents pour détecter un changement
PIXEL_DIFF_INTENSITY: int = 25     # tolérance par pixel (0-255)
# ==============================================================================

VALID_VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".flv"}


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION AUDIO
# ─────────────────────────────────────────────────────────────────────────────

def extract_audio(video_path: Path) -> None:
    OUT_AUDIO.mkdir(parents=True, exist_ok=True)
    out = OUT_AUDIO / f"{video_path.stem}_audio.{AUDIO_FORMAT}"
    print(f"  [audio] -> {out.name}")

    if AUDIO_FORMAT == "mp3":
        codec_args = ["-c:a", "libmp3lame", "-q:a", str(AUDIO_QUALITY)]
    elif AUDIO_FORMAT == "aac":
        codec_args = ["-c:a", "aac", "-b:a", "192k"]
    elif AUDIO_FORMAT == "opus":
        codec_args = ["-c:a", "libopus", "-b:a", "128k"]
    elif AUDIO_FORMAT == "flac":
        codec_args = ["-c:a", "flac"]
    elif AUDIO_FORMAT == "wav":
        codec_args = ["-c:a", "pcm_s16le"]
    else:
        codec_args = ["-c:a", "copy"]

    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vn"] + codec_args + [str(out)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  [audio] OK ({out})")


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION VIDÉO
# ─────────────────────────────────────────────────────────────────────────────

def extract_video(video_path: Path) -> None:
    OUT_VIDEO.mkdir(parents=True, exist_ok=True)
    out = OUT_VIDEO / f"{video_path.stem}_video.mp4"
    print(f"  [video] -> {out.name}")

    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c:v", VIDEO_CODEC]

    if AUDIO_CODEC_VIDEO == "none":
        cmd += ["-an"]
    elif AUDIO_CODEC_VIDEO == "aac":
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-c:a", AUDIO_CODEC_VIDEO]

    if VIDEO_CODEC == "copy":
        cmd += ["-movflags", "+faststart"]

    cmd.append(str(out))
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  [video] OK ({out})")


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION SLIDES
# ─────────────────────────────────────────────────────────────────────────────

def _is_new_slide(
    curr_gray: cv2.typing.MatLike,
    last_gray: cv2.typing.MatLike | None,
) -> tuple[bool, float]:
    if last_gray is None:
        return True, 1.0
    diff = cv2.absdiff(curr_gray, last_gray)
    changed = diff > PIXEL_DIFF_INTENSITY
    ratio = float(np.mean(changed))
    return ratio >= DIFF_THRESHOLD, ratio


def extract_slides(video_path: Path) -> None:
    OUT_SLIDES.mkdir(parents=True, exist_ok=True)
    out = OUT_SLIDES / f"{video_path.stem}_slides.pdf"
    print(f"  [slides] -> {out.name}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  [slides] ERREUR : impossible d'ouvrir {video_path.name}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_step = max(1, int(fps * SAMPLE_INTERVAL_SEC))

    saved_frames: list[Image.Image] = []
    last_gray: cv2.typing.MatLike | None = None
    frame_idx = 0

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        scaled_w = 640
        scaled_h = int(scaled_w * h / w)
        small_gray = cv2.cvtColor(
            cv2.resize(frame, (scaled_w, scaled_h)), cv2.COLOR_BGR2GRAY
        )
        small_gray = cv2.GaussianBlur(small_gray, (5, 5), 0)

        detected, _ = _is_new_slide(small_gray, last_gray)
        if detected:
            last_gray = small_gray
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            saved_frames.append(Image.fromarray(rgb))

        frame_idx += frame_step
        if frame_idx >= total_frames:
            break

    cap.release()

    if not saved_frames:
        print(f"  [slides] Aucune diapositive détectée.")
        return

    saved_frames[0].save(
        out, save_all=True, append_images=saved_frames[1:], quality=95
    )
    print(f"  [slides] OK — {len(saved_frames)} slides ({out})")


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────

def get_videos() -> list[Path]:
    """Renvoie la liste des vidéos à traiter (argument CLI ou tout le dossier input/)."""
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
        missing = [p for p in paths if not p.is_file()]
        if missing:
            for p in missing:
                print(f"Fichier introuvable : {p}")
            sys.exit(1)
        return paths

    if not INPUT_DIR.exists():
        print(f"Dossier '{INPUT_DIR}' introuvable.")
        sys.exit(1)

    videos = sorted(p for p in INPUT_DIR.iterdir() if p.suffix.lower() in VALID_VIDEO_EXTS)
    if not videos:
        print(f"Aucune vidéo trouvée dans '{INPUT_DIR}'.")
        sys.exit(1)
    return videos


def main() -> None:
    videos = get_videos()

    print(f"{'='*60}")
    print(f"  {len(videos)} vidéo(s) à traiter → sortie dans des dossiers spécifiques 'output_...'")
    print(f"{'='*60}\n")

    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video.name}")
        try:
            extract_audio(video)
        except subprocess.CalledProcessError as e:
            print(f"  [audio] ERREUR FFmpeg (code {e.returncode})")

        try:
            extract_video(video)
        except subprocess.CalledProcessError as e:
            print(f"  [video] ERREUR FFmpeg (code {e.returncode})")

        extract_slides(video)
        print()

    print(f"{'='*60}")
    print("  Traitement terminé.")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print("\n[ERREUR] FFmpeg introuvable. Vérifiez qu'il est dans le PATH.")
        sys.exit(1)
