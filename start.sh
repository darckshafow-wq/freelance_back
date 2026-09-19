#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".venv/bin/activate" ]]; then
    echo "Erreur: environnement virtuel absent: $ROOT_DIR/.venv" >&2
    exit 1
fi

source .venv/bin/activate

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
API_URL="http://${HOST}:${PORT}"

setup_postgres() {
    echo "🔧 Configuration de PostgreSQL..."
    if [[ -f "./setup_postgres.sh" ]]; then
        ./setup_postgres.sh
        echo "✅ PostgreSQL configuré avec succès"
    else
        echo "❌ Erreur: setup_postgres.sh non trouvé" >&2
        return 1
    fi
}

run_migrations() {
    echo "🔄 Exécution des migrations Alembic..."
    alembic upgrade head
    if [[ $? -eq 0 ]]; then
        echo "✅ Migrations appliquées avec succès"
    else
        echo "❌ Erreur lors de l'application des migrations" >&2
        return 1
    fi
}

seed_database() {
    echo "🌱 Chargement des données de test..."
    if [[ -f "./seed_data.py" ]]; then
        python seed_data.py
        if [[ $? -eq 0 ]]; then
            echo "✅ Données de test chargées avec succès"
        else
            echo "❌ Erreur lors du chargement des données" >&2
            return 1
        fi
    else
        echo "⚠️  Fichier seed_data.py non trouvé"
    fi
}

start_api() {
    echo "Demarrage de l'API sur ${API_URL}..."
    python -m uvicorn app.main:app --host "$HOST" --port "$PORT" &
    API_PID=$!

    cleanup() {
        if kill -0 "$API_PID" 2>/dev/null; then
            kill "$API_PID" 2>/dev/null || true
            wait "$API_PID" 2>/dev/null || true
        fi
    }
    trap cleanup EXIT INT TERM

    for _ in {1..30}; do
        if curl --silent --fail "${API_URL}/health" >/dev/null 2>&1; then
            echo "API disponible: ${API_URL}"
            return 0
        fi
        if ! kill -0 "$API_PID" 2>/dev/null; then
            echo "Erreur: l'API n'a pas pu demarrer." >&2
            wait "$API_PID" || true
            exit 1
        fi
        sleep 1
    done

    echo "Erreur: l'API n'est pas disponible apres 30 secondes." >&2
    exit 1
}

run_tests() {
    echo "Verification de la base de donnees..."
    python verify_data.py

    echo "Execution des tests API..."
    python test_api.py
}

case "${1:-all}" in
    postgres)
        setup_postgres
        ;;
    migrate)
        run_migrations
        ;;
    seed)
        seed_database
        ;;
    setup)
        echo "📋 Configuration complète du projet (PostgreSQL + Migrations + Seed)"
        setup_postgres && run_migrations && seed_database
        echo "✨ Configuration terminée!"
        ;;
    api)
        exec python -m uvicorn app.main:app --host "$HOST" --port "$PORT"
        ;;
    test)
        run_tests
        ;;
    all)
        start_api
        run_tests
        echo "Tests termines. L'API reste active sur ${API_URL}"
        wait "$API_PID"
        ;;
    *)
        echo "Usage: $0 [command]"
        echo ""
        echo "🗄️  Database Commands:"
        echo "  postgres  Configure PostgreSQL (user: admin, password: mohamed)"
        echo "  migrate   Execute les migrations Alembic"
        echo "  seed      Charge les données de test"
        echo "  setup     Configure PostgreSQL + Migrations + Seed (complet)"
        echo ""
        echo "🚀 API Commands:"
        echo "  api       Démarre uniquement l'API"
        echo "  test      Exécute les tests sur une API démarrée"
        echo "  all       Démarre API, exécute tests, garde API active (défaut)"
        echo ""
        echo "📚 Exemples:"
        echo "  $0 setup      # Configuration complète"
        echo "  $0 api        # Démarrer l'API"
        echo "  $0 migrate    # Appliquer migrations"
        echo "  $0 test       # Exécuter tests"
        exit 2
        ;;
esac
