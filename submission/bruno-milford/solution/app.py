from __future__ import annotations

from flask import Flask, jsonify

from config import DEBUG
from routes.api_routes import api_bp
from routes.page_routes import page_bp
from services.database_service import DatabaseValidationError, validate_database


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    app.register_blueprint(page_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Recurso nao encontrado."}), 404

    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify({"success": False, "error": str(error)}), 400

    @app.errorhandler(Exception)
    def server_error(error):
        app.logger.exception("Erro inesperado")
        return jsonify({"success": False, "error": "Erro interno ao processar a requisicao."}), 500

    return app


app = create_app()


if __name__ == "__main__":
    try:
        validate_database()
    except DatabaseValidationError as error:
        print("RavenStack Churn Intelligence nao pode iniciar:")
        print(error)
        raise SystemExit(1)

    print("Banco validado com sucesso: database/ravenstack.db")
    print("Aplicacao disponivel em http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=DEBUG)
