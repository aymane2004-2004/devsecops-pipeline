# Guide d'exécution et de test – Secure CI/CD Pipeline

## 0. Prérequis

| Outil | Version | Vérification |
|---|---|---|
| Python | 3.12+ | `python3 --version` |
| Docker | 24+ | `docker --version` |
| Git | 2.x | `git --version` |
| Compte GitHub | – | pour GitHub Actions |

## 1. Structure du projet

```
devsecops-pipeline/
├── app/main.py                  # API Flask (en-têtes de sécurité, validation)
├── tests/test_app.py            # tests pytest (16 tests)
├── requirements.txt             # dépendances épinglées
├── requirements-dev.txt         # pytest + pip-audit
├── Dockerfile                   # multi-stage, non-root, healthcheck
├── .dockerignore
├── .gitleaks.toml               # config détection de secrets
├── zap/rules.tsv                # règles ZAP (exceptions documentées)
├── .github/workflows/devsecops.yml
└── docs/                        # ce guide + questions d'entretien
```

## 2. Exécution locale (sans Docker)

```bash
cd devsecops-pipeline
python -m venv .venv
source .venv/bin/activate            # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v                            # attendu : 16 passed
python -m app.main                   # API sur http://127.0.0.1:5000
```

Test rapide (autre terminal) :

```bash
curl -i http://127.0.0.1:5000/health
curl -X POST http://127.0.0.1:5000/api/items -H "Content-Type: application/json" -d '{"name":"demo"}'
curl http://127.0.0.1:5000/api/items
# Entrée malveillante -> 400
curl -i -X POST http://127.0.0.1:5000/api/items -H "Content-Type: application/json" -d '{"name":"<script>alert(1)</script>"}'
```

Vérifie les en-têtes dans la réponse : `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`, `Cache-Control`.

## 3. Exécution avec Docker

```bash
docker build -t devsecops-api .
docker run -d --name api -p 5000:5000 devsecops-api
curl http://localhost:5000/health
docker ps                                   # STATUS doit passer à (healthy)
```

Vérifier le durcissement :

```bash
docker exec api id                          # uid=10001 (pas root)
docker exec api whoami                      # app ou "cannot find name" : ok
docker image ls devsecops-api               # taille de l'image
```

Option de durcissement runtime supplémentaire :

```bash
docker rm -f api
docker run -d --name api -p 5000:5000 \
  --read-only --tmpfs /tmp \
  --cap-drop ALL --security-opt no-new-privileges:true \
  devsecops-api
```

## 4. Lancer les scans de sécurité en local

### 4.1 Gitleaks (secrets)
```bash
docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:latest detect --source /repo -c /repo/.gitleaks.toml -v
```

### 4.2 Semgrep (SAST)
```bash
docker run --rm -v "$PWD:/src" semgrep/semgrep semgrep scan \
  --config p/owasp-top-ten --config p/python --config p/flask --error /src/app
```

### 4.3 pip-audit (SCA)
```bash
pip-audit -r requirements.txt --strict
```

### 4.4 Trivy (scan d'image + quality gate)
```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest \
  image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 devsecops-api
```
`--exit-code 1` = le quality gate : la commande échoue s'il reste une CVE HIGH/CRITICAL.

### 4.5 OWASP ZAP (DAST baseline)
Avec le conteneur de l'API lancé sur le port 5000 :
```bash
docker run --rm --network host -v "$PWD:/zap/wrk:rw" ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t http://localhost:5000 -r zap-report.html -c zap/rules.tsv
```
Sous macOS/Windows (pas de `--network host`) : remplace par `http://host.docker.internal:5000`.
Ouvre `zap-report.html` pour lire les résultats.

## 5. Déployer le pipeline sur GitHub

```bash
git init
git add .
git commit -m "feat: secure CI/CD pipeline"
git branch -M main
git remote add origin https://github.com/aymane2004-2004/devsecops-pipeline.git
git push -u origin main
```

Puis dans GitHub, onglet **Actions** : le workflow *DevSecOps Pipeline* démarre.
Ordre d'exécution : `secrets-scan`, `sast`, `sca`, `test` (en parallèle) puis `build-scan-dast`.

Recommandé : *Settings > Branches > Branch protection* sur `main` avec les jobs ci-dessus en « required status checks ». Les rapports (Trivy SARIF, ZAP) sont dans les artefacts du run ; le SARIF apparaît aussi dans **Security > Code scanning** si disponible sur votre dépôt.

## 6. Prouver que le pipeline protège vraiment (démos pour l'entretien)

Chaque démo se fait sur une branche + Pull Request : le pipeline doit passer au rouge.

| Démo | Action | Job attendu en échec |
|---|---|---|
| Secret | Ajouter dans un fichier : `AWS_KEY = "AKIAIOSFODNN7EXAMPLE"` (clé factice) | Gitleaks |
| SAST | Dans `app/main.py`, ajouter `import subprocess; subprocess.call(request.args["c"], shell=True)` | Semgrep |
| SCA | Dans `requirements.txt`, rétrograder `Werkzeug==3.0.6` | pip-audit |
| Image | Changer la base en `python:3.8-slim` (ancienne, vulnérable) | Trivy quality gate |
| DAST | Supprimer l'en-tête `X-Content-Type-Options` dans `add_security_headers` | ZAP baseline (et pytest) |
| Tests | Changer `"ok"` en `"ko"` dans `/health` | pytest |

Fais une capture d'écran de chaque échec, puis du pipeline revenu au vert après correction. C'est un excellent support pour l'entretien. Ne merge pas ces branches.

## 7. Dépannage

| Problème | Cause probable | Solution |
|---|---|---|
| pip-audit échoue après quelque temps | nouvelle CVE publiée sur une dépendance | mettre à jour la version épinglée, relancer |
| Trivy échoue sur l'image | CVE dans l'image de base | reconstruire (`--pull`), passer à une base plus récente |
| ZAP : connexion refusée | conteneur pas prêt ou mauvais réseau | vérifier `curl localhost:5000/health`, attendre la boucle d'attente |
| Gitleaks signale un faux positif | motif ressemblant à un secret | ajouter une règle dans `.gitleaks.toml` (allowlist) |
| `upload-sarif` échoue | Code scanning indisponible sur dépôt privé | l'étape est en `continue-on-error`, sans impact |
| Port 5000 occupé (macOS) | AirPlay Receiver | utiliser `-p 8080:5000` |

Les versions d'actions GitHub et d'outils évoluent : si une étape échoue pour cause de version, consulte la documentation de l'action concernée et mets à jour le tag.

## 8. Pistes d'amélioration (à mentionner en entretien)

- Signature d'images (Cosign) et SBOM (Syft / `trivy sbom`)
- Épingler les actions GitHub par SHA de commit
- Dependabot ou Renovate pour les mises à jour automatiques
- Publication de l'image sur GHCR et déploiement (Kubernetes / ArgoCD)
- DAST complet (`zap-full-scan`) ou avec spécification OpenAPI
- Scan IaC (Checkov) si ajout de Terraform
