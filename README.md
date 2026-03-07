# Conversor Image com RealESRGAN

Projeto para conversao de imagens e melhoria de qualidade (upscale) em lote, com fluxo interativo no terminal.

## Finalidade do Projeto

Este projeto permite:

- Ler imagens de `converter/input/` (`.jpg`, `.jpeg`, `.png`)
- Converter para formato escolhido (`original`, `png`, `webp`, `jpg`)
- Opcionalmente aplicar upscale com RealESRGAN (`.pth`) para melhorar qualidade
- Salvar o resultado em `converter/output/`

Ideal para padronizar imagens para web e melhorar resolucao sem precisar abrir editor manualmente.

## Estrutura de Pastas

```text
conversor_image/
  converter/
    script.py
    requirements.txt
    .env
    input/
    output/
    ai/
      realesrgan/
        models/
          RealESRGAN_x4plus.pth
```

## Requisitos

- Windows
- Python 3.11
- Modelo `.pth` em `converter/ai/realesrgan/models/`

Modelo atual esperado por padrao:

- `RealESRGAN_x4plus.pth`

## Configuracao do Ambiente (venv)

O `venv` deve ser mantido localmente e NAO enviado para o Git.

### 1. Criar ambiente virtual

```bat
cd C:\Users\Vini\Documents\GitHub\conversor_image\converter
py -3.11 -m venv .venv311
```

### 2. Ativar ambiente virtual

```bat
.venv311\Scripts\activate
```

### 3. Instalar dependencias

```bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Como Usar

### 1. Coloque as imagens em `converter/input/`

Formatos aceitos:

- `.jpg`
- `.jpeg`
- `.png`

### 2. Execute o script

```bat
cd C:\Users\Vini\Documents\GitHub\conversor_image\converter
.venv311\Scripts\activate
python script.py
```

### 3. Responda as perguntas no terminal

O script pergunta:

1. Formato final (`original`, `png`, `webp`, `jpg`)
2. Se deseja aplicar upscale (`s`/`n`)

Se escolher upscale, o RealESRGAN sera aplicado antes de salvar no formato escolhido.

## Variaveis de Ambiente (`converter/.env`)

Arquivo usado para defaults do script:

```env
REALESRGAN_MODEL_FILE=RealESRGAN_x4plus.pth
REALESRGAN_SCALE=2
REALESRGAN_OUTPUT_FORMAT=original
REALESRGAN_WEBP_QUALITY=90
REALESRGAN_JPG_QUALITY=95
```

Observacoes:

- O script continua perguntando no terminal e voce pode sobrescrever os defaults na hora.
- `REALESRGAN_SCALE` define o fator de upscale quando ativado.

## Solucao de Problemas

### Erro de modulo (ex: `No module named cv2`)

Significa que as dependencias nao foram instaladas no ambiente ativo.

```bat
.venv311\Scripts\activate
python -m pip install -r requirements.txt
```

### Erro de modelo nao encontrado

Verifique se o arquivo existe em:

- `converter/ai/realesrgan/models/RealESRGAN_x4plus.pth`

### Sair do ambiente virtual

```powershell
deactivate
```

## Fluxo Git Recomendado

Versione:

- `converter/script.py`
- `converter/requirements.txt`
- `README.md`
- `.gitignore`

Nao versione:

- `.venv311/`
- `converter/output/`
- caches temporarios
