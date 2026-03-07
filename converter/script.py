from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import cv2
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DEFAULT_MODEL_FILE = "RealESRGAN_x4plus.pth"
DEFAULT_SCALE = 2
DEFAULT_OUTPUT_FORMAT = "original"
DEFAULT_WEBP_QUALITY = 90
DEFAULT_JPG_QUALITY = 95
VALID_OUTPUT_FORMATS = {"original", "png", "webp", "jpg"}


def load_env_file(base_dir: Path) -> None:
    env_path = base_dir / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_project_paths() -> tuple[Path, Path, Path]:
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    models_dir = base_dir / "ai" / "realesrgan" / "models"
    return input_dir, output_dir, models_dir


def iter_images(input_dir: Path) -> Iterable[Path]:
    for item in input_dir.iterdir():
        if item.is_file() and item.suffix.lower() in VALID_EXTENSIONS:
            yield item


def ask_choice(prompt: str, options: set[str], default: str) -> str:
    ordered = ["original", "png", "webp", "jpg"]
    printable = "/".join([item for item in ordered if item in options])
    while True:
        raw = input(f"{prompt} [{printable}] (padrao: {default}): ").strip().lower()
        value = raw or default
        if value in options:
            return value
        print("Opcao invalida. Tente novamente.")


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    default_text = "s" if default_yes else "n"
    while True:
        raw = input(f"{prompt} [s/n] (padrao: {default_text}): ").strip().lower()
        if not raw:
            return default_yes
        if raw in {"s", "sim", "y", "yes"}:
            return True
        if raw in {"n", "nao", "não", "no"}:
            return False
        print("Resposta invalida. Digite s ou n.")


def resolve_output_file(image_path: Path, output_dir: Path, output_format: str) -> Path:
    if output_format == "webp":
        return output_dir / image_path.with_suffix(".webp").name
    if output_format == "png":
        return output_dir / image_path.with_suffix(".png").name
    if output_format == "jpg":
        return output_dir / image_path.with_suffix(".jpg").name
    return output_dir / image_path.name


def get_save_params(output_format: str, webp_quality: int, jpg_quality: int) -> list[int]:
    if output_format == "webp":
        return [cv2.IMWRITE_WEBP_QUALITY, webp_quality]
    if output_format == "png":
        return [cv2.IMWRITE_PNG_COMPRESSION, 3]
    if output_format == "jpg":
        return [cv2.IMWRITE_JPEG_QUALITY, jpg_quality]
    return []


def load_image(image_path: Path):
    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"[AVISO] Arquivo ignorado (invalido/corrompido): {image_path.name}")
        return None
    return img


def save_image(
    output_file: Path,
    image,
    output_format: str,
    webp_quality: int,
    jpg_quality: int,
) -> bool:
    params = get_save_params(output_format, webp_quality, jpg_quality)
    ok = cv2.imwrite(str(output_file), image, params)
    if not ok:
        print(f"[ERRO] Falha ao salvar imagem: {output_file.name}")
        return False
    print(f"[OK] Salvo em: {output_file.name}")
    return True


def build_upsampler(model_path: Path, use_half: bool) -> RealESRGANer:
    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=4,
    )

    return RealESRGANer(
        scale=4,
        model_path=str(model_path),
        model=model,
        tile=0,
        tile_pad=10,
        pre_pad=0,
        half=use_half,
        gpu_id=0 if torch.cuda.is_available() else None,
    )


def convert_only_image(
    image_path: Path,
    output_dir: Path,
    output_format: str,
    webp_quality: int,
    jpg_quality: int,
) -> bool:
    img = load_image(image_path)
    if img is None:
        return False

    output_file = resolve_output_file(image_path, output_dir, output_format)
    try:
        return save_image(output_file, img, output_format, webp_quality, jpg_quality)
    except OSError as exc:
        print(f"[ERRO] Nao foi possivel converter {image_path.name}: {exc}")
        return False


def run_upscale_for_image(
    upsampler: RealESRGANer,
    image_path: Path,
    output_dir: Path,
    scale: int,
    output_format: str,
    webp_quality: int,
    jpg_quality: int,
) -> bool:
    img = load_image(image_path)
    if img is None:
        return False

    output_file = resolve_output_file(image_path, output_dir, output_format)

    try:
        output, _ = upsampler.enhance(img, outscale=scale)
        return save_image(output_file, output, output_format, webp_quality, jpg_quality)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"[ERRO] Nao foi possivel processar {image_path.name}: {exc}")
        return False


