# 🚀 Private RAG Desktop Client

**A fully offline, privacy-focused desktop application for chatting with your documents using local LLMs.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black.svg)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 Overview

**Private RAG Desktop Client** is a local-first AI assistant that lets you query your documents (PDF, DOCX, TXT) without sending any data to the cloud. It uses **Ollama** for local LLM inference, **ChromaDB** for vector storage, and **PyQt6** for a responsive, modern desktop interface.

Perfect for lawyers, researchers, or anyone who needs to extract answers from sensitive documents while keeping everything **100% offline**.

## 📸 Screenshots

![Private RAG Desktop Client - Chat Interface](https://github.com/user-attachments/assets/fef7e088-2148-46f5-b882-0a1c262ef1d1)
*Private RAG Desktop Client - Main Interface (Dark Theme)*

## ✨ Features

- 🔒 **100% Offline & Private**: No data leaves your machine.
- 📂 **Multi-format Support**: Parse `.pdf`, `.docx`, and `.txt` files.
- 🤖 **Multiple Local Models**: Supports `llama3`, `mistral`, and `phi3` out of the box.
- ⚡ **Streaming Responses**: See the answer appear word-by-word, just like ChatGPT.
- 🎨 **Dark & Light Themes**: Switch instantly without restarting.
- 🌍 **Localization Ready**: English by default, with architecture for Russian (i18n).
- 🛡️ **Robust Error Handling**: Gracefully handles scanned PDFs, missing models, and Ollama disconnection.

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **GUI**: PyQt6
- **Local LLM**: Ollama (llama3 / mistral / phi3)
- **Vector Database**: ChromaDB
- **Text Splitting**: LangChain
- **Build**: PyInstaller

## 🚀 Getting Started

### Prerequisites

- Windows 10/11 (64-bit)
- [Ollama](https://ollama.com/) installed and running

### 1. Install Ollama (PowerShell)

Open **PowerShell** and run the following command to install Ollama automatically:

```powershell
irm https://ollama.com/install.ps1 | iex
```

*(Alternatively, download the installer manually from [ollama.com/download](https://ollama.com/download).)*

### 2. Download the Models

The application supports three LLMs. You can download them all or pick one. Open PowerShell and run:

```powershell
# Main chat models (choose one or more)
ollama pull llama3
ollama pull mistral
ollama pull phi3

# Required embedding model (for document indexing)
ollama pull nomic-embed-text
```

*Model sizes: Llama 3 (~4.7 GB), Mistral (~4.1 GB), Phi-3 (~2.3 GB), Nomic-Embed (~274 MB).*

### 3. Run the Application

- **Option A (Ready-to-use)**: Download the `.zip` from the [Releases](../../releases) page, extract it, and run `RAG_Desktop_Client.exe`.
- **Option B (From Source)**:
  ```bash
  git clone https://github.com/mountspir-coder/private-rag-desktop-client.git
  cd private-rag-desktop-client
  python -m venv .venv
  .\.venv\Scripts\activate
  pip install -r requirements.txt
  python main.py
  ```

## 📁 Project Structure

```text
rag_desktop_client/
├── core/                  # RAG engine, Ollama client
├── parsers/               # PDF, DOCX, TXT extractors
├── ui/                    # PyQt6 interface, themes, workers
├── main.py                # Entry point
├── requirements.txt
└── README.md
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
