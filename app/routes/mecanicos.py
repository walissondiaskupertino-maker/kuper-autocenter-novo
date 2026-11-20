from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db
from app.models import Mecanico
from app.forms import MecanicoForm
from sqlalchemy import or_

mecanicos_bp = Blueprint('mecanicos', __name__)

@mecanicos_bp.route('/')
def lista():
    busca = request.args.get('busca', '').strip()[:100]
    status = request.args.get('status', '')
    query = Mecanico.query
    if busca:
        termo = f'%{busca}%'
        query = query.filter(or_(
            Mecanico.nome.ilike(termo),
            Mecanico.cpf.ilike(termo),
            Mecanico.telefone.ilike(termo),
            Mecanico.especialidade.ilike(termo),
        ))
    if status == 'ativo':
        query = query.filter(Mecanico.ativo.is_(True))
    elif status == 'inativo':
        query = query.filter(Mecanico.ativo.is_(False))
    mecanicos = query.order_by(Mecanico.nome).all()
    return render_template(
        'mecanicos/lista.html',
        mecanicos=mecanicos,
        busca=busca,
        status=status,
    )

@mecanicos_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    form = MecanicoForm()
    if form.validate_on_submit():
        mecanico = Mecanico(
            nome=form.nome.data,
            cpf=form.cpf.data,
            telefone=form.telefone.data,
            especialidade=form.especialidade.data,
            ativo=form.ativo.data
        )
        db.session.add(mecanico)
        db.session.commit()
        flash('Mecânico cadastrado com sucesso!', 'success')
        return redirect(url_for('mecanicos.lista'))
    return render_template('mecanicos/form.html', form=form, titulo='Novo Mecânico')

@mecanicos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    mecanico = Mecanico.query.get_or_404(id)
    form = MecanicoForm(obj=mecanico)
    if form.validate_on_submit():
        mecanico.nome = form.nome.data
        mecanico.cpf = form.cpf.data
        mecanico.telefone = form.telefone.data
        mecanico.especialidade = form.especialidade.data
        mecanico.ativo = form.ativo.data
        db.session.commit()
        flash('Mecânico atualizado com sucesso!', 'success')
        return redirect(url_for('mecanicos.lista'))
    return render_template('mecanicos/form.html', form=form, titulo='Editar Mecânico')

@mecanicos_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    mecanico = Mecanico.query.get_or_404(id)
    db.session.delete(mecanico)
    db.session.commit()
    flash('Mecânico excluído com sucesso!', 'success')
    return redirect(url_for('mecanicos.lista'))