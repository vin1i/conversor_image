from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import cv2
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_MODEL_FILE = "RealESRGAN_x4plus.pth"
DEFAULT_SCALE = 2
DEFAULT_OUTPUT_FORMAT = "original"
# Valores ajustados para reduzir o tamanho final dos arquivos,
# mantendo boa qualidade visual.
DEFAULT_WEBP_QUALITY = 80
DEFAULT_JPG_QUALITY = 85
VALID_OUTPUT_FORMATS = {"original", "png", "webp", "jpg"}

# RealESRGAN execution defaults (tunable via env)
DEFAULT_TILE = 0
DEFAULT_TILE_PAD = 10
DEFAULT_PRE_PAD = 0
DEFAULT_GPU_ID = 0


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


def ask_dimensions() -> tuple[int | None, int | None, bool]:
    """Ask user for target dimensions and aspect behavior."""
    apply_resize = ask_yes_no("Deseja redimensionar as imagens?", default_yes=False)
    if not apply_resize:
        return None, None, True

    while True:
        try:
            width_input = input("Digite a largura (width) em pixels (deixe vazio para manter): ").strip()
            height_input = input("Digite a altura (height) em pixels (deixe vazio para manter): ").strip()

            width = int(width_input) if width_input else None
            height = int(height_input) if height_input else None

            if width is not None and width < 1:
                print("Largura deve ser >= 1.")
                continue
            if height is not None and height < 1:
                print("Altura deve ser >= 1.")
                continue

            if width is None and height is None:
                print("Especifique ao menos largura ou altura.")
                continue

            keep_aspect = True
            if width is not None and height is not None:
                keep_aspect = ask_yes_no(
                    "Manter proporcao usando largura/altura como limite (sem distorcer)?",
                    default_yes=True,
                )

            return width, height, keep_aspect
        except ValueError:
            print("Entrada invalida. Digite numeros inteiros.")


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
        # 0 = sem compressao, 9 = maxima compressao (mais lento, arquivos menores)
        return [cv2.IMWRITE_PNG_COMPRESSION, 9]
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


def build_upsampler(
    model_path: Path,
    use_half: bool,
    tile: int,
    tile_pad: int,
    pre_pad: int,
    gpu_id: int | None,
) -> RealESRGANer:
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
        tile=tile,
        tile_pad=tile_pad,
        pre_pad=pre_pad,
        half=use_half,
        gpu_id=gpu_id,
    )


def _choose_resize_interpolation(src_w: int, src_h: int, dst_w: int, dst_h: int) -> int:
    # INTER_AREA preserves details better when shrinking, INTER_CUBIC is softer when enlarging.
    if dst_w < src_w or dst_h < src_h:
        return cv2.INTER_AREA
    return cv2.INTER_CUBIC


def resize_image(image, width: int | None, height: int | None, keep_aspect: bool = True):
    """Resize image. Supports exact size or bounded resize preserving aspect ratio."""
    h, w = image.shape[:2]

    if width is None and height is not None:
        ratio = height / h
        width = int(w * ratio)
    elif height is None and width is not None:
        ratio = width / w
        height = int(h * ratio)

    if width and height:
        if keep_aspect:
            ratio = min(width / w, height / h)
            width = max(1, int(w * ratio))
            height = max(1, int(h * ratio))
        interpolation = _choose_resize_interpolation(w, h, width, height)
        return cv2.resize(image, (width, height), interpolation=interpolation)
    return image


def convert_only_image(
    image_path: Path,
    output_dir: Path,
    output_format: str,
    webp_quality: int,
    jpg_quality: int,
    resize_width: int | None = None,
    resize_height: int | None = None,
    keep_aspect: bool = True,
) -> bool:
    img = load_image(image_path)
    if img is None:
        return False

    if resize_width or resize_height:
        img = resize_image(img, resize_width, resize_height, keep_aspect=keep_aspect)

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
    resize_width: int | None = None,
    resize_height: int | None = None,
    keep_aspect: bool = True,
) -> bool:
    img = load_image(image_path)
    if img is None:
        return False

    output_file = resolve_output_file(image_path, output_dir, output_format)

    try:
        output, _ = upsampler.enhance(img, outscale=scale)

        if resize_width or resize_height:
            output = resize_image(output, resize_width, resize_height, keep_aspect=keep_aspect)

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

    # Small speedup on CUDA for some conv workloads
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True

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

    try:
        tile = int(os.getenv("REALESRGAN_TILE", str(DEFAULT_TILE)))
    except ValueError:
        print(f"[AVISO] REALESRGAN_TILE invalido. Usando {DEFAULT_TILE}.")
        tile = DEFAULT_TILE

    try:
        tile_pad = int(os.getenv("REALESRGAN_TILE_PAD", str(DEFAULT_TILE_PAD)))
    except ValueError:
        print(f"[AVISO] REALESRGAN_TILE_PAD invalido. Usando {DEFAULT_TILE_PAD}.")
        tile_pad = DEFAULT_TILE_PAD

    try:
        pre_pad = int(os.getenv("REALESRGAN_PRE_PAD", str(DEFAULT_PRE_PAD)))
    except ValueError:
        print(f"[AVISO] REALESRGAN_PRE_PAD invalido. Usando {DEFAULT_PRE_PAD}.")
        pre_pad = DEFAULT_PRE_PAD

    try:
        env_gpu_id = os.getenv("REALESRGAN_GPU_ID", str(DEFAULT_GPU_ID)).strip().lower()
        gpu_id = None if env_gpu_id in {"none", "cpu", ""} else int(env_gpu_id)
    except ValueError:
        print(f"[AVISO] REALESRGAN_GPU_ID invalido. Usando {DEFAULT_GPU_ID}.")
        gpu_id = DEFAULT_GPU_ID

    tile = max(0, tile)
    tile_pad = max(0, tile_pad)
    pre_pad = max(0, pre_pad)

    output_format = ask_choice(
        "Formato final das imagens",
        VALID_OUTPUT_FORMATS,
        env_output_format,
    )
    apply_upscale = ask_yes_no("Deseja aplicar upscale para melhorar a qualidade?", default_yes=True)
    resize_width, resize_height, keep_aspect = ask_dimensions()

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
            tile=tile,
            tile_pad=tile_pad,
            pre_pad=pre_pad,
            gpu_id=(gpu_id if torch.cuda.is_available() else None),
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
    if resize_width or resize_height:
        print(f"Redimensionamento: {resize_width or 'auto'} x {resize_height or 'auto'}")
        print(f"Manter proporcao: {'sim' if keep_aspect else 'nao'}")

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
                resize_width=resize_width,
                resize_height=resize_height,
                keep_aspect=keep_aspect,
            )
        else:
            ok = convert_only_image(
                image_path=image_path,
                output_dir=output_dir,
                output_format=output_format,
                webp_quality=webp_quality,
                jpg_quality=jpg_quality,
                resize_width=resize_width,
                resize_height=resize_height,
                keep_aspect=keep_aspect,
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
