import subprocess
import sys
from pathlib import Path

# ==============================================================================
# PARAMÈTRES DE CONFIGURATION
# ==============================================================================
# Codec vidéo de sortie :
#   "copy"        → remux sans réencodage (ultra-rapide, qualité originale)
#   "libx264"     → encodage CPU H.264
#   "libx265"     → encodage CPU H.265 / HEVC (meilleure compression)
#   "h264_nvenc"  → encodage GPU Nvidia H.264 (nécessite CUDA)
#   "hevc_nvenc"  → encodage GPU Nvidia H.265 (nécessite CUDA)
VIDEO_CODEC: str = "copy"

# Codec audio de sortie :
#   "copy"    → conserve la piste audio d'origine (recommandé avec VIDEO_CODEC="copy")
#   "aac"     → réencode en AAC 192k
#   "none"    → supprime la piste audio (vidéo muette)
AUDIO_CODEC: str = "copy"

# Format / extension du conteneur de sortie : mp4, mkv, mov
OUTPUT_FORMAT: str = "mp4"

# Dossiers d'entrée et de sortie
INPUT_DIR: Path = Path("input")
OUTPUT_DIR: Path = Path("output_video")
# ==============================================================================

VALID_VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".flv"}


def get_video_path() -> Path:
    """Récupère la vidéo passée en argument CLI ou la première trouvée dans input/."""
    if len(sys.argv) > 1:
        video_arg = Path(sys.argv[1])
        if video_arg.is_file():
            return video_arg

    if not INPUT_DIR.exists():
        INPUT_DIR.mkdir(parents=True, exist_ok=True)

    candidates = [p for p in INPUT_DIR.iterdir() if p.suffix.lower() in VALID_VIDEO_EXTS]

    if not candidates:
        print("Erreur : Aucune vidéo trouvée dans le dossier 'input/'.")
        print("Placez une vidéo dans 'input/' ou indiquez son chemin en argument :")
        print("  python extract_video.py input/ma_video.mp4")
        sys.exit(1)

    return candidates[0]


def build_ffmpeg_cmd(video_path: Path, video_output: Path) -> list[str]:
    """Construit la commande FFmpeg adaptée aux codecs et au format demandés."""
    cmd = ["ffmpeg", "-y", "-i", str(video_path)]

    # Piste vidéo
    cmd += ["-c:v", VIDEO_CODEC]

    # Piste audio
    if AUDIO_CODEC == "none":
        cmd += ["-an"]
    elif AUDIO_CODEC == "aac":
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-c:a", AUDIO_CODEC]

    # Évite les problèmes de compatibilité MP4 lors d'un remux
    if OUTPUT_FORMAT == "mp4" and VIDEO_CODEC == "copy":
        cmd += ["-movflags", "+faststart"]

    cmd.append(str(video_output))
    return cmd


def extract_video() -> None:
    video_path = get_video_path()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    video_output = OUTPUT_DIR / f"{video_path.stem}_extracted.{OUTPUT_FORMAT}"

    print(f"-> Vidéo source    : {video_path}")
    print(f"-> Sortie vidéo    : {video_output}")
    print(f"-> Codec vidéo     : {VIDEO_CODEC}")
    print(f"-> Codec audio     : {AUDIO_CODEC if AUDIO_CODEC != 'none' else 'supprimé'}")
    print(f"-> Conteneur       : {OUTPUT_FORMAT.upper()}")
    print()

    cmd = build_ffmpeg_cmd(video_path, video_output)
    print(f"-> Commande FFmpeg : {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd, check=True)
        print(f"\n[OK] Vidéo extraite avec succès : {video_output}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERREUR] FFmpeg a échoué (code {e.returncode}).")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("\n[ERREUR] FFmpeg introuvable. Vérifiez qu'il est bien installé et dans le PATH.")
        sys.exit(1)


if __name__ == "__main__":
    extract_video()
