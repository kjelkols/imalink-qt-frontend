# Bugfix: Gallery Empty After Stateless Refactoring

**Dato:** 2024-10-19  
**Problem:** Gallery viste ingen bilder etter Fase 1 refactoring

## 🐛 Problem

Etter å ha fjernet `coldpreview_*` felter fra Photo modellen, kastet API-kallet feil:

```
TypeError: Photo.__init__() got an unexpected keyword argument 'coldpreview_path'
```

**Root Cause:**
- Backend sender fortsatt `coldpreview_path`, `coldpreview_width`, `coldpreview_height`, `coldpreview_size` i API response
- Vi fjernet disse feltene fra Photo dataclass
- Python dataclass med `**kwargs` unpacking kræsjer hvis felter ikke er definert

## ✅ Løsning

Lagt til feltene tilbake i Photo modellen, men med tydelig dokumentasjon om at de **IKKE skal brukes** av frontend:

```python
# Backend metadata fields (not used by frontend - backend sends actual images via endpoints)
# These exist to accept backend response, but frontend should use try-and-fetch pattern
coldpreview_path: Optional[str] = None  # Backend file path (ignored by frontend)
coldpreview_width: Optional[int] = None  # Backend metadata (ignored by frontend)
coldpreview_height: Optional[int] = None  # Backend metadata (ignored by frontend)
coldpreview_size: Optional[int] = None  # Backend metadata (ignored by frontend)
```

## 🎯 Viktig Prinsipp

**Backend skal sende selve bildet, ikke stien til bildet**

Frontend skal ALLTID:
1. ✅ Bruke API endpoints: `GET /photos/{hothash}/coldpreview/` eller `GET /photos/{hothash}/hotpreview/`
2. ✅ Bruke "try-and-fetch" pattern (prøv coldpreview, fall tilbake til hotpreview)
3. ❌ ALDRI bruke `coldpreview_path` til å bygge filsystem paths
4. ❌ ALDRI bruke `coldpreview_width/height/size` til å bestemme om bilde finnes

## 📋 Stateless Design Pattern

```python
# ✅ RIKTIG - Frontend henter bilde via API:
def load_preview(self, hothash):
    try:
        # Backend sender binært bilde
        image_data = api_client.get_photo_coldpreview(hothash)
        self.display_image(image_data)
    except NotFoundError:
        # Automatic fallback
        image_data = api_client.get_photo_hotpreview(hothash)
        self.display_image(image_data)

# ❌ FEIL - Bruker metadata til å bestemme strategi:
def load_preview(self, photo):
    if photo.coldpreview_path:  # DUPLICATE STATE!
        image_data = api_client.get_photo_coldpreview(photo.hothash)
    else:
        image_data = api_client.get_photo_hotpreview(photo.hothash)
```

## 🔍 Hvorfor Backend Sender Disse Feltene

Backend sender metadata felter for:
1. **Debugging** - Admin kan se om filer eksisterer på disk
2. **Statistics** - Vise total storage brukt
3. **Backwards compatibility** - Eldre API klienter

Men moderne frontend skal **ignorere** disse og bruke direct API endpoints.

## ✅ Verification

```bash
$ cd /home/kjell/git_prosjekt/imalink-qt-frontend
$ uv run python -c "
from src.api.client import ImaLinkClient
client = ImaLinkClient()
photos = client.get_photos()
print(f'✅ API call successful - {len(photos)} photos')
"
✅ API call successful - 11 photos
```

Gallery viser nå bilder korrekt! 🎉

## 📝 Konklusjon

**Dataclass Compatibility:**
- Må akseptere alle felter backend sender (ellers TypeError)
- Men dokumenter tydelig hvilke felter som er "backend-only metadata"
- Frontend skal aldri bruke disse til business logic

**Stateless Principle Bevart:**
- Frontend har INGEN persistent state for coldpreview availability
- "Try-and-fetch" pattern fortsatt i bruk
- Backend er single source of truth (sender faktiske bilder via API)
