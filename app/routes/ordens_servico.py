from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db
from app.models import OrdemServico, Veiculo, Mecanico, Servico, Peca, OsServico, OsPeca, MovimentacaoEstoque, Financeiro
from app.forms import OrdemServicoForm
from sqlalchemy.sql import func

os_bp = Blueprint('ordens_servico', __name__)

@os_bp.route('/')
def lista():
    ordens = OrdemServico.query.order_by(OrdemServico.data_abertura.desc()).all()
    return render_template('ordens_servico/lista.html', ordens=ordens)

@os_bp.route('/nova', methods=['GET', 'POST'])
def nova():
    form = OrdemServicoForm()
    form.veiculo_id.choices = [(v.id, f"{v.placa} - {v.marca} {v.modelo}") for v in Veiculo.query.all()]
    form.mecanico_id.choices = [(m.id, m.nome) for m in Mecanico.query.filter_by(ativo=True).all()]
    form.mecanico_id.choices.insert(0, (0, '-- Sem mecânico --'))

    if form.validate_on_submit():
        os_obj = OrdemServico(
            veiculo_id=form.veiculo_id.data,
            mecanico_id=form.mecanico_id.data if form.mecanico_id.data != 0 else None,
            status=form.status.data,
            defeito_relatado=form.defeito_relatado.data,
            diagnostico=form.diagnostico.data
        )
        db.session.add(os_obj)
        db.session.commit()
        flash('Ordem de Serviço criada com sucesso!', 'success')
        return redirect(url_for('ordens_servico.detalhes', id=os_obj.id))

    return render_template('ordens_servico/form.html', form=form, titulo='Nova OS')

@os_bp.route('/<int:id>')
def detalhes(id):
    os_obj = OrdemServico.query.get_or_404(id)
    servicos = Servico.query.filter_by(ativo=True).all()
    pecas = Peca.query.all()
    return render_template('ordens_servico/detalhes.html', os_obj=os_obj, servicos=servicos, pecas=pecas)

@os_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    os_obj = OrdemServico.query.get_or_404(id)
    form = OrdemServicoForm(obj=os_obj)
    form.veiculo_id.choices = [(v.id, f"{v.placa} - {v.marca} {v.modelo}") for v in Veiculo.query.all()]
    form.mecanico_id.choices = [(m.id, m.nome) for m in Mecanico.query.filter_by(ativo=True).all()]
    form.mecanico_id.choices.insert(0, (0, '-- Sem mecânico --'))

    if form.validate_on_submit():
        os_obj.veiculo_id = form.veiculo_id.data
        os_obj.mecanico_id = form.mecanico_id.data if form.mecanico_id.data != 0 else None
        os_obj.status = form.status.data
        os_obj.defeito_relatado = form.defeito_relatado.data
        os_obj.diagnostico = form.diagnostico.data

        if form.status.data == 'Concluído' and not os_obj.data_conclusao:
            os_obj.data_conclusao = datetime.utcnow()

        db.session.commit()
        flash('OS atualizada com sucesso!', 'success')
        return redirect(url_for('ordens_servico.detalhes', id=os_obj.id))

    return render_template('ordens_servico/form.html', form=form, titulo=f'Editar OS #{os_obj.id}')

@os_bp.route('/<int:id>/adicionar-servico', methods=['POST'])
def adicionar_servico(id):
    os_obj = OrdemServico.query.get_or_404(id)
    servico_id = request.form.get('servico_id')
    quantidade = int(request.form.get('quantidade', 1))

    servico = Servico.query.get(servico_id)
    if servico:
        subtotal = quantidade * float(servico.preco_base) # ✅ CORREÇÃO: Cálculo do subtotal
        item = OsServico(
            os_id=os_obj.id,
            servico_id=servico.id,
            quantidade=quantidade,
            preco_unitario=servico.preco_base,
            subtotal=subtotal
        )
        db.session.add(item)
        db.session.commit()
        _recalcular_total(os_obj)
        flash('Serviço adicionado!', 'success')

    return redirect(url_for('ordens_servico.detalhes', id=id))

