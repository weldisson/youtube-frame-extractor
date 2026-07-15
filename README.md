# YouTube Frame & Subtitle Extractor 🎥🖼️

Uma aplicação web local moderna (Backend em Python/FastAPI e Frontend em HTML/JS com Glassmorphism) que permite extrair frames de qualquer vídeo do YouTube em intervalos de tempo personalizados (ex: de 1 em 1 segundo, etc.), desenhar a legenda correspondente na imagem e baixar tudo em um pacote ZIP comprimido.

Esta aplicação foi desenvolvida e otimizada para contornar as restrições e bloqueios recentes do YouTube (como erros HTTP 403 Forbidden e "The page needs to be reloaded") através de técnicas de spoofing de player (Android client emulation) e fallback dinâmico de legendas.

---

## ✨ Funcionalidades

- **Extração Customizável:** Extraia frames com intervalos de tempo precisos (ex: a cada 1 segundo, 1.5s, 5s, etc.).
- **Legendas Embutidas:** O app busca a legenda ativa em cada frame e a desenha na parte inferior com fundo semi-transparente para máxima legibilidade.
- **Nomenclatura Inteligente:** Os arquivos de imagem são salvos no formato `{tempo_segundos}s_{legenda_sanitizada}.jpg` para fácil identificação.
- **Interface Premium:** Frontend moderno com tema escuro (Dark Mode), efeito Glassmorphism, barra de progresso em tempo real, galeria responsiva com visualizador individual (Lightbox) e botão de download do ZIP completo.
- **Performance Otimizada:** Exclusão automática do vídeo original em disco após a extração dos frames para poupar espaço de armazenamento.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.9+, FastAPI, Uvicorn, OpenCV (extração de frames), Pillow/numpy.
- **Downloader Engine:** `yt-dlp` (com spoofing do player Android) e `youtube-transcript-api`.
- **Frontend:** HTML5, Vanilla CSS3 (com Glassmorphism e animações fluidas), JavaScript (ES6).

---

## 🚀 Como Executar o App Localmente

### Pré-requisitos
Certifique-se de ter o Python 3.9+ instalado no seu computador.

### Passo 1: Entrar no diretório do projeto
Abra o seu terminal e navegue até a pasta do projeto:
```bash
cd /Users/weldissonaraujo/.gemini/antigravity/scratch/youtube_frame_extractor
```

### Passo 2: Iniciar a aplicação
O projeto já conta com um script automatizado que ativa o ambiente virtual (`venv`) e inicializa o servidor de forma limpa:
```bash
./start.sh
```

### Passo 3: Acessar no Navegador
Abra o seu navegador de preferência e acesse:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 📁 Estrutura do Projeto

```text
youtube_frame_extractor/
├── app/
│   ├── __init__.py
│   ├── main.py          # Endpoints do FastAPI e HTML do Frontend
│   ├── downloader.py    # Gerenciador de downloads do YouTube e legendas
│   ├── processor.py     # Motor de extração de frames, desenho de legenda e ZIP
│   └── exceptions.py    # Exceções customizadas
├── tests/               # Conjunto de testes E2E e mocks offline
├── requirements.txt     # Dependências do projeto
├── start.sh             # Script de inicialização automática
├── .gitignore           # Evita o envio de vídeos, imagens e caches para o Git
└── README.md            # Documentação do projeto
```

---

## 🧪 Rodando os Testes E2E (Offline)
Para rodar a suíte de testes integrada offline do projeto:
```bash
./venv/bin/python tests/test_runner.py
```
