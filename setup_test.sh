echo "Setting environment variables:"
export DB_NAME="trade_compliance_monitor_test"
echo "DB_NAME=${DB_NAME}"
export DATABASE_URL="postgresql://postgres@localhost:5432/${DB_NAME}"
echo "DATABASE_URL=${DATABASE_URL}"
export FLASK_APP="tcm_app"
echo "FLASK_APP=${FLASK_APP}"
export APP_SETTINGS="config.TestingConfig"
echo "APP_SETTINGS=${APP_SETTINGS}"
export APP_BASE_URL="http://127.0.0.1:5000"
echo "APP_BASE_URL=${APP_BASE_URL}"
echo ""
echo "NOTE !!!"
echo "Environment variable AUTH0_CLIENT_SECRET is NOT set by this script."