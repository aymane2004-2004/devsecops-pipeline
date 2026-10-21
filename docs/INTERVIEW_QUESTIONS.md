# Questions d'entretien – Projet Secure CI/CD Pipeline (DevSecOps)

Réponses courtes modèles en italique après chaque question. Adapte-les avec tes propres mots et ton vécu.

---

## 1. Présentation du projet

**Q1. Présentez ce projet en 1 minute.**
*J'ai construit un pipeline CI/CD sous GitHub Actions pour une API Flask conteneurisée. Chaque push déclenche : détection de secrets (Gitleaks), SAST (Semgrep), SCA (pip-audit), tests (pytest), puis build Docker, scan Trivy avec quality gate sur les CVE HIGH/CRITICAL, et DAST avec OWASP ZAP sur le conteneur lancé. Si un contrôle échoue, rien n'avance. L'objectif est le shift-left : trouver les problèmes tôt, automatiquement.*

**Q2. Pourquoi ce projet ? Quel problème résout-il ?**
**Q3. Quelle a été la plus grande difficulté ?** *(ex : faux positifs, ordre des jobs, réseau ZAP vers conteneur, CVE de dépendances trouvée par pip-audit pendant le développement)*
**Q4. Qu'avez-vous appris ? Que referiez-vous différemment ?**

## 2. Concepts DevSecOps

**Q5. Qu'est-ce que DevSecOps ? Différence avec DevOps ?**
*DevOps automatise build/livraison ; DevSecOps intègre la sécurité comme étape automatisée et responsabilité partagée dans tout le cycle.*

**Q6. Qu'est-ce que le shift-left ?** *Déplacer les contrôles de sécurité au plus tôt (code, commit) car un défaut coûte moins cher à corriger tôt.*

**Q7. Différence SAST / DAST / SCA / IAST ?**
*SAST : analyse du code source sans l'exécuter. DAST : tests de l'application en fonctionnement (boîte noire). SCA : vulnérabilités des dépendances tierces. IAST : instrumentation à l'exécution combinant les deux.*

**Q8. Qu'est-ce qu'un quality gate ?** *Un seuil qui bloque le pipeline (ex : aucune CVE HIGH/CRITICAL corrigeable).*

**Q9. Qu'est-ce que la supply chain security ?** Citer : dépendances épinglées, SCA, SBOM, signature d'images, actions épinglées par SHA, image de base de confiance.

## 3. GitHub Actions / CI-CD

**Q10. Expliquez la structure de votre workflow.** *Jobs parallèles pour les contrôles rapides, puis un job `needs:` qui build/scanne/DAST.*

**Q11. Pourquoi `permissions: contents: read` ?** *Principe du moindre privilège sur le `GITHUB_TOKEN` ; chaque job n'élève que si nécessaire (`security-events: write`).*

**Q12. Différence entre `needs`, `if`, `continue-on-error` ?**
**Q13. Comment gérez-vous les secrets dans GitHub Actions ?** *`secrets.*`, jamais en clair, masqués dans les logs, environnements protégés.*

**Q14. Quels risques liés à l'utilisation d'actions tierces ?** *Compromission d'une action (ex : incident tj-actions). Mitigation : épingler par SHA, actions de confiance, Dependabot.*

**Q15. Comment éviter qu'un développeur contourne le pipeline ?** *Branch protection, required status checks, revue obligatoire, interdiction de push direct sur main.*

**Q16. `pull_request` vs `pull_request_target` : risque ?** *`pull_request_target` s'exécute avec secrets sur du code potentiellement non fiable ; à éviter ou à manipuler avec grande prudence.*

## 4. Outils de sécurité

**Q17. Comment fonctionne Gitleaks ? Que faire si un secret est déjà commité ?**
*Regex + entropie sur le code et l'historique git. Réponse : révoquer/rotater immédiatement le secret (le supprimer du dépôt ne suffit pas), puis nettoyer l'historique si nécessaire.*

**Q18. Comment fonctionne Semgrep ? Qu'est-ce qu'une règle ? Comment gérer un faux positif ?**
*Analyse par motifs syntaxiques/sémantiques ; règles YAML ; `# nosemgrep: <rule-id>` avec justification, ou ajustement de la règle.*

**Q19. Comment pip-audit trouve-t-il des vulnérabilités ?** *Compare les versions installées aux bases de vulnérabilités (PyPI Advisory / OSV).* **Que faire quand aucun correctif n'existe ?** *Évaluer l'exploitabilité, mitigation, remplacement, exception documentée et datée.*

**Q20. Que scanne Trivy ? Que signifie `--ignore-unfixed` ?** *OS packages, dépendances, secrets, misconfig. `--ignore-unfixed` ignore les CVE sans correctif disponible ; compromis à justifier.*

**Q21. Comment fonctionne OWASP ZAP baseline ? Différence avec full scan ?** *Baseline : spider + règles passives, rapide, sans attaque active. Full : attaques actives, plus long, à faire sur un environnement dédié.*

**Q22. Qu'est-ce que CVSS ? Comment priorisez-vous ?** *Score 0–10 (gravité). Prioriser selon exploitabilité (EPSS, KEV), exposition, criticité de l'actif, pas seulement le score.*

**Q23. Un faux positif/faux négatif : lequel est le plus dangereux ?** *Le faux négatif (risque non vu) ; mais trop de faux positifs fatigue les équipes et font ignorer les alertes.*

## 5. Docker et conteneurs

**Q24. Pourquoi un utilisateur non-root ?** *Limite l'impact d'une compromission (évasion, écriture système).*

