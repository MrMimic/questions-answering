# questions-answering

## Run on GCP

### Login gcloud

```bash
    gcloud auth login
    gcloud config set project data-baguette
```

### Build Docker

```bash
    gcloud builds submit --tag gcr.io/data-baguette/question-answering
```

### Run Docker

```bash
    gcloud run deploy --image gcr.io/data-baguette/question-answering --platform managed --max-instances=1
```

## Local run

### With Python

```bash
    git clone https://github.com/MrMimic/questions-answering
    cd questions-answering
    python -m venv .venv
    source .venv/bin/activate  # or source .venv/Scripts/activate on Windows
    pip install -r requirements.txt
    python main.py
```

### With Docker

```bash
    git clone https://github.com/MrMimic/questions-answering
    cd questions-answering
    docker build -t questions-answering .
    docker run -e PORT=8080 -p 8080:8080 questions-answering:latest
```

Then, navigate to `http://localhost:8080/`.