def validate_environment(
    input_dir: Path,
    models_dir: Path,
    model_file: str,
    apply_upscale: bool,
) -> bool:
    if not input_dir.exists():
        print(f"[ERRO] Pasta de entrada nao encontrada: {input_dir}")
        return False

    if apply_upscale:
        if not models_dir.exists():
            print(f"[ERRO] Pasta de modelos nao encontrada: {models_dir}")
            return False

        model_path = models_dir / model_file
        if not model_path.exists():
            print(f"[ERRO] Arquivo de modelo .pth nao encontrado: {model_path}")
            return False

    return True


def run_batch() -> None:
    input_dir, output_dir, models_dir = get_project_paths()
    load_env_file(base_dir=input_dir.parent)

    model_file = os.getenv("REALESRGAN_MODEL_FILE", DEFAULT_MODEL_FILE)

    try:
        scale = int(os.getenv("REALESRGAN_SCALE", str(DEFAULT_SCALE)))
    except ValueError:
        print(f"[AVISO] REALESRGAN_SCALE invalido. Usando {DEFAULT_SCALE}.")
        scale = DEFAULT_SCALE

    env_output_format = os.getenv("REALESRGAN_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT)
    env_output_format = env_output_format.lower().strip()
    if env_output_format not in VALID_OUTPUT_FORMATS:
        print(
            "[AVISO] REALESRGAN_OUTPUT_FORMAT invalido. "
            f"Usando '{DEFAULT_OUTPUT_FORMAT}'."
        )
        env_output_format = DEFAULT_OUTPUT_FORMAT

    try:
        webp_quality = int(os.getenv("REALESRGAN_WEBP_QUALITY", str(DEFAULT_WEBP_QUALITY)))
    except ValueError:
        print(f"[AVISO] REALESRGAN_WEBP_QUALITY invalido. Usando {DEFAULT_WEBP_QUALITY}.")
        webp_quality = DEFAULT_WEBP_QUALITY

    try:
        jpg_quality = int(os.getenv("REALESRGAN_JPG_QUALITY", str(DEFAULT_JPG_QUALITY)))
    except ValueError:
        print(f"[AVISO] REALESRGAN_JPG_QUALITY invalido. Usando {DEFAULT_JPG_QUALITY}.")
        jpg_quality = DEFAULT_JPG_QUALITY

    scale = max(1, scale)
    webp_quality = min(100, max(1, webp_quality))
    jpg_quality = min(100, max(1, jpg_quality))

    output_format = ask_choice(
        "Formato final das imagens",
        VALID_OUTPUT_FORMATS,
        env_output_format,
    )
    apply_upscale = ask_yes_no("Deseja aplicar upscale para melhorar a qualidade?", default_yes=True)

    if not validate_environment(
        input_dir=input_dir,
        models_dir=models_dir,
        model_file=model_file,
        apply_upscale=apply_upscale,
    ):
        return

    upsampler = None
    if apply_upscale:
        model_path = models_dir / model_file
        upsampler = build_upsampler(
            model_path=model_path,
            use_half=torch.cuda.is_available(),
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    images = list(iter_images(input_dir))

    if not images:
        print("Nenhuma imagem valida encontrada em input (jpg, jpeg, png).")
        return

    print(f"Iniciando processamento de {len(images)} imagem(ns)...")
    if apply_upscale:
        print("Modo: conversao + upscale")
        print(f"Modelo: {model_file} | Escala: {scale}x")
        print(f"GPU CUDA ativa: {'sim' if torch.cuda.is_available() else 'nao'}")
    else:
        print("Modo: somente conversao")
    print(f"Formato de saida: {output_format}")

    success = 0
    failed = 0

    for index, image_path in enumerate(images, start=1):
        print(f"[{index}/{len(images)}] Processando: {image_path.name}")
        if apply_upscale and upsampler is not None:
            ok = run_upscale_for_image(
                upsampler=upsampler,
                image_path=image_path,
                output_dir=output_dir,
                scale=scale,
                output_format=output_format,
                webp_quality=webp_quality,
                jpg_quality=jpg_quality,
            )
        else:
            ok = convert_only_image(
                image_path=image_path,
                output_dir=output_dir,
                output_format=output_format,
                webp_quality=webp_quality,
                jpg_quality=jpg_quality,
            )

        if ok:
            success += 1
        else:
            failed += 1

    print("\nResumo:")
    print(f"Sucesso: {success}")
    print(f"Falhas: {failed}")
    print(f"Saida: {output_dir}")


def main() -> None:
    run_batch()


if __name__ == "__main__":
    main()
