import argparse
import io
from pathlib import Path

from PIL import Image

try:
    import resvg_py
except ImportError:
    resvg_py = None

# Résolutions standard supportées par l'explorateur Windows
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def make_square(image: Image.Image) -> Image.Image:
    """
    Cadre l'image au centre d'un carré transparent si ses proportions ne sont pas 1:1.
    """
    if image.width == image.height:
        return image

    max_dim = max(image.width, image.height)
    square_img = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
    offset = ((max_dim - image.width) // 2, (max_dim - image.height) // 2)
    square_img.paste(image, offset)
    return square_img


def load_image(file_path: Path) -> Image.Image:
    """
    Charge une image SVG ou matricielle (PNG, JPG, etc.) et renvoie une image Pillow RGBA.
    """
    ext = file_path.suffix.lower()

    if ext == ".svg":
        if resvg_py is None:
            raise ImportError(
                "Le module 'resvg_py' est requis pour convertir les fichiers SVG. "
                "Installe-le avec : pip install resvg_py"
            )
        svg_content = file_path.read_text(encoding="utf-8")
        # Rendu haute définition (512x512) pour assurer une netteté maximale dans l'icône
        png_bytes = resvg_py.svg_to_bytes(svg_string=svg_content, width=512, height=512)
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    # PNG et autres formats
    img = Image.open(file_path)
    return img.convert("RGBA")


def convert_file(input_file: Path, output_dir: Path) -> Path:
    """
    Convertit un fichier image en icône .ico multi-résolution.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{input_file.stem}.ico"

    img = load_image(input_file)
    img_square = make_square(img)

    img_square.save(output_file, format="ICO", sizes=ICO_SIZES)
    return output_file


def process_directory(input_dir: Path, output_dir: Path):
    """
    Traite automatiquement toutes les images compatibles du dossier d'entrée.
    """
    valid_extensions = {".png", ".svg", ".jpg", ".jpeg", ".webp"}
    files = [
        f
        for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_extensions
    ]

    if not files:
        print(
            f"Aucune image trouvée dans '{input_dir}' ({', '.join(valid_extensions)})"
        )
        return

    print(f"Trouvé {len(files)} fichier(s) à convertir...")
    for f in files:
        try:
            out = convert_file(f, output_dir)
            print(f" [OK] {f.name} -> {out.name}")
        except Exception as e:
            print(f" [ERREUR] Impossible de convertir {f.name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Convertit des images SVG/PNG en fichiers .ico pour Windows."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="input",
        help="Chemin vers le fichier ou dossier source (par défaut: 'input')",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output",
        help="Dossier de sortie (par défaut: 'output')",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file():
        out = convert_file(input_path, output_path)
        print(f"[OK] Fichier converti avec succès : {out}")
    elif input_path.is_dir():
        process_directory(input_path, output_path)
    else:
        print(f"Erreur : le chemin spécifié n'existe pas : {input_path}")


if __name__ == "__main__":
    main()
