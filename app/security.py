from flask import abort, request
from flask_login import current_user
from app.extensions import login_manager


ROLE_ENDPOINTS = {
    'Recepcionista': {
        'auth.logout',
        'clientes.lista',
        'clientes.novo',
        'clientes.editar',
        'clientes.excluir',
        'veiculos.lista',
        'veiculos.novo',
        'veiculos.editar',
        'veiculos.excluir',
        'ordens_servico.lista',
        'ordens_servico.nova',
        'ordens_servico.detalhes',
        'ordens_servico.editar',
        'ordens_servico.adicionar_servico',
        'relatorios.os_pdf',
        'relatorios.os_pdf_detalhe',
    },
    'Mecanico': {
        'auth.logout',
        'ordens_servico.lista',
        'ordens_servico.detalhes',
        'ordens_servico.atualizar_diagnostico',
    },
}


def protect_application_route():
    public_endpoints = {'auth.login', 'auth.cadastro', 'static'}
    if request.endpoint is None or request.endpoint in public_endpoints:
        return None

    if not current_user.is_authenticated:
        return login_manager.unauthorized()

    if current_user.perfil == 'Admin':
        return None

    if request.endpoint not in ROLE_ENDPOINTS.get(current_user.perfil, set()):
        abort(403)

    if current_user.perfil == 'Mecanico' and request.blueprint == 'ordens_servico':
        if (
            not current_user.mecanico_id
            or current_user.mecanico is None
            or not current_user.mecanico.ativo
        ):
            abort(403)

        view_args = request.view_args or {}
        ordem_id = view_args.get('id_os') or view_args.get('id')
        if ordem_id is not None:
            from app.models import OrdemServico

            assigned_order = OrdemServico.query.filter_by(
                id=ordem_id,
                mecanico_id=current_user.mecanico_id
            ).first()
            if assigned_order is None:
                abort(404)

    return None
