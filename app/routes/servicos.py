from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db
from app.models import Servico
from app.forms import ServicoForm
from sqlalchemy import or_

servicos_bp = Blueprint('servicos', __name__)

@servicos_bp.route('/')
def lista():
    busca = request.args.get('busca', '').strip()[:100]
    status = request.args.get('status', '')
    query = Servico.query
    if busca:
        termo = f'%{busca}%'
        query = query.filter(or_(
            Servico.nome.ilike(termo),
            Servico.descricao.ilike(termo),
        ))
    if status == 'ativo':
        query = query.filter(Servico.ativo.is_(True))
    elif status == 'inativo':
        query = query.filter(Servico.ativo.is_(False))
    servicos = query.order_by(Servico.nome).all()
    return render_template(
        'servicos/lista.html',
        servicos=servicos,
        busca=busca,
        status=status,
    )

@servicos_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    form = ServicoForm()
    if form.validate_on_submit():
        servico = Servico(
            nome=form.nome.data,
            descricao=form.descricao.data,
            preco_base=form.preco_base.data,
            ativo=form.ativo.data
        )
        db.session.add(servico)
        db.session.commit()
        flash('Serviço cadastrado com sucesso!', 'success')
        return redirect(url_for('servicos.lista'))
    return render_template('servicos/form.html', form=form, titulo='Novo Serviço')

@servicos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    servico = Servico.query.get_or_404(id)
    form = ServicoForm(obj=servico)
    if form.validate_on_submit():
        servico.nome = form.nome.data
        servico.descricao = form.descricao.data
        servico.preco_base = form.preco_base.data
        servico.ativo = form.ativo.data
        db.session.commit()
        flash('Serviço atualizado com sucesso!', 'success')
        return redirect(url_for('servicos.lista'))
    return render_template('servicos/form.html', form=form, titulo='Editar Serviço')

@servicos_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    servico = Servico.query.get_or_404(id)
    db.session.delete(servico)
    db.session.commit()
    flash('Serviço excluído com sucesso!', 'success')
    return redirect(url_for('servicos.lista'))
