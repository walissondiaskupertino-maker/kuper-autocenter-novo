from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from app.extensions import db
from app.models import Usuario
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.verificar_senha(senha):
            if not usuario.ativo:
                flash('Usuário desativado. Contate o administrador.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(usuario, remember=True)
            session['usuario_nome'] = usuario.nome
            session['usuario_perfil'] = usuario.perfil
            flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
            return redirect(url_for('dashboard.index'))
        
        flash('E-mail ou senha inválidos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        perfil = request.form.get('perfil', 'Recepcionista')
        
        # Verifica se o e-mail já existe
        if Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado no sistema.', 'danger')
            return redirect(url_for('auth.cadastro'))
        
        # Cria o novo usuário
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            perfil=perfil,
            ativo=True
        )
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça login para acessar.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/cadastro.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/criar-admin')
def criar_admin():
    """Rota de emergência para criar o primeiro administrador"""
    if Usuario.query.filter_by(perfil='Admin').count() == 0:
        admin = Usuario(
            nome='Administrador', 
            email='admin@kuper.com',
            senha=generate_password_hash('admin123'), 
            perfil='Admin'
        )
        db.session.add(admin)
        db.session.commit()
        return '✅ Admin criado! Email: admin@kuper.com | Senha: admin123<br><a href="/auth/login">Ir para Login</a>'
    return '⚠️ Admin já existe.'
