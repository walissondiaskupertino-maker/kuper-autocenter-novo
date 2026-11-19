from flask import Flask
from .config import Config
from .extensions import db, csrf, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Carregar usuário
    @login_manager.user_loader
    def load_user(user_id):
        from .models import Usuario
        return Usuario.query.get(int(user_id))

    # Blueprints
    from .routes.dashboard import dashboard_bp
    from .routes.clientes import clientes_bp
    from .routes.veiculos import veiculos_bp
    from .routes.mecanicos import mecanicos_bp
    from .routes.pecas import pecas_bp
    from .routes.servicos import servicos_bp
    from .routes.ordens_servico import os_bp
    from .routes.financeiro import financeiro_bp
    from .routes.relatorios import relatorios_bp
    from .routes.auth import auth_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    app.register_blueprint(veiculos_bp, url_prefix='/veiculos')
    app.register_blueprint(mecanicos_bp, url_prefix='/mecanicos')
    app.register_blueprint(pecas_bp, url_prefix='/pecas')
    app.register_blueprint(servicos_bp, url_prefix='/servicos')
    app.register_blueprint(os_bp, url_prefix='/ordens-servico')
    app.register_blueprint(financeiro_bp, url_prefix='/financeiro')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app