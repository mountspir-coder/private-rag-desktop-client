# 📄 PROJECT_STATE — Private RAG Desktop Client

## 1. Метаданные и статус

| Поле | Значение |
|---|---|
| **Название проекта** | Private RAG Desktop Client (Local AI) |
| **Стек** | Python 3.10+, PyQt6, Ollama (llama3 + nomic-embed-text), ChromaDB, LangChain, PyInstaller |
| **Текущая версия/этап** | **MVP v1.0** — Проект завершён. Все 6 этапов закрыты. |
| **Статус** | 🟢 Готов к релизу / портфолио |
| **Готово** | Этапы 1, 2, 3, 4, 5, 6 |
| **В работе** | — |
| **Следующий** | Пост-MVP улучшения (см. Бэклог) |
| **Платформа** | Windows 10/11 (x64) |

---

## 2. Архитектура (как это работает)

**Краткая схема (end-to-end):**

При старте `startup_check.py` проверяет доступность Ollama (`ping()`) и наличие моделей (`has_model()`). Если всё в порядке — открывается GUI.

Пользователь нажимает `Add Document` → `QFileDialog` → `IndexingWorker(QThread)` → `document_parser.extract_text()` → `rag_engine.index_document()` (чанкинг 800/150 → эмбеддинги `nomic-embed-text` → ChromaDB) → сигнал `indexed`.

Пользователь задаёт вопрос → `ChatWorker(QThread)` → `rag_engine.ask_stream()` → top-3 чанка из ChromaDB → промпт с системной инструкцией → `llama3` (Ollama) со `stream=True` → сигнал `chunk_received` на каждый токен → `MainWindow._flush_streaming()` (инкрементальная вставка дельты через `QTextCursor`, без перерисовки всего чата) → плавный вывод без мерцания → по завершении `finished()` → `_finalize_last_bot_message()` → единичный full re-render с Markdown.

**Структура проекта:**

```
rag_desktop_client/
├── chroma_db/                    # PersistentClient storage (next to .exe in build)
├── core/
│   ├── __init__.py
│   ├── ollama_client.py          # Ollama wrapper (host override, ping, has_model)
│   └── rag_engine.py             # ChromaDB + chunking + retrieval + ask/ask_stream
├── parsers/
│   ├── __init__.py
│   ├── document_parser.py        # PDF/DOCX/TXT + typed exceptions
│   └── _test_files/
├── ui/
│   ├── __init__.py
│   ├── i18n.py                   # en (default) + ru (stub)
│   ├── styles.py                 # DARK_THEME + LIGHT_THEME
│   ├── workers.py                # IndexingWorker + ChatWorker (QThread)
│   └── main_window.py            # QMainWindow + streaming + QTextCursor rendering
├── main.py                       # Entry point + rotating logging + excepthook
├── startup_check.py              # Ollama & models validation on launch
├── rag_client.spec               # PyInstaller build configuration
├── requirements.txt              # Fixed production dependencies
├── README.md                     # English documentation for GitHub
├── sample_stage1.txt
├── app.log                       # rotating, max 1MB × 3
└── PROJECT_STATE.md
```

---

## 3. Журнал фиксов и решений (Fix Log)

*(Сокращённая версия предыдущих этапов + новые фиксы Этапа 6)*

