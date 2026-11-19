from flask import Blueprint, render_template, redirect, url_for, flash
from app.extensions import db
from app.models import Peca
from app.forms import PecaForm

pecas_bp = Blueprint('pecas', __name__)

@pecas_bp.route('/')
def lista():
    pecas = Peca.query.order_by(Peca.descricao).all()
    return render_template('pecas/lista.html', pecas=pecas)

@pecas_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    form = PecaForm()
    if form.validate_on_submit():
        peca = Peca(
            codigo=form.codigo.data, descricao=form.descricao.data,
            preco_custo=form.preco_custo.data or 0, preco_venda=form.preco_venda.data,
            estoque_atual=form.estoque_atual.data or 0, estoque_minimo=form.estoque_minimo.data or 0
        )
        db.session.add(peca)
        db.session.commit()
        flash('Peça cadastrada com sucesso!', 'success')
        return redirect(url_for('pecas.lista'))
    return render_template('pecas/form.html', form=form, titulo='Nova Peça')

@pecas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    peca = Peca.query.get_or_404(id)
    form = PecaForm(obj=peca)
    if form.validate_on_submit():
        peca.codigo = form.codigo.data
        peca.descricao = form.descricao.data
        peca.preco_custo = form.preco_custo.data or 0
        peca.preco_venda = form.preco_venda.data
        peca.estoque_atual = form.estoque_atual.data or 0
        peca.estoque_minimo = form.estoque_minimo.data or 0
        db.session.commit()
        flash('Peça atualizada com sucesso!', 'success')
        return redirect(url_for('pecas.lista'))
    return render_template('pecas/form.html', form=form, titulo='Editar Peça')

@pecas_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    peca = Peca.query.get_or_404(id)
    db.session.delete(peca)
    db.session.commit()
    flash('Peça excluída com sucesso!', 'success')
    return redirect(url_for('pecas.lista'))
