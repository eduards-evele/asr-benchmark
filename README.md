# ASR Benchmark

Grafiskā lietotne kas paredzēta audio ierakstu teksta atpazīšanas precizitātes novērtēšanai.


## Prasības

- Python 3.10+
- Tkinter (usually bundled with Python)
- A [Gemini API atslēga](https://aistudio.google.com/app/apikey)

## Instalācijas process

### Linux:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
### Windows: 
```bash
python -m venv .venv
.venv\Scripts\activate
```


Pārsauc failu **.env.example** uz **.env** un ielīmē Gemini API atslēgu

```bash
cp .env.example .env
# edit .env and set GEMINI_API_KEY=your_key_here
```

## Kā lietot

```bash
.venv/bin/python gui.py
```

1. Izvēlies manuālo transkripciju
2. Izvēlies automātiski izveidotas transkripcijas (<= 10)
3. Uzspiedi "Novērtēt"
