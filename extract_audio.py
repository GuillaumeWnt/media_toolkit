import subprocess
import sys
from pathlib import Path

# ==============================================================================
# PARAMÈTRES DE CONFIGURATION
# ==============================================================================
# Format de sortie audio : mp3, aac, opus, flac, wav
OUTPUT_FORMAT: str = "mp3"

# Qualité audio (uniquement pour mp3 via libmp3lame, 0 = meilleure qualité)
# Pour les autres formats, FFmpeg choisit la qualité par défaut.
AUDIO_QUALITY: int = 2

# Dossiers d'entrée et de sortie
INPUT_DIR: Path = Path("input")
OUTPUT_DIR: Path = Path("output_audio")
# ==============================================================================

VALID_VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".flv"}


def get_videos() -> list[Path]:
    """Récupère la vidéo passée en argument CLI ou toutes celles trouvées dans input/."""
    if len(sys.argv) > 1:
        video_arg = Path(sys.argv[1])
        if video_arg.is_file():
            return [video_arg]
        print(f"Erreur : Le fichier '{video_arg}' n'existe pas.")
        sys.exit(1)

    if not INPUT_DIR.exists():
        INPUT_DIR.mkdir(parents=True, exist_ok=True)

    candidates = [p for p in INPUT_DIR.iterdir() if p.suffix.lower() in VALID_VIDEO_EXTS]

    if not candidates:
        print("Erreur : Aucune vidéo trouvée dans le dossier 'input/'.")
        sys.exit(1)

    return candidates


def build_ffmpeg_cmd(video_path: Path, audio_output: Path) -> list[str]:
    """Construit la commande FFmpeg adaptée au format de sortie demandé."""
    cmd = ["ffmpeg", "-y", "-i", str(video_path)]

    if OUTPUT_FORMAT == "mp3":
        cmd += ["-vn", "-c:a", "libmp3lame", "-q:a", str(AUDIO_QUALITY)]
    elif OUTPUT_FORMAT == "aac":
        cmd += ["-vn", "-c:a", "aac", "-b:a", "192k"]
    elif OUTPUT_FORMAT == "opus":
        cmd += ["-vn", "-c:a", "libopus", "-b:a", "128k"]
    elif OUTPUT_FORMAT == "flac":
        cmd += ["-vn", "-c:a", "flac"]
    elif OUTPUT_FORMAT == "wav":
        cmd += ["-vn", "-c:a", "pcm_s16le"]
    else:
        # Fallback : copie du flux audio brut si le format contient déjà le bon codec
        cmd += ["-vn", "-c:a", "copy"]

    cmd.append(str(audio_output))
    return cmd


def process_single_video(video_path: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audio_output = OUTPUT_DIR / f"{video_path.stem}_audio.{OUTPUT_FORMAT}"

    print(f"-> Vidéo source    : {video_path.name}")
    print(f"-> Sortie audio    : {audio_output.name}")
    print(f"-> Format          : {OUTPUT_FORMAT.upper()}")

    cmd = build_ffmpeg_cmd(video_path, audio_output)
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[OK] Audio extrait avec succès.\n")
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] FFmpeg a échoué (code {e.returncode}).\n")
    except FileNotFoundError:
        print("\n[ERREUR] FFmpeg introuvable dans le PATH.")
        sys.exit(1)


def main() -> None:
    videos = get_videos()
    print(f"=== Traitement de {len(videos)} vidéo(s) ===\n")
    for vid in videos:
        process_single_video(vid)


if __name__ == "__main__":
    main()
