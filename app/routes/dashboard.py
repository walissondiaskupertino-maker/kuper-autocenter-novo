from flask import Blueprint, render_template
from flask_login import login_required  # <-- Adicione este import
from app.models import Cliente, Veiculo, Mecanico, OrdemServico, Financeiro, Peca
from app.extensions import db
from sqlalchemy.sql import func
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required  # <-- Adicione este decorador aqui
def index():
    dados = {
        'total_clientes': Cliente.query.count(),
        'total_veiculos': Veiculo.query.count(),
        'total_mecanicos': Mecanico.query.filter_by(ativo=True).count(),
        'os_abertas': OrdemServico.query.filter_by(status='Aberto').count(),
        'os_andamento': OrdemServico.query.filter_by(status='Em Andamento').count(),
        'os_aguardando': OrdemServico.query.filter_by(status='Aguardando Peças').count(),
        'os_concluidas': OrdemServico.query.filter_by(status='Concluído').count(),
        'entradas': float(db.session.query(func.coalesce(func.sum(Financeiro.valor), 0)).filter_by(tipo='Entrada').scalar() or 0),
        'saidas': float(db.session.query(func.coalesce(func.sum(Financeiro.valor), 0)).filter_by(tipo='Saida').scalar() or 0)
    }
    dados['saldo'] = dados['entradas'] - dados['saidas']
    
    # 🔔 Alertas de estoque baixo
    dados['pecas_estoque_baixo'] = Peca.query.filter(
        Peca.estoque_atual <= Peca.estoque_minimo
    ).all()
    
    # 📊 Faturamento mensal (últimos 6 meses)
    dados['faturamento_mensal'] = _faturamento_mensal()
    
    return render_template('dashboard.html', dados=dados, now=datetime.now)


def _faturamento_mensal():
    """Retorna lista com faturamento dos últimos 6 meses"""
    from sqlalchemy import extract
    meses = []
    from datetime import date
    hoje = date.today()
    
    for i in range(5, -1, -1):
        mes = hoje.month - i
        ano = hoje.year
        if mes <= 0:
            mes += 12
            ano -= 1
        
        entradas = db.session.query(func.coalesce(func.sum(Financeiro.valor), 0)).filter(
            func.extract('month', Financeiro.data_movimentacao) == mes,
            func.extract('year', Financeiro.data_movimentacao) == ano,
            Financeiro.tipo == 'Entrada'
        ).scalar()
        
        saidas = db.session.query(func.coalesce(func.sum(Financeiro.valor), 0)).filter(
            func.extract('month', Financeiro.data_movimentacao) == mes,
            func.extract('year', Financeiro.data_movimentacao) == ano,
            Financeiro.tipo == 'Saida'
        ).scalar()
        
        meses.append({
            'mes': f'{mes:02d}/{ano}',
            'entradas': float(entradas or 0),
            'saidas': float(saidas or 0)
        })
    
    return meses