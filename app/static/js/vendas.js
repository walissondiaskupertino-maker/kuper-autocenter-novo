(function () {
    const form = document.getElementById('form-venda');
    if (!form) return;

    const body = document.getElementById('itens-venda');
    const template = document.getElementById('modelo-linha-item');
    const cliente = document.getElementById('cliente_id');
    const veiculo = document.getElementById('veiculo_id');
    const desconto = document.getElementById('desconto');
    const subtotalDisplay = document.getElementById('subtotal-venda');
    const totalDisplay = document.getElementById('total-venda');
    const emptyMessage = document.getElementById('sem-itens');
    const formatarMoeda = new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    });

    function valorDecimal(valor) {
        const texto = String(valor || '').trim();
        if (!texto) return 0;
        return Number(texto.includes(',')
            ? texto.replace(/\./g, '').replace(',', '.')
            : texto) || 0;
    }

    function filtrarVeiculos() {
        const clienteId = cliente.value;
        Array.from(veiculo.options).forEach((opcao) => {
            opcao.hidden = Boolean(opcao.value)
                && (!clienteId || opcao.dataset.clienteId !== clienteId);
        });
        if (veiculo.selectedOptions[0]?.hidden) veiculo.value = '0';
    }

    function filtrarCatalogo(linha) {
        const tipo = linha.querySelector('.tipo-item').value;
        const item = linha.querySelector('.item-catalogo');
        item.disabled = !tipo;
        Array.from(item.options).forEach((opcao) => {
            opcao.hidden = Boolean(opcao.value) && opcao.dataset.tipo !== tipo;
        });
        if (item.selectedOptions[0]?.hidden) item.value = '';
        calcularTotais();
    }

    function calcularTotais() {
        let subtotal = 0;
        body.querySelectorAll('.linha-item').forEach((linha) => {
            const produto = linha.querySelector('.item-catalogo').selectedOptions[0];
            const quantidade = Number(linha.querySelector('.quantidade-item').value) || 0;
            const valorUnitario = Number(produto?.dataset.preco) || 0;
            const valorLinha = valorUnitario * quantidade;
            subtotal += valorLinha;
            linha.querySelector('.subtotal-item').textContent = formatarMoeda.format(valorLinha);
        });
        const total = Math.max(0, subtotal - valorDecimal(desconto.value));
        subtotalDisplay.textContent = formatarMoeda.format(subtotal);
        totalDisplay.textContent = formatarMoeda.format(total);
        emptyMessage.hidden = body.querySelectorAll('.linha-item').length > 0;
    }

    function adicionarLinha(itemInicial) {
        const linha = template.content.firstElementChild.cloneNode(true);
        const tipo = linha.querySelector('.tipo-item');
        const item = linha.querySelector('.item-catalogo');
        tipo.addEventListener('change', () => filtrarCatalogo(linha));
        item.addEventListener('change', calcularTotais);
        linha.querySelector('.quantidade-item').addEventListener('input', calcularTotais);
        linha.querySelector('.remover-item').addEventListener('click', () => {
            linha.remove();
            calcularTotais();
        });
        body.appendChild(linha);
        if (itemInicial) {
            tipo.value = itemInicial.tipo;
            filtrarCatalogo(linha);
            item.value = itemInicial.id;
            linha.querySelector('.quantidade-item').value = itemInicial.quantidade;
        }
        calcularTotais();
    }

    document.getElementById('adicionar-item').addEventListener('click', () => adicionarLinha());
    cliente.addEventListener('change', filtrarVeiculos);
    desconto.addEventListener('input', calcularTotais);
    form.addEventListener('submit', () => {
        document.querySelectorAll('[data-decimal]').forEach((input) => {
            input.value = valorDecimal(input.value).toFixed(2);
        });
    });

    filtrarVeiculos();
    const initialItems = JSON.parse(document.getElementById('itens-iniciais').textContent || '[]');
    initialItems.forEach(adicionarLinha);
    calcularTotais();
})();
