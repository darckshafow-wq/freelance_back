# Tests d'intégration

Ce dossier contient les scripts de données de test et les vérifications d'intégration du backend.

## Contenu
- `seed_data.py` : génération des données de test
- `integration/test_api.py` : vérification des endpoints via l'API

## Utilisation

```bash
cd /home/shadow-66/freelance_back
source .venv/bin/activate
python tests/seed_data.py
python tests/integration/test_api.py
```
