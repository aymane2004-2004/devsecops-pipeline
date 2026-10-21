# Secure CI/CD Pipeline – DevSecOps

![DevSecOps Pipeline](https://github.com/aymane2004-2004/devsecops-pipeline/actions/workflows/devsecops.yml/badge.svg)

Pipeline CI/CD sécurisé pour une API Flask conteneurisée (GitHub Actions, Docker, Trivy, Semgrep, Gitleaks, pip-audit, OWASP ZAP).

## Pipeline

```
push / PR ──► Gitleaks (secrets) ─┐
              Semgrep (SAST)      ├──► Build Docker ──► Trivy (quality gate HIGH/CRITICAL) ──► OWASP ZAP (DAST)
              pip-audit (SCA)     │
              pytest              ─┘
```

## Sécurité intégrée

- Détection de secrets, SAST OWASP Top 10, SCA, scan d'image, DAST
- Image Docker multi-stage, non-root (UID 10001), minimale, avec healthcheck
- Dépendances épinglées, en-têtes HTTP de sécurité, validation stricte des entrées
- Principe du moindre privilège sur le `GITHUB_TOKEN`

## Démarrage rapide

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
docker build -t devsecops-api . && docker run -p 5000:5000 devsecops-api
```

Guide complet : [docs/GUIDE.md](docs/GUIDE.md) · Questions d'entretien : [docs/INTERVIEW_QUESTIONS.md](docs/INTERVIEW_QUESTIONS.md)
