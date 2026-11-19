from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user
from app.extensions import db
from app.models import OrdemServico, Veiculo, Mecanico, Servico, Peca, OsServico, OsPeca, MovimentacaoEstoque, Financeiro
from app.forms import DiagnosticoForm, OrdemServicoForm
from sqlalchemy.sql import func

os_bp = Blueprint('ordens_servico', __name__)

@os_bp.route('/')
def lista():
    query = OrdemServico.query
    if current_user.perfil == 'Mecanico':
        query = query.filter_by(mecanico_id=current_user.mecanico_id)
    ordens = query.order_by(OrdemServico.data_abertura.desc()).all()
    return render_template('ordens_servico/lista.html', ordens=ordens)

@os_bp.route('/nova', methods=['GET', 'POST'])
def nova():
    form = OrdemServicoForm()
    form.veiculo_id.choices = [(v.id, f"{v.placa} - {v.marca} {v.modelo}") for v in Veiculo.query.all()]
    form.mecanico_id.choices = [(m.id, m.nome) for m in Mecanico.query.filter_by(ativo=True).all()]
    form.mecanico_id.choices.insert(0, (0, '-- Sem mecânico --'))

    if form.validate_on_submit():
        if form.status.data == 'Concluído':
            form.status.errors.append('Conclua a OS após criá-la, usando a ação própria.')
            return render_template('ordens_servico/form.html', form=form, titulo='Nova OS')
        if current_user.perfil == 'Recepcionista' and form.status.data == 'Cancelado':
            form.status.errors.append('Somente o administrador pode cancelar uma OS.')
            return render_template('ordens_servico/form.html', form=form, titulo='Nova OS')

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
    servicos = Servico.query.filter_by(ativo=True).all() if current_user.perfil != 'Mecanico' else []
    pecas = Peca.query.all() if current_user.perfil == 'Admin' else []
    return render_template(
        'ordens_servico/detalhes.html',
        os_obj=os_obj,
        servicos=servicos,
        pecas=pecas,
        diagnostico_form=DiagnosticoForm()
    )

@os_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    os_obj = OrdemServico.query.get_or_404(id)
    form = OrdemServicoForm(obj=os_obj)
    form.veiculo_id.choices = [(v.id, f"{v.placa} - {v.marca} {v.modelo}") for v in Veiculo.query.all()]
    form.mecanico_id.choices = [(m.id, m.nome) for m in Mecanico.query.filter_by(ativo=True).all()]
    form.mecanico_id.choices.insert(0, (0, '-- Sem mecânico --'))

    if form.validate_on_submit():
        if os_obj.status in {'Concluído', 'Cancelado'} and form.status.data != os_obj.status:
            form.status.errors.append('Não é possível reabrir ou alterar o status de uma OS encerrada.')
            return render_template(
                'ordens_servico/form.html',
                form=form,
                titulo=f'Editar OS #{os_obj.id}'
            )
        if current_user.perfil == 'Recepcionista' and form.status.data in {'Concluído', 'Cancelado'}:
            form.status.errors.append('Somente o administrador pode concluir ou cancelar uma OS.')
            return render_template(
                'ordens_servico/form.html',
                form=form,
                titulo=f'Editar OS #{os_obj.id}'
            )
        if form.status.data == 'Concluído' and os_obj.status != 'Concluído':
            form.status.errors.append('Use a ação Concluir OS para registrar o lançamento financeiro.')
            return render_template(
                'ordens_servico/form.html',
                form=form,
                titulo=f'Editar OS #{os_obj.id}'
            )

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


@os_bp.route('/<int:id>/diagnostico', methods=['POST'])
def atualizar_diagnostico(id):
    if current_user.perfil != 'Mecanico':
        abort(403)

    os_obj = OrdemServico.query.filter_by(
        id=id,
        mecanico_id=current_user.mecanico_id
    ).first_or_404()
    if os_obj.status in {'Concluído', 'Cancelado'}:
        flash('Não é possível alterar o diagnóstico de uma OS encerrada.', 'danger')
        return redirect(url_for('ordens_servico.detalhes', id=id))

    form = DiagnosticoForm()
    if not form.validate_on_submit():
        flash('Diagnóstico inválido. Use no máximo 5.000 caracteres.', 'danger')
        return redirect(url_for('ordens_servico.detalhes', id=id))

    os_obj.diagnostico = form.diagnostico.data
    db.session.commit()
    flash('Diagnóstico atualizado com sucesso.', 'success')
    return redirect(url_for('ordens_servico.detalhes', id=id))


