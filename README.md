# Beat Detector API

Backend API dla Beat Detector - używa librosa do profesjonalnej detekcji beatów.

## Deployment na Render.com (DARMOWY)

### 1. Stwórz repozytorium na GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TWOJ_USERNAME/beat-detector-api.git
git push -u origin main
```

### 2. Załóż konto na Render.com

1. Idź na https://render.com
2. Zaloguj się przez GitHub
3. **To wszystko - za darmo!**

### 3. Stwórz Web Service

1. Kliknij **"New +"** → **"Web Service"**
2. Połącz swoje repozytorium GitHub
3. Ustawienia:
   - **Name**: `beat-detector-api` (lub cokolwiek)
   - **Region**: Frankfurt (najbliżej Polski)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free` ⭐
4. Kliknij **"Create Web Service"**

### 4. Poczekaj 5-10 minut

Render zainstaluje wszystko automatycznie. Zobaczysz:
```
==> Installing dependencies from requirements.txt
==> Build successful!
==> Starting service...
```

### 5. Gotowe! 🎉

Twoje API będzie dostępne na:
```
https://beat-detector-api-XXXXX.onrender.com
```

## Testowanie lokalnie

```bash
pip install -r requirements.txt
python app.py
```

API będzie na `http://localhost:5000`

## Użycie API

### Endpoint: `/detect-beats`

**POST** z plikiem audio:

```javascript
const formData = new FormData();
formData.append('audio', audioFile);
formData.append('sensitivity', '1.0');
formData.append('detect_extra', 'true');

const response = await fetch('https://your-api.onrender.com/detect-beats', {
    method: 'POST',
    body: formData
});

const data = await response.json();
console.log(data.bpm, data.beats);
```

## Limity darmowego planu

- ✅ 750 godzin/miesiąc (wystarczy!)
- ✅ Nieograniczone requesty
- ⚠️ Usypia po 15 min braku aktywności (pierwsze żądanie budzi - 30s opóźnienie)
- ⚠️ Max 512MB RAM (wystarczy dla librosa)

## Alternatywy

- **Railway.app** - 500h/miesiąc za darmo
- **PythonAnywhere** - darmowy tier
- **Fly.io** - 3 darmowe maszyny

## Troubleshooting

**Problem**: "Build failed"
**Rozwiązanie**: Sprawdź czy `requirements.txt` jest w głównym katalogu

**Problem**: "Out of memory"
**Rozwiązanie**: Zmniejsz pliki audio (max 3-5 min)
