import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import pymupdf as fitz
from PIL import Image

# ==============================================================================
# PARAMÈTRES DE FILTRAGE
# ==============================================================================
HASH_TOLERANCE: int = 12  # Assez permissif pour capter les légers décalages

# Si la densité de "bords" (lignes/détails) dans les 6% du haut ou du bas
# dépasse ce seuil, c'est considéré comme une interface (bureau, ruban PPT, barre Windows)
# et non un slide plein écran.
MAX_UI_EDGE_DENSITY: float = 0.05
# ==============================================================================


def compute_dhash(image_bgr: np.ndarray, hash_size: int = 8) -> np.ndarray:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    return diff.flatten()


def hamming_distance(h1: np.ndarray, h2: np.ndarray) -> int:
    return int(np.sum(h1 != h2))


def is_fullscreen_slide(image_bgr: np.ndarray) -> tuple[bool, float, float]:
    """Analyse le haut et le bas de l'image pour détecter un Ruban ou une Barre des tâches."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Isoler les bandes de 6% en haut (Ruban) et en bas (Barre des tâches)
    top_strip = gray[0 : int(h * 0.06), :]
    bottom_strip = gray[int(h * 0.94) : h, :]

    # Détecter les contours forts
    top_edges = cv2.Canny(top_strip, 50, 150)
    bottom_edges = cv2.Canny(bottom_strip, 50, 150)

    # Ratio de pixels appartenant à un contour (lignes, texte, icones)
    top_density = np.mean(top_edges > 0)
    bottom_density = np.mean(bottom_edges > 0)

    # Vrai si les deux bords sont "propres" (faible densité visuelle)
    is_clean = (top_density < MAX_UI_EDGE_DENSITY) and (
        bottom_density < MAX_UI_EDGE_DENSITY
    )
    return bool(is_clean), float(top_density), float(bottom_density)


def analyze_pdf(pdf_path: Path) -> list[Image.Image]:
    print(f"\n[>] Analyse de : {pdf_path.name}")
    doc = fitz.open(pdf_path)

    kept_images: list[Image.Image] = []
    kept_hashes: list[np.ndarray] = []
    total_slides = len(doc)

    for i in range(total_slides):
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=150)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )

        if pix.n == 4:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)

        # 1. Rejeter les Faux-Slides (Bureau, Ruban PowerPoint, Fenêtré)
        is_fs, t_den, b_den = is_fullscreen_slide(img_bgr)
        if not is_fs:
            print(
                f"  [-] Slide {i + 1:02d}/{total_slides} : Rejeté (Bureau/Fenêtré détecté - Densité: Haut={t_den:.3f}, Bas={b_den:.3f})"
            )
            continue

        # 2. Dédoublonnage global (dHash)
        current_hash = compute_dhash(img_bgr)
        is_duplicate = False

        for idx, prev_hash in enumerate(kept_hashes):
            dist = hamming_distance(current_hash, prev_hash)
            if dist <= HASH_TOLERANCE:
                print(
                    f"  [-] Slide {i + 1:02d}/{total_slides} : Rejeté (Doublon du slide retenu n°{idx + 1}, dist={dist})"
                )
                is_duplicate = True
                break

        if is_duplicate:
            continue

        print(f"  [+] Slide {i + 1:02d}/{total_slides} : Gardé (Plein écran propre)")
        kept_hashes.append(current_hash)

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        kept_images.append(Image.fromarray(img_rgb))

    doc.close()
    return kept_images


def main():
    parser = argparse.ArgumentParser(
        description="Filtre ultra-rapide pour nettoyer les PDF de slides extraits."
    )
    parser.add_argument(
        "input_pdf", nargs="*", help="Fichiers PDF. Si vide, cherche dans input/"
    )
    args = parser.parse_args()

    IN_DIR = Path("input")
    OUT_DIR = Path("output_slides_filtered")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prendre les PDF demandés ou tout scanner dans input/
    if args.input_pdf:
        pdf_files = [Path(p) for p in args.input_pdf if Path(p).is_file()]
    else:
        if not IN_DIR.exists():
            print(f"Dossier '{IN_DIR}' introuvable.")
            sys.exit(1)
        pdf_files = [
            p
            for p in IN_DIR.iterdir()
            if p.suffix.lower() == ".pdf" and not p.name.endswith("_filtered.pdf")
        ]

    if not pdf_files:
        print(f"Aucun fichier PDF trouvé dans '{IN_DIR}'.")
        sys.exit(0)

    for pdf_path in pdf_files:
        filtered_slides = analyze_pdf(pdf_path)

        if not filtered_slides:
            print(f"  [!] Attention : Aucun slide n'a survécu pour {pdf_path.name}.")
            continue

        # Écriture dans output/
        out_path = OUT_DIR / f"{pdf_path.stem}_filtered.pdf"
        filtered_slides[0].save(
            out_path, save_all=True, append_images=filtered_slides[1:], quality=95
        )
        print(
            f"  => Enregistré : {out_path} ({len(filtered_slides)} slides finaux au lieu de {len(fitz.open(pdf_path))})"
        )


if __name__ == "__main__":
    main()