def _positive_quantity():
    try:
        quantity = int(request.form.get('quantidade', '1'))
    except (TypeError, ValueError):
        return None
    return quantity if quantity > 0 else None


def _ensure_os_editable(os_obj):
    if os_obj.status in {'Concluído', 'Cancelado'}:
        flash('Não é possível alterar os itens de uma OS encerrada.', 'danger')
        return False
    return True


@os_bp.route('/<int:id>/adicionar-servico', methods=['POST'])
def adicionar_servico(id):
    os_obj = OrdemServico.query.get_or_404(id)
    if not _ensure_os_editable(os_obj):
        return redirect(url_for('ordens_servico.detalhes', id=id))

    servico_id = request.form.get('servico_id')
    quantidade = _positive_quantity()
    if quantidade is None:
        flash('Informe uma quantidade inteira maior que zero.', 'danger')
        return redirect(url_for('ordens_servico.detalhes', id=id))

    servico = db.session.get(Servico, servico_id)
    if servico is None or not servico.ativo:
        flash('Serviço não encontrado ou inativo.', 'danger')
        return redirect(url_for('ordens_servico.detalhes', id=id))

    item = OsServico(
        os_id=os_obj.id,
        servico_id=servico.id,
        quantidade=quantidade,
        preco_unitario=servico.preco_base
    )
    db.session.add(item)
    db.session.flush()
    _recalcular_total(os_obj)
    db.session.commit()
    flash('Serviço adicionado!', 'success')

    return redirect(url_for('ordens_servico.detalhes', id=id))

@os_bp.route('/<int:id>/adicionar-peca', methods=['POST'])
def adicionar_peca(id):
    os_obj = OrdemServico.query.get_or_404(id)
    if not _ensure_os_editable(os_obj):
        return redirect(url_for('ordens_servico.detalhes', id=id))

    peca_id = request.form.get('peca_id')
    quantidade = _positive_quantity()
    if quantidade is None:
        flash('Informe uma quantidade inteira maior que zero.', 'danger')
        return redirect(url_for('ordens_servico.detalhes', id=id))

    peca = Peca.query.filter_by(id=peca_id).with_for_update().first()
    if peca is None:
        flash('Peça não encontrada.', 'danger')
        return redirect(url_for('ordens_servico.detalhes', id=id))
    if peca.estoque_atual < quantidade:
        flash(f'Estoque insuficiente! Disponível: {peca.estoque_atual}', 'danger')
        return redirect(url_for('ordens_servico.detalhes', id=id))

    item = OsPeca(
        os_id=os_obj.id,
        peca_id=peca.id,
        quantidade=quantidade,
        preco_unitario=peca.preco_venda
    )
    db.session.add(item)

    peca.estoque_atual -= quantidade
    mov = MovimentacaoEstoque(
        peca_id=peca.id,
        os_id=os_obj.id,
        tipo='Saida',
        quantidade=quantidade,
        descricao=f'Utilizada na OS #{os_obj.id}'
    )
    db.session.add(mov)
    db.session.flush()
    _recalcular_total(os_obj)
    db.session.commit()
    flash('Peça adicionada e estoque atualizado!', 'success')

    return redirect(url_for('ordens_servico.detalhes', id=id))

@os_bp.route('/<int:id_os>/remover-item/<tipo>/<int:id_item>', methods=['POST'])
def remover_item(id_os, tipo, id_item):
    os_obj = OrdemServico.query.get_or_404(id_os)
    if not _ensure_os_editable(os_obj):
        return redirect(url_for('ordens_servico.detalhes', id=id_os))

    if tipo == 'servico':
        item = OsServico.query.filter_by(id=id_item, os_id=id_os).first_or_404()
        db.session.delete(item)
    elif tipo == 'peca':
        item = OsPeca.query.filter_by(id=id_item, os_id=id_os).first_or_404()
        peca = Peca.query.filter_by(id=item.peca_id).with_for_update().first()
        if peca is None:
            abort(409, description='A peça vinculada à OS não existe mais.')
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
    else:
        abort(404)

    _recalcular_total(os_obj)
    db.session.commit()
    flash('Item removido!', 'success')
    return redirect(url_for('ordens_servico.detalhes', id=id_os))

@os_bp.route('/<int:id>/concluir', methods=['POST'])
def concluir(id):
    os_obj = OrdemServico.query.get_or_404(id)

    if os_obj.status == 'Cancelado':
        flash('Não é possível concluir uma OS cancelada.', 'danger')
        return redirect(url_for('ordens_servico.detalhes', id=id))
    
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
    
    os_obj.valor_total = (total_servicos or 0) + (total_pecas or 0)
