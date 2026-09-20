import sys
from pathlib import Path

from PIL import Image

# ==============================================================================
# PARAMÈTRES
# ==============================================================================
# Qualité de sortie (1 à 95). 75-80 offre une forte réduction de poids quasi-invisible à l'œil nu.
QUALITY: int = 80

# Optionnel : redimensionner si l'image dépasse une largeur max en pixels (None pour désactiver)
MAX_WIDTH: int | None = 1920

INPUT_DIR: Path = Path("input")
OUTPUT_DIR: Path = Path("output")
# ==============================================================================


def format_size(size_bytes: int) -> str:
    """Affiche une taille lisible en Ko ou Mo."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} Mo"
    return f"{size_bytes / 1024:.1f} Ko"


def compress_single_image(
    image_path: Path, output_dir: Path, quality: int = 80
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{image_path.stem}_compressed.jpg"

    initial_size = image_path.stat().st_size

    with Image.open(image_path) as img:
        # Conversion en RGB au cas où l'image contiendrait un canal alpha (RGBA/PNG renommé)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Redimensionnement proportionnel si largeur > MAX_WIDTH
        if MAX_WIDTH and img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

        # Sauvegarde optimisée
        img.save(
            output_path,
            format="JPEG",
            quality=quality,
            optimize=True,  # Réorganise la table de Huffman pour gagner de l'espace
            progressive=True,  # Chargement progressif pour le web
        )

    final_size = output_path.stat().st_size
    gain = (1 - (final_size / initial_size)) * 100

    print(f"-> {image_path.name}")
    print(
        f"   Taille : {format_size(initial_size)} -> {format_size(final_size)} (Gain : -{gain:.1f}%)"
    )
    print(f"   Sortie : {output_path}\n")


def main() -> None:
    # 1. Si un fichier précis est passé en argument CLI
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_file():
            compress_single_image(target, OUTPUT_DIR, quality=QUALITY)
            return
        print(f"Erreur : Le fichier '{target}' n'existe pas.")
        sys.exit(1)

    # 2. Sinon, traitement par lot de tous les JPG/JPEG/PNG dans input/
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    candidates = [p for p in INPUT_DIR.iterdir() if p.suffix.lower() in valid_exts]

    if not candidates:
        print("Aucune image trouvée dans le dossier 'input/'.")
        print("Usage : python compress_jpg.py input/photo.jpg")
        return

    print(
        f"-> Traitement de {len(candidates)} image(s) avec une qualité de {QUALITY}...\n"
    )
    for img_path in candidates:
        compress_single_image(img_path, OUTPUT_DIR, quality=QUALITY)


if __name__ == "__main__":
    main()
