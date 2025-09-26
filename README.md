

                        +===========================================================+
                        |   ____                      ___           _           _   |
                        |  / __ \  __ _ _ __  _   _  / _ \_ __ ___ (_) ___  ___| |_ |
                        | / / _` |/ _` | '_ \| | | |/ /_)/ '__/ _ \| |/ _ \/ __| __||
                        || | (_| | (_| | | | | |_| / ___/| | | (_) | |  __/ (__| |_ |
                        | \ \__,_|\__,_|_| |_|\__, \/    |_|  \___// |\___|\___|\__||
                        |  \____/             |___/              |__/               |
                        |        _____                     _       _                |
                        |       /__   \___ _ __ ___  _ __ | | __ _| |_ ___          |
                        |         / /\/ _ \ '_ ` _ \| '_ \| |/ _` | __/ _ \         |
                        |        / / |  __/ | | | | | |_) | | (_| | ||  __/         |
                        |        \/   \___|_| |_| |_| .__/|_|\__,_|\__\___|         |
                        |                           |_|                             |
                        +===========================================================+

# anyProjectTemplate  

**A modular, AI-assisted project template for rapid prototyping.**  
Designed to handle **Android apps, AI backends, or any language/framework** with a consistent bootstrap + planning workflow.  

---

## ✨ Features
- **Bootstrap system** (`tools/bootstrap.py`)  
  - Creates required folders (`debug/`, `memory/`, `planning/`, `vector_db/`, `automation/`).  
  - Sets up Python virtual environment.  
  - Installs project dependencies.  
  - Migrates old config/rules files if needed.  

- **Seed files & planning flow**
  - `PROGRAM_FEATURES.json` → declare what the app should do.  
  - `RESEARCH_GUIDELINES.md` → paste research, constraints, design notes.  
  - `rules.md` → persistent rules & AI guidance.  

- **Vector + JSON storage**
  - Keeps structured knowledge in `memory/todo.json`.  
  - Stores semantic chunks in `vector_db/`.  
  - Both update automatically when you run workflows.  

- **CLI driver (`anyProject.py`)**
  - `init` → Bootstrap + validate repo.  
  - `plan` → Analyze `PROGRAM_FEATURES.json` + `RESEARCH_GUIDELINES.md`, scaffold TODO list.  
  - `scaffold` → (future) build project structures (Android, web, etc.).  
  - `debug` → Tools for running + testing with device (ADB).  

- **Debug tools**
  - `debug/device_config.json` to track devices.  
  - `debug/runner.py` to orchestrate ADB tests (future).  

- **Safety layer**
  - All writes handled by `tools/safe_writer.py` (no accidental overwrites).  
  - Repo integrity checker: `tools/check_integrity.py`.  

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/yourname/anyProjectTemplate.git
cd anyProjectTemplate
```

### 2. Bootstrap the project
```bash
python3 tools/bootstrap.py
```

### 3. Initialize workflow
```bash
python3 anyProject.py init
```

### 4. Fill in planning docs
- Open `PROGRAM_FEATURES.json` and describe app features.  
- Add research into `RESEARCH_GUIDELINES.md`.  

### 5. Generate plan
```bash
python3 anyProject.py plan
```

---

## 🛠 Tooling Overview
- `tools/bootstrap.py` → setup + deps  
- `tools/validate_repo.py` → validate repo structure  
- `tools/clean_repo.py` → remove temp/old files  
- `tools/check_integrity.py` → CRC-like file integrity check  
- `tools/vector_store.py` → vector DB handling  
- `tools/adb_helper.py` → Android device helpers  
- `tools/safe_writer.py` → safe write layer  

---

## 📦 Packaging & Releases
Build a zip for distribution:
```bash
python3 tools/package_release.py
```

Publish release with GitHub CLI:
```bash
gh release create v0.1.0 dist/anyProjectTemplate-v0.1.0-*.zip \
  --title "v0.1.0" \
  --notes "First production-ready template release."
```

---

## 📂 Repo Structure (cleaned)
```
anyProjectTemplate/
├── anyProject.py         # main CLI entrypoint
├── PROGRAM_FEATURES.json # seed file for features
├── RESEARCH_GUIDELINES.md
├── rules.md
├── config.json
├── requirements.txt
├── debug/
│   ├── device_config.json
│   └── runner.py
├── memory/
│   └── todo.json
├── planning/
│   └── .gitkeep
├── vector_db/
│   └── .gitkeep
├── automation/
│   └── .gitkeep
├── tools/
│   ├── bootstrap.py
│   ├── clean_repo.py
│   ├── validate_repo.py
│   ├── check_integrity.py
│   ├── package_release.py
│   ├── adb_helper.py
│   ├── vector_store.py
│   ├── safe_writer.py
│   └── logger.py
└── .gitignore
```

---

## 🔮 Roadmap
- Self-testing UI automation (ADB driven).  
- Expand scaffolding (web, API, cross-lang).  
- Plugin system for project types.  
- CI/CD release automation.  

---

## 📜 License
MIT License. Free to use and modify.  