@os_bp.route('/<int:id>/adicionar-peca', methods=['POST'])
def adicionar_peca(id):
    os_obj = OrdemServico.query.get_or_404(id)
    peca_id = request.form.get('peca_id')
    quantidade = int(request.form.get('quantidade', 1))

    peca = Peca.query.get(peca_id)
    if peca:
        if peca.estoque_atual < quantidade:
            flash(f'Estoque insuficiente! Disponível: {peca.estoque_atual}', 'danger')
            return redirect(url_for('ordens_servico.detalhes', id=id))

        subtotal = quantidade * float(peca.preco_venda) # ✅ CORREÇÃO: Cálculo do subtotal
        item = OsPeca(
            os_id=os_obj.id,
            peca_id=peca.id,
            quantidade=quantidade,
            preco_unitario=peca.preco_venda,
            subtotal=subtotal
        )
        db.session.add(item)

        # Baixar estoque
        peca.estoque_atual -= quantidade
        mov = MovimentacaoEstoque(
            peca_id=peca.id,
            os_id=os_obj.id,
            tipo='Saida',
            quantidade=quantidade,
            descricao=f'Utilizada na OS #{os_obj.id}'
        )
        db.session.add(mov)
        db.session.commit()
        _recalcular_total(os_obj)
        flash('Peça adicionada e estoque atualizado!', 'success')

    return redirect(url_for('ordens_servico.detalhes', id=id))

@os_bp.route('/<int:id_os>/remover-item/<tipo>/<int:id_item>', methods=['POST'])
def remover_item(id_os, tipo, id_item):
    if tipo == 'servico':
        item = OsServico.query.get_or_404(id_item)
        db.session.delete(item)
    else:
        item = OsPeca.query.get_or_404(id_item)
        # Devolver estoque
        peca = Peca.query.get(item.peca_id)
        if peca:
            peca.estoque_atual += item.quantidade
            mov = MovimentacaoEstoque(
                peca_id=peca.id,
                os_id=id_os,
                tipo='Entrada',
                quantidade=item.quantidade,
                descricao=f'Devolução da OS #{id_os}'
            )
            db.session.add(mov)
        db.session.delete(item)

    os_obj = OrdemServico.query.get(id_os)
    _recalcular_total(os_obj)
    db.session.commit()
    flash('Item removido!', 'success')
    return redirect(url_for('ordens_servico.detalhes', id=id_os))

@os_bp.route('/<int:id>/concluir', methods=['POST'])
def concluir(id):
    os_obj = OrdemServico.query.get_or_404(id)
    
    # Evita duplicidade de lançamento financeiro se já estiver concluído
    if os_obj.status != 'Concluído':
        os_obj.status = 'Concluído'
        os_obj.data_conclusao = datetime.utcnow()

        # Lançar no financeiro automaticamente
        if os_obj.valor_total and float(os_obj.valor_total) > 0:
            financeiro = Financeiro(
                os_id=os_obj.id,
                tipo='Entrada',
                descricao=f'Pagamento da OS #{os_obj.id}',
                valor=os_obj.valor_total,
                categoria='Serviços',
                forma_pagamento='A definir'
            )
            db.session.add(financeiro)

    db.session.commit()
    flash('OS concluída e lançamento financeiro criado!', 'success')
    return redirect(url_for('ordens_servico.detalhes', id=id))

def _recalcular_total(os_obj):
    total_servicos = db.session.query(func.coalesce(func.sum(OsServico.subtotal), 0)).filter_by(os_id=os_obj.id).scalar()
    total_pecas = db.session.query(func.coalesce(func.sum(OsPeca.subtotal), 0)).filter_by(os_id=os_obj.id).scalar()
    
    # Garante conversão segura para float
    total_servicos = float(total_servicos) if total_servicos else 0.0
    total_pecas = float(total_pecas) if total_pecas else 0.0
    
    os_obj.valor_total = total_servicos + total_pecas
    db.session.commit()
