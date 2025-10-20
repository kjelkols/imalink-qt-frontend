# Photo Variants Concept

## Grunnkonsept

ImaLink skal støtte at **ett Photo-objekt kan inneholde flere relaterte bildefiler** (varianter). Dette er en av hovedideene bak ImaLink og kan være til stor hjelp for fotografer.

## Arkitektur

### Struktur
```
Photo (logisk enhet)
├── Master: JPEG-fil (primær representasjon)
└── Variants: Liste av relaterte filer
    ├── RAW-original (NEF, CR2, ARW, etc.)
    ├── Bearbeidet versjon (PSD, TIFF, etc.)
    ├── Eksporterte versjoner (web-optimalisert, print, etc.)
    └── Andre variasjoner
```

### Nøkkelprinsipper

1. **JPEG som Master**
   - Import scanner alltid JPEG-filer først
   - JPEG blir automatisk master når Photo opprettes
   - Master brukes for thumbnails, preview, og visning

2. **Ikke-invasiv Workflow**
   - Fotografer kan fortsette sin normale workflow
   - ImaLink tilpasser seg eksisterende filstrukturer
   - Ingen krav om spesielle navnekonvensjoner eller organisering

3. **Fleksibel Variant-støtte**
   - JPEG/RAW-par (mest vanlig)
   - Bearbeidede filer (PSD, TIFF, etc.)
   - Flere versjoner av samme bilde
   - Eksporterte variasjoner

## Eksempler på Use Cases

### Use Case 1: Profesjonell Fotograf
```
Photo: "Bryllup Oslo 2024 - Portrett"
├── Master: DSC_0123.JPG (2.5 MB)
└── Variants:
    ├── DSC_0123.NEF (25 MB RAW-original)
    ├── DSC_0123_retusjert.PSD (150 MB med lag)
    ├── DSC_0123_kunde.JPG (5 MB høy kvalitet for klient)
    └── DSC_0123_web.JPG (200 KB for sosiale medier)
```

### Use Case 2: Hobbyist
```
Photo: "Ferie Spania 2024"
├── Master: IMG_5678.JPG (3 MB)
└── Variants:
    └── IMG_5678.HEIC (original fra iPhone)
```

### Use Case 3: Advanced Workflow
```
Photo: "Landskapsfoto Lofoten"
├── Master: PANO_001.JPG (panorama output)
└── Variants:
    ├── DSC_1001.NEF (bracket -2)
    ├── DSC_1002.NEF (bracket 0)
    ├── DSC_1003.NEF (bracket +2)
    ├── PANO_001_32bit.TIFF (HDR merge)
    └── PANO_001_final.PSD (bearbeidet versjon)
```

## Teknisk Implementering

### Nåværende Status (✅ Fungerer)
- Import scanner JPEG-filer
- Ekstraherer EXIF fra JPEG (master)
- Oppretter Photo med JPEG som master
- Sender metadata til backend

### Mangler (❓ Må utvikles)
- [ ] Automatisk deteksjon av RAW-filer ved siden av JPEG
- [ ] Matching-logikk (filnavn, timestamp, etc.)
- [ ] API for å legge til varianter til eksisterende Photo
- [ ] UI for å vise varianter i galleriet
- [ ] UI for å administrere varianter (legge til/fjerne)
- [ ] Variant-type klassifisering (RAW, PSD, export, etc.)
- [ ] Metadata fra varianter (størrelse, format, opprettet dato)

## Spørsmål å Utforske

### 1. Matching-strategi
- **Filnavn-basert?** (DSC_0123.JPG + DSC_0123.NEF)
- **Timestamp-basert?** (samme EXIF DateTimeOriginal)
- **Manual kobling?** (bruker velger i UI)
- **Kombinasjon?** (automatisk forslag + manuell override)

### 2. Backend-støtte
- Er `ImageFile`-modellen klar for varianter?
- Trenger backend-endringer?
- Hvordan lagres relasjoner i database?

### 3. Import-workflow
- **Automatisk deteksjon under import?**
  - Scanner samtidig for JPEG og RAW
  - Kobler automatisk hvis match funnet
- **Separat variant-import?**
  - Importer JPEG først
  - Legg til varianter senere via UI
- **Batch-prosessering?**
  - Scan hele mapper for par
  - Vis forslag til kobling før import

### 4. UI/UX Design
- Hvordan visualisere at Photo har varianter?
  - Badge/indikator på thumbnail?
  - Spesiell farge/ikon?
- Hvordan vise liste av varianter?
  - Dropdown i info-panel?
  - Separat variants-dialog?
- Hvordan administrere varianter?
  - Dra-og-slipp for å legge til?
  - File browser dialog?

## Lignende Løsninger (Research Needed)

### Kommersielle Produkter
- [ ] **Adobe Lightroom** - Hvordan håndterer de RAW+JPEG?
- [ ] **Capture One** - Variant management?
- [ ] **Photo Mechanic** - Filkobling?
- [ ] **ACDSee** - Stack/group features?

### Open Source
- [ ] **digiKam** - Image grouping?
- [ ] **Darktable** - RAW+JPEG handling?
- [ ] **RawTherapee** - File associations?
- [ ] **Shotwell** - Image stacks?

### Spørsmål til Research
1. Hva er standard praksis for JPEG/RAW-par?
2. Hvordan håndterer andre flere versjoner av samme bilde?
3. Finnes det etablerte metadata-standarder for dette?
4. Hvilke features er mest brukt av fotografer?

## Design-beslutninger å Ta

### Prioritet 1 (Grunnleggende)
- [ ] Definere matching-strategi for JPEG/RAW-par
- [ ] Backend API design for varianter
- [ ] Enkel UI for å vise at varianter finnes

### Prioritet 2 (Utvidet)
- [ ] Automatisk deteksjon under import
- [ ] Manual variant-kobling via UI
- [ ] Metadata fra alle varianter

### Prioritet 3 (Avansert)
- [ ] Intelligent matching (timestamp, content analysis)
- [ ] Bulk variant-operasjoner
- [ ] Variant-type klassifisering og ikoner

## Notater

### 2024-10-20
- Grunnkonseptet dokumentert
- Nåværende status: JPEG-import fungerer
- Trenger research på eksisterende løsninger
- Må diskutere backend-arkitektur før implementering
- UI/UX design må tenkes grundig gjennom

### Neste Steg
1. Research lignende systemer (Adobe, digiKam, etc.)
2. Diskutere backend-design for varianter
3. Lage mockups for UI
4. Definere matching-strategi
5. Prototype enkel versjon (kun JPEG/RAW-par)

## Referanser
- [ImaLink Backend Repository](../../../imalink-backend/) (når backend er klar)
- Ekstern research dokumenteres her når gjennomført

---

**Status**: 💡 Konsept-fase - Trenger mer research og design