**Q25. Pourquoi un build multi-stage ?** *Image finale plus petite, sans outils de build, moins de surface d'attaque.*

**Q26. Pourquoi une image slim/minimale ? Et distroless/alpine ?** *Moins de paquets = moins de CVE. Distroless sans shell ; alpine (musl) peut poser des soucis de compatibilité.*

**Q27. À quoi sert `.dockerignore` ?** *Éviter d'embarquer `.git`, `.env`, tests dans l'image (fuite de secrets, taille).*

**Q28. Quels durcissements runtime ajouteriez-vous ?** `--read-only`, `--cap-drop ALL`, `no-new-privileges`, limites CPU/mémoire, seccomp/AppArmor.

**Q29. Pourquoi gunicorn plutôt que `flask run` ?** *Le serveur de développement Flask n'est pas conçu pour la production (performance, sécurité, debugger).*

**Q30. Pourquoi épingler les versions des dépendances et de l'image ? Quel inconvénient ?** *Reproductibilité et maîtrise de la supply chain ; inconvénient : il faut mettre à jour régulièrement (Dependabot).*

**Q31. Où mettre les secrets d'un conteneur ?** *Jamais dans l'image ni le Dockerfile : variables injectées à l'exécution, Docker/K8s secrets, Vault.*

## 6. Sécurité applicative (OWASP)

**Q32. Citez l'OWASP Top 10 et comment le projet adresse certains points.**
*Injection / validation d'entrée (regex stricte, rejet 400), mauvaise configuration (en-têtes, pas de debug, pas de stack trace), composants vulnérables (SCA), logging (access log gunicorn).*

**Q33. Expliquez chaque en-tête de sécurité que vous avez mis en place.**
*`X-Content-Type-Options: nosniff` (anti MIME sniffing), `X-Frame-Options: DENY` et CSP `frame-ancestors` (clickjacking), CSP (XSS), `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` (pas de mise en cache de données sensibles). HSTS se configure côté reverse proxy TLS.*

**Q34. Comment se protéger de l'injection SQL, du XSS, du SSRF ?**
**Q35. Pourquoi limiter la taille des requêtes (`MAX_CONTENT_LENGTH`) ?** *Déni de service par gros payloads.*

**Q36. Ce qui manque à cette API pour la production ?** *Authentification/autorisation (JWT/OAuth2), rate limiting, TLS, base de données, logs structurés, monitoring.*

## 7. Mise en situation

**Q37. Le pipeline est bloqué par une CVE HIGH sans correctif. Que faites-vous ?**
*Analyser l'exploitabilité réelle, chercher une mitigation ou une autre image, ouvrir une exception temporaire documentée (ID, justification, date d'expiration, validée par la sécurité), suivre la correction.*

**Q38. Les développeurs se plaignent que le pipeline est trop lent ou génère trop de faux positifs.**
*Paralléliser, cache, scans incrémentaux sur PR, full scan en nightly, affiner les règles, mesurer les temps.*

**Q39. Gitleaks détecte une clé AWS dans l'historique. Procédure ?**
*Révoquer la clé, auditer son utilisation (CloudTrail), créer une nouvelle clé stockée dans un secret manager, purger l'historique (git filter-repo) si besoin, ajouter un pre-commit hook.*

**Q40. Comment mesurer l'efficacité de la démarche DevSecOps ?** *MTTR des vulnérabilités, nombre de vulnérabilités bloquées avant la prod, taux de faux positifs, couverture des scans, temps du pipeline.*

**Q41. Comment étendriez-vous ce pipeline vers un déploiement Kubernetes ?** *Push sur registry, signature Cosign, scan IaC (Checkov/kube-linter), admission controller (Kyverno/OPA), GitOps (ArgoCD), policies réseau.*

## 8. Questions comportementales

**Q42. Pourquoi le DevSecOps plutôt que le pentest pur ?** *(ton CV combine les deux : explique la complémentarité, le pentest valide, DevSecOps prévient et automatise)*
**Q43. Un développeur refuse de corriger une vulnérabilité. Comment réagissez-vous ?**
**Q44. Comment vous tenez-vous informé ?** *(TryHackMe, veille CVE, blogs OWASP, labs)*
**Q45. Où vous voyez-vous dans 5 ans ?**

## 9. Questions pièges (sois honnête)

- « Avez-vous utilisé ce pipeline en production ? » → Non, c'est un projet personnel/lab ; explique ce que tu ferais en vrai (voir section 8 du guide).
- « Pourquoi Semgrep et pas SonarQube / CodeQL ? » → open source, rapide, règles OWASP prêtes ; CodeQL plus profond mais plus lourd ; SonarQube centré qualité + serveur à héberger.
- « Pourquoi `--ignore-unfixed` ? » → réduire le bruit ; en contrepartie, un suivi séparé des CVE sans correctif.
- « Pourquoi ZAP baseline et non full scan ? » → rapidité et sécurité en CI ; full scan planifié sur un environnement de test.
- « Votre quality gate peut-il casser si une nouvelle CVE sort demain ? » → oui, c'est voulu ; d'où des builds planifiés pour détecter tôt et des mises à jour automatisées.

## 10. Checklist avant l'entretien

- [ ] Le dépôt GitHub est public, avec README clair et badge du pipeline
- [ ] Tu as des captures de pipeline vert + de pipelines rouges (démos section 6 du guide)
- [ ] Tu sais expliquer chaque ligne du Dockerfile et du workflow
- [ ] Tu peux lancer le projet en local en moins de 2 minutes
- [ ] Tu connais les limites du projet et ses pistes d'amélioration