*   **Fix 1–4:** Решение проблем с `OLLAMA_HOST=0.0.0.0`, API `ollama.Client`, форматом `/api/tags` и кодировкой `cp1251` в `.txt`.
*   **Fix 5–6:** Мгновенная смена темы (QSS) и локализация без Qt Linguist (словари `_STRINGS`).
*   **Fix 7–10:** Защита QThread от GC, разблокировка UI при исключениях, двухслойная защита форматов, traceback в логах (`logger.exception`).
*   **Fix 11:** `QTextDocumentFragment.toHtml()` возвращает полный HTML-документ. Вложенность ломала парсер Qt, и сообщения не отображались. **Решение:** переход на `QTextCursor.insertFragment()` — прямая работа с документом без промежуточного HTML.
*   **Fix 12:** Мерцание чата при стриминге из-за `clear()` на каждый токен. **Решение:** `_flush_streaming()` вставляет только дельту (новые символы) в конец, без перерисовки всего документа. Полный рендер (с Markdown) — только по завершении ответа.
*   **Fix 13:** Ошибка `No module named PyInstaller` из-за несовместимости версии `6.3.0` с Python 3.13. **Решение:** установка актуальной версии через `pip install pyinstaller` (подобралась `6.22.1`).
*   **Fix 14:** При сборке `.exe` папка `chroma_db` создавалась бы во временной папке `_MEIPASS`. **Решение:** в `core/rag_engine.py` добавлена проверка `sys.frozen` и `Path(sys.executable).resolve().parent`, чтобы база создавалась рядом с `.exe`.
*   **Fix 15:** PyInstaller не видел скрытые зависимости `tiktoken` и `chromadb`. **Решение:** в `rag_client.spec` добавлены `tiktoken_ext`, `tiktoken_ext.openai_public` и `collect_submodules('chromadb')`.

---

## 4. Бэклог

### ✅ Сделано (MVP v1.0)

- ☑ **Ядро:** RAG-движок, ChromaDB, Ollama API (embeddings, chat, stream).
- ☑ **Парсинг:** PDF (pypdf), DOCX (python-docx), TXT (utf-8/cp1251).
- ☑ **UI:** PyQt6, QSplitter, Dark/Light темы, i18n.
- ☑ **Многопоточность:** QThread воркеры, плавный UI без зависаний.
- ☑ **Стриминг:** По токенам, с Markdown-рендерингом и автоскроллом.
- ☑ **Надёжность:** Startup check (Ollama + модели), Rotating logs.
- ☑ **Сборка:** PyInstaller `.exe` с корректными путями к базе.

### 🔮 Пост-MVP (Идеи для развития)

- □ Поддержка Excel (`.xlsx`) через `openpyxl`.
- □ Префиксы `search_document:` / `search_query:` для `nomic-embed-text` (улучшит поиск в больших документах).
- □ Динамический список моделей из `ollama.list()` вместо захардкоженного `["llama3", "mistral", "phi3"]`.
- □ Отображение источников (chunk previews + distance) под каждым ответом бота.
- □ Переключатель языка в UI (хук `MainWindow.set_language("ru")` уже готов).
- □ CI/CD на GitHub Actions (сборка релизов при пуше тега).

---

## 5. Тесты и валидация

### ✅ Выполнено

**Test 1 — RAG core (Этап 1):** `python -m core.rag_engine` → корректный ответ с контекстом. ✅
**Test 2 — Document parser (Этап 2):** `python -m parsers.document_parser` → `6/6 tests passed`. ✅
**Test 3 — UI Smoke (Этап 3):** Открытие, темы, локализация, тулбар. ✅
**Test 4 — Full Integration (Этап 4–5):** 
  - Индексация `.txt` / `.docx` / ошибки `.pdf` (скан). ✅
  - RAG-вопрос → стриминг → Markdown. ✅
  - Смена темы на лету во время чата. ✅
  - Автоскролл без мерцания (после Fix 12). ✅
**Test 5 — Startup Checks (Этап 6):** 
  - Отключенный Ollama → `QMessageBox` с инструкцией. ✅
  - Отсутствие модели → `QMessageBox` с `ollama pull`. ✅

**Test 6 — Build & Executable (Этап 6):**
- `python -m PyInstaller rag_client.spec` → успешная сборка без ошибок.
- Запуск `dist\RAG_Desktop_Client.exe` → старт, проверка окружения, UI открывается.
- Создание папки `chroma_db` рядом с `.exe`.
- Добавление файла, индексация, вопрос, стриминг ответа — **всё работает**. ✅ PASSED.

### 📌 Известные ограничения (приняты в MVP v1.0)

- Сканированные PDF (без текстового слоя) не поддерживаются (явная ошибка, не silent fail).
- Markdown применяется только в конце стриминга (одна перерисовка) — компромисс ради отсутствия мерцания.
- `httpx` пишет INFO-логи в консоль/файл (можно заглушить `logging.getLogger("httpx").setLevel(logging.WARNING)`).