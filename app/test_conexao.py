from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("🔗 URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    try:
        result = db.session.execute(db.text("SELECT 1")).scalar()
        print("✅ Conexão OK! Resultado:", result)
    except Exception as e:
        print("❌ ERRO:", e)