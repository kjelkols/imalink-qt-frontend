# Utviklerinformasjon for ImaLink Qt Frontend

## 🔧 Kritisk prosjektinformasjon

**VIKTIG - LES DETTE FØRST VED ALLE UTVIKLINGSOPPGAVER:**

### Pakkehåndtering
- **Pakkehandler**: `uv` (IKKE pip)
- **Installasjon av pakker**: `uv pip install <pakke>`
- **Virtual environment**: `uv venv` for å opprette, `source .venv/bin/activate` for å aktivere

### Utviklingsplattform
- **Utviklingsmiljø**: WSL (Windows Subsystem for Linux)
- **Målplattform**: Windows (applikasjonen skal kjøre på Windows)
- **Kryssplattform-kompatibilitet**: Koden må fungere både på WSL og Windows

### Nettverkskonfigurasjon
- **Backend lokasjon**: Kan kjøre på Windows mens frontend utvikles på WSL
- **API URL for WSL→Windows**: Bruk `http://172.x.x.x:8000/api/v1` (finn IP med `hostname -I`)
- **API URL for lokal utvikling**: `http://localhost:8000/api/v1`

### Filstier og kompatibilitet
- **Filstier**: Bruk `Path` fra `pathlib` for kryssplattform-kompatibilitet
- **Separatorer**: Unngå hardkodede `/` eller `\` - bruk `Path.joinpath()` eller `/` operator
- **Temp filer**: Bruk `tempfile` modulen for midlertidige filer

### Kommandoer for utviklingsoppgaver

#### Oppsett av nytt miljø:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

#### Legge til ny pakke:
```bash
uv pip install <pakkenavn>
uv pip freeze > requirements.txt  # Oppdater requirements
```

#### Kjøre applikasjonen:
```bash
python main.py
```

#### Finne WSL IP for Windows backend:
```bash
hostname -I  # Første IP er vanligvis riktig
```

### Testing på målplattformen
- Test regelmessig på Windows for å sikre kompatibilitet
- Vær oppmerksom på filsti-problemer og case-sensitivity
- Test nettverkstilkoblinger mellom WSL og Windows

### Qt/PySide6 spesialiteter
- **Import**: Bruk `PySide6` (ikke `PyQt6`)
- **Threading**: Bruk Qt's threading system for API-kall
- **Signaler**: Bruk `pyqtSignal` for kommunikasjon mellom komponenter
- **Resources**: Bilder og stiler ligger i `resources/` mappen

## 📋 Sjekkliste før utvikling
1. ✅ Aktiver virtual environment
2. ✅ Sjekk at `uv` brukes for pakkeinstallasjon
3. ✅ Verifiser API-tilkobling (WSL IP hvis nødvendig)
4. ✅ Test filstier for kryssplattform-kompatibilitet

## 🐛 Vanlige problemer
- **Import errors**: Sjekk at virtual environment er aktivert
- **API connection failed**: Verifiser IP-adresse for WSL→Windows
- **File not found**: Bruk `Path.resolve()` for absolutte stier
- **Qt import issues**: Sjekk at PySide6 er installert med `uv`