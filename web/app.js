/**
 * Recipe Planner — Frontend SPA Logic (Vanilla JS)
 */

let catalogoReceitas = [];
let planoAtual = null;
let listaComprasAtual = null;

let config = {
  dias: 7,
  pessoas: 2,
  refeicoesDia: 2,
  escolhasManuais: {} // { receita_id: refeicoes_cobertas }
};

let receitaParaTrocar = null;
let receitaAtualVisualizada = null;

// Elementos DOM
const dom = {
  tabs: document.querySelectorAll('.tab-btn'),
  tabContents: document.querySelectorAll('.tab-content'),
  inputDias: document.getElementById('input-dias'),
  btnDiasPresets: document.querySelectorAll('#dias-presets .btn-toggle'),
  btnMenosPessoas: document.getElementById('btn-menos-pessoas'),
  btnMaisPessoas: document.getElementById('btn-mais-pessoas'),
  labelPessoas: document.getElementById('label-pessoas'),
  selectRefeicoesDia: document.getElementById('select-refeicoes-dia'),
  badgeTotalRefeicoes: document.getElementById('badge-total-refeicoes'),
  badgeResumoCalculo: document.getElementById('badge-resumo-calculo'),
  btnGerarAleatorio: document.getElementById('btn-gerar-aleatorio'),
  toggleEscolhasManuais: document.getElementById('toggle-escolhas-manuais'),
  blocoEscolhasManuais: document.getElementById('bloco-escolhas-manuais'),
  listaSelecaoManual: document.getElementById('lista-selecao-manual'),
  btnAplicarEscolhas: document.getElementById('btn-aplicar-escolhas'),
  btnApenasSelecionadas: document.getElementById('btn-apenas-selecionadas'),
  gridPlano: document.getElementById('grid-plano'),
  emptyPlano: document.getElementById('empty-plano'),
  btnIrCompras: document.getElementById('btn-ir-compras'),
  containerCompras: document.getElementById('container-compras'),
  emptyCompras: document.getElementById('empty-compras'),
  comprasResumoCard: document.getElementById('compras-resumo-card'),
  metaDias: document.getElementById('meta-dias'),
  metaPessoas: document.getElementById('meta-pessoas'),
  metaRefeicoes: document.getElementById('meta-refeicoes'),
  btnCopiarCompras: document.getElementById('btn-copiar-compras'),
  btnWhatsappCompras: document.getElementById('btn-whatsapp-compras'),
  btnCopiarMd: document.getElementById('btn-copiar-md'),
  btnDescarregarCompras: document.getElementById('btn-descarregar-compras'),
  modalCopiarManual: document.getElementById('modal-copiar-manual'),
  modalCopiarTitulo: document.getElementById('modal-copiar-titulo'),
  textareaCopiarManual: document.getElementById('textarea-copiar-manual'),
  gridCatalogo: document.getElementById('grid-catalogo'),
  filtroPesquisa: document.getElementById('filtro-pesquisa'),
  filtroCategorias: document.getElementById('filtro-categorias'),
  formNovaReceita: document.getElementById('form-nova-receita'),
  modalReceita: document.getElementById('modal-receita'),
  modalRecTitulo: document.getElementById('modal-rec-titulo'),
  modalRecCorpo: document.getElementById('modal-rec-corpo'),
  modalEditar: document.getElementById('modal-editar'),
  modalEditarTitulo: document.getElementById('modal-editar-titulo'),
  formEditarReceita: document.getElementById('form-editar-receita'),
  editRecId: document.getElementById('edit-rec-id'),
  editRecTitulo: document.getElementById('edit-rec-titulo'),
  editRecDoses: document.getElementById('edit-rec-doses'),
  editRecPrep: document.getElementById('edit-rec-prep'),
  editRecCoz: document.getElementById('edit-rec-coz'),
  editRecDificuldade: document.getElementById('edit-rec-dificuldade'),
  editRecCategoria: document.getElementById('edit-rec-categoria'),
  editRecIngredientes: document.getElementById('edit-rec-ingredientes'),
  editRecInstrucoes: document.getElementById('edit-rec-instrucoes'),
  editRecNotas: document.getElementById('edit-rec-notas'),
  btnSalvarEdicao: document.getElementById('btn-salvar-edicao'),
  modalTrocar: document.getElementById('modal-trocar'),
  modalTrocarOrigem: document.getElementById('modal-trocar-origem'),
  selectNovaReceita: document.getElementById('select-nova-receita'),
  btnConfirmarTroca: document.getElementById('btn-confirmar-troca'),
  toast: document.getElementById('toast'),
};

// ==========================================
// INICIALIZAÇÃO
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
  configurarNavegacao();
  configurarControlosPlaneamento();
  configurarFormularioNovaReceita();
  configurarFormularioEditarReceita();

  await carregarCatalogo();
  await carregarPlanoAtual();
});

// ==========================================
// NOTIFICAÇÕES TOAST
// ==========================================
function mostrarToast(mensagem, duracao = 3000) {
  dom.toast.textContent = mensagem;
  dom.toast.classList.remove('hidden');
  setTimeout(() => {
    dom.toast.classList.add('hidden');
  }, duracao);
}

// ==========================================
// NAVEGAÇÃO ENTRE SEPARADORES
// ==========================================
function configurarNavegacao() {
  dom.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-tab');
      ativarSeparador(targetId);
    });
  });

  dom.btnIrCompras.addEventListener('click', () => {
    ativarSeparador('tab-compras');
  });
}

function ativarSeparador(tabId) {
  dom.tabs.forEach(t => {
    t.classList.toggle('active', t.getAttribute('data-tab') === tabId);
  });
  dom.tabContents.forEach(content => {
    content.classList.toggle('active', content.id === tabId);
  });
}

// ==========================================
// CONTROLOS DE CONFIGURAÇÃO DO PLANO
// ==========================================
function configurarControlosPlaneamento() {
  // Presets de Dias
  dom.btnDiasPresets.forEach(btn => {
    btn.addEventListener('click', () => {
      dom.btnDiasPresets.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      config.dias = parseInt(btn.getAttribute('data-dias'), 10);
      dom.inputDias.value = config.dias;
      atualizarSumarioCalculo();
    });
  });

  dom.inputDias.addEventListener('input', (e) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val) && val > 0) {
      config.dias = val;
      dom.btnDiasPresets.forEach(b => {
        b.classList.toggle('active', parseInt(b.getAttribute('data-dias'), 10) === val);
      });
      atualizarSumarioCalculo();
    }
  });

  // Pessoas (+ / -)
  dom.btnMenosPessoas.addEventListener('click', () => {
    if (config.pessoas > 1) {
      config.pessoas--;
      dom.labelPessoas.textContent = config.pessoas;
      atualizarSumarioCalculo();
    }
  });

  dom.btnMaisPessoas.addEventListener('click', () => {
    config.pessoas++;
    dom.labelPessoas.textContent = config.pessoas;
    atualizarSumarioCalculo();
  });

  // Refeições por dia
  dom.selectRefeicoesDia.addEventListener('change', (e) => {
    config.refeicoesDia = parseInt(e.target.value, 10);
    atualizarSumarioCalculo();
  });

  // Toggle do bloco de escolhas manuais
  dom.toggleEscolhasManuais.addEventListener('click', () => {
    dom.toggleEscolhasManuais.classList.toggle('open');
    dom.blocoEscolhasManuais.classList.toggle('open');
  });

  // Ações de geração
  dom.btnGerarAleatorio.addEventListener('click', () => {
    gerarPlano(false);
  });

  dom.btnAplicarEscolhas.addEventListener('click', () => {
    gerarPlano(true, true);
  });

  dom.btnApenasSelecionadas.addEventListener('click', () => {
    gerarPlano(true, false);
  });

  // Botões da lista de compras
  dom.btnCopiarCompras.addEventListener('click', copiarListaCompras);
  if (dom.btnWhatsappCompras) {
    dom.btnWhatsappCompras.addEventListener('click', abrirWhatsApp);
  }
  if (dom.btnCopiarMd) {
    dom.btnCopiarMd.addEventListener('click', copiarMarkdownCompras);
  }
  dom.btnDescarregarCompras.addEventListener('click', descarregarListaCompras);

  // Modal Troca
  dom.btnConfirmarTroca.addEventListener('click', confirmarTrocaRefeicao);

  // Filtros do Catálogo
  dom.filtroPesquisa.addEventListener('input', filtrarCatalogo);
  dom.filtroCategorias.addEventListener('click', (e) => {
    if (e.target.classList.contains('pill')) {
      document.querySelectorAll('#filtro-categorias .pill').forEach(p => p.classList.remove('active'));
      e.target.classList.add('active');
      filtrarCatalogo();
    }
  });
}

function atualizarSumarioCalculo() {
  const totalRef = config.dias * config.refeicoesDia;
  const dosesTotais = totalRef * config.pessoas;
  dom.badgeTotalRefeicoes.textContent = `Total: ${totalRef} refeições`;
  dom.badgeResumoCalculo.textContent = `(${config.dias} dias × ${config.refeicoesDia} ref. × ${config.pessoas} pessoas = ${dosesTotais} doses totais)`;
}

// ==========================================
// CARREGAR DADOS DA API
// ==========================================
async function carregarCatalogo() {
  try {
    const res = await fetch('/api/receitas');
    const data = await res.json();
    if (data.sucesso) {
      catalogoReceitas = data.receitas;
      renderizarCatalogo(catalogoReceitas);
      renderizarSelecaoManual();
    }
  } catch (err) {
    console.error('Erro ao carregar catálogo:', err);
    mostrarToast('Erro ao ligar ao servidor de receitas.');
  }
}

async function carregarPlanoAtual() {
  try {
    const res = await fetch('/api/plano');
    const data = await res.json();
    if (data.sucesso && data.plano) {
      planoAtual = data.plano;
      listaComprasAtual = data.lista_compras;
      renderizarPlano(planoAtual);
      renderizarListaCompras(listaComprasAtual, planoAtual);
    }
  } catch (err) {
    console.error('Erro ao carregar plano:', err);
  }
}

// ==========================================
// GERAÇÃO DE PLANO
// ==========================================
async function gerarPlano(usarManuais = false, preencherAleatorio = true) {
  const escolhas = [];
  if (usarManuais) {
    for (const [recId, count] of Object.entries(config.escolhasManuais)) {
      if (count > 0) {
        escolhas.push({ receita_id: recId, refeicoes: count });
      }
    }
  }

  if (usarManuais && !preencherAleatorio && escolhas.length === 0) {
    mostrarToast('⚠️ Selecione pelo menos uma receita manual.');
    return;
  }

  const payload = {
    dias: config.dias,
    pessoas: config.pessoas,
    refeicoes_dia: config.refeicoesDia,
    escolhas: escolhas,
    preencher_aleatorio: preencherAleatorio,
    escalar_selecionadas: !preencherAleatorio
  };

  try {
    dom.btnGerarAleatorio.disabled = true;
    if (dom.btnAplicarEscolhas) dom.btnAplicarEscolhas.disabled = true;
    if (dom.btnApenasSelecionadas) dom.btnApenasSelecionadas.disabled = true;

    if (!preencherAleatorio && dom.btnApenasSelecionadas) {
      dom.btnApenasSelecionadas.textContent = 'A ajustar quantidades...';
    } else {
      dom.btnGerarAleatorio.textContent = 'A gerar plano...';
    }

    const res = await fetch('/api/planear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.sucesso) {
      planoAtual = data.plano;
      listaComprasAtual = data.lista_compras;

      // Se usou apenas as selecionadas, sincronizar contadores manuais com os valores ajustados
      if (!preencherAleatorio && planoAtual && planoAtual.itens) {
        const itensMap = {};
        planoAtual.itens.forEach(it => {
          itensMap[it.receita_id] = it.refeicoes_cobertas;
        });
        for (const recId of Object.keys(config.escolhasManuais)) {
          const novoVal = itensMap[recId] || 0;
          config.escolhasManuais[recId] = novoVal;
          const el = document.getElementById(`manual-val-${recId}`);
          if (el) el.textContent = novoVal;
        }
      }

      renderizarPlano(planoAtual);
      renderizarListaCompras(listaComprasAtual, planoAtual);

      if (!preencherAleatorio) {
        mostrarToast(`✅ Quantidades ajustadas para cobrir as ${planoAtual.total_refeicoes_planeadas} refeições do plano!`);
      } else {
        mostrarToast('✅ Plano gerado e lista de compras atualizada!');
      }
    } else {
      mostrarToast(`❌ ${data.erro || 'Erro ao gerar plano'}`);
    }
  } catch (err) {
    console.error(err);
    mostrarToast('Erro de comunicação com o servidor.');
  } finally {
    dom.btnGerarAleatorio.disabled = false;
    dom.btnGerarAleatorio.innerHTML = '<span>✨</span> Gerar Plano Completo';
    if (dom.btnAplicarEscolhas) dom.btnAplicarEscolhas.disabled = false;
    if (dom.btnApenasSelecionadas) {
      dom.btnApenasSelecionadas.disabled = false;
      dom.btnApenasSelecionadas.innerHTML = '<span>🔒</span> Usar Apenas as Selecionadas';
    }
  }
}

// ==========================================
// RENDERIZAÇÃO DO PLANO
// ==========================================
function renderizarPlano(plano) {
  if (!plano || !plano.itens || plano.itens.length === 0) {
    dom.emptyPlano.classList.remove('hidden');
    dom.gridPlano.classList.add('hidden');
    return;
  }

  dom.emptyPlano.classList.add('hidden');
  dom.gridPlano.classList.remove('hidden');
  dom.gridPlano.innerHTML = '';

  plano.itens.forEach((item, idx) => {
    const card = document.createElement('div');
    card.className = 'plano-card';

    const escalaFmt = item.fator_escala !== 1.0 ? `${item.fator_escala.toFixed(2)}x` : '1x';

    card.innerHTML = `
      <div>
        <div class="plano-card-header">
          <h4 class="plano-card-title">${item.titulo}</h4>
          <span class="badge-scale">${escalaFmt}</span>
        </div>
        <div class="plano-card-meta mt-3">
          <span class="badge-tag">🍛 Cobre ${item.refeicoes_cobertas} refeição(ões)</span>
          <span class="badge-tag">👥 ${item.doses_necessarias} doses totais</span>
          <span class="badge-tag">Base: ${item.doses_base} doses</span>
        </div>
      </div>
      <div class="plano-card-actions">
        <button class="btn btn-outline btn-sm" onclick="abrirModalTrocar('${item.receita_id}', '${item.titulo.replace(/'/g, "\\'")}')">
          🔄 Trocar
        </button>
        <button class="btn btn-secondary btn-sm" onclick="verDetalhesReceita('${item.receita_id}')">
          👁️ Ver Receita
        </button>
      </div>
    `;

    dom.gridPlano.appendChild(card);
  });
}

// ==========================================
// RENDERIZAÇÃO DA LISTA DE COMPRAS
// ==========================================
function renderizarListaCompras(compras, plano) {
  if (!compras || !compras.seccoes || Object.keys(compras.seccoes).length === 0) {
    dom.emptyCompras.classList.remove('hidden');
    dom.comprasResumoCard.classList.add('hidden');
    dom.containerCompras.classList.add('hidden');
    return;
  }

  dom.emptyCompras.classList.add('hidden');
  dom.comprasResumoCard.classList.remove('hidden');
  dom.containerCompras.classList.remove('hidden');

  dom.metaDias.textContent = plano.dias;
  dom.metaPessoas.textContent = plano.pessoas;
  dom.metaRefeicoes.textContent = plano.total_refeicoes_planeadas;

  dom.containerCompras.innerHTML = '';

  for (const [seccao, itens] of Object.entries(compras.seccoes)) {
    if (!itens || itens.length === 0) continue;

    const secCard = document.createElement('div');
    secCard.className = 'compras-section-card';

    const secTitle = document.createElement('h3');
    secTitle.className = 'compras-section-title';
    secTitle.textContent = `📍 ${seccao}`;
    secCard.appendChild(secTitle);

    const ul = document.createElement('ul');
    ul.className = 'compras-list';

    itens.forEach(it => {
      const li = document.createElement('li');
      li.className = 'compras-item';

      const check = document.createElement('input');
      check.type = 'checkbox';
      check.addEventListener('change', () => {
        li.classList.toggle('checked', check.checked);
      });

      const spanText = document.createElement('span');
      spanText.className = 'compras-item-text';

      const conetor = it.quantidade_str && !it.nome.toLowerCase().startsWith('de ') ? ' de ' : ' ';
      const qtdPart = it.quantidade_str ? `${it.quantidade_str}${conetor}` : '';
      const origens = it.receitas && it.receitas.length > 0 ? ` (${it.receitas.join(', ')})` : '';

      spanText.innerHTML = `<strong>${qtdPart}${it.nome}</strong><span class="compras-item-origem">${origens}</span>`;

      li.appendChild(check);
      li.appendChild(spanText);
      ul.appendChild(li);
    });

    secCard.appendChild(ul);
    dom.containerCompras.appendChild(secCard);
  }
}

function obterTextoListaWhatsApp() {
  if (!listaComprasAtual || !listaComprasAtual.seccoes) {
    return '';
  }

  let textoSimples = `🛒 LISTA DE COMPRAS (${planoAtual ? planoAtual.dias : 7} dias, ${planoAtual ? planoAtual.pessoas : 2} pessoas)\n\n`;

  for (const [seccao, itens] of Object.entries(listaComprasAtual.seccoes)) {
    if (!itens || itens.length === 0) continue;
    textoSimples += `*${seccao}*\n`;
    itens.forEach(it => {
      const conetor = it.quantidade_str && !it.nome.toLowerCase().startsWith('de ') ? ' de ' : ' ';
      const qtd = it.quantidade_str ? `${it.quantidade_str}${conetor}` : '';
      textoSimples += `[ ] ${qtd}${it.nome}\n`;
    });
    textoSimples += '\n';
  }

  return textoSimples.trim();
}

/**
 * Fallback de cópia para Android/iOS e contextos HTTP não-seguros via document.execCommand
 */
function fallbackCopiar(texto) {
  const textarea = document.createElement('textarea');
  textarea.value = texto;
  // readonly previne o teclado virtual de abrir no Android durante a seleção
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.top = '0';
  textarea.style.left = '0';
  textarea.style.width = '2em';
  textarea.style.height = '2em';
  textarea.style.padding = '0';
  textarea.style.border = 'none';
  textarea.style.outline = 'none';
  textarea.style.boxShadow = 'none';
  textarea.style.background = 'transparent';
  textarea.style.opacity = '0';
  textarea.style.zIndex = '-9999';

  document.body.appendChild(textarea);

  textarea.focus();
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);

  let copiado = false;
  try {
    copiado = document.execCommand('copy');
  } catch (err) {
    console.warn('document.execCommand falhou:', err);
    copiado = false;
  }

  document.body.removeChild(textarea);
  return copiado;
}

/**
 * Copia texto com deteção automática de suporte (Clipboard API ou execCommand)
 * e abre modal de seleção manual como contingência em mobile restritivo.
 */
async function copiarParaAreaDeTransferencia(texto, titulo = 'Lista de Compras') {
  // 1. Tentar Clipboard API moderna se estiver num contexto seguro (HTTPS ou localhost)
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(texto);
      return true;
    } catch (err) {
      console.warn('navigator.clipboard.writeText falhou, a tentar fallback:', err);
    }
  }

  // 2. Fallback robusto para dispositivos Android/iOS acedendo via HTTP (IP local)
  if (fallbackCopiar(texto)) {
    return true;
  }

  // 3. Fallback de contingência caso o navegador bloqueie acesso à área de transferência
  abrirModalCopiarManual(texto, titulo);
  return false;
}

async function copiarListaCompras() {
  const texto = obterTextoListaWhatsApp();
  if (!texto) {
    mostrarToast('Nenhuma lista de compras ativa.');
    return;
  }

  const copiou = await copiarParaAreaDeTransferencia(texto, 'Lista de Compras (WhatsApp/Notas)');
  if (copiou) {
    mostrarToast('📋 Lista copiada para a área de transferência!');
  }
}

async function copiarMarkdownCompras() {
  if (!listaComprasAtual || !listaComprasAtual.markdown) {
    mostrarToast('Nenhuma lista de compras ativa.');
    return;
  }

  const copiou = await copiarParaAreaDeTransferencia(listaComprasAtual.markdown, 'Markdown da Lista');
  if (copiou) {
    mostrarToast('📝 Markdown copiado para a área de transferência!');
  }
}

function abrirWhatsApp() {
  const texto = obterTextoListaWhatsApp();
  if (!texto) {
    mostrarToast('Nenhuma lista de compras ativa.');
    return;
  }

  // Se o browser móvel tiver a Web Share API, partilhar nativamente
  if (navigator.share && window.isSecureContext) {
    navigator.share({
      title: 'Lista de Compras — Recipe Planner',
      text: texto
    }).catch(() => {
      // Se utilizador cancelou ou falhou, abrir fallback WhatsApp
      const urlWa = `https://api.whatsapp.com/send?text=${encodeURIComponent(texto)}`;
      window.open(urlWa, '_blank');
    });
    return;
  }

  // Fallback universal: link oficial do WhatsApp Web/App
  const urlWhatsapp = `https://api.whatsapp.com/send?text=${encodeURIComponent(texto)}`;
  window.open(urlWhatsapp, '_blank');
}

function descarregarListaCompras() {
  if (!listaComprasAtual || !listaComprasAtual.markdown) {
    mostrarToast('Nenhuma lista de compras ativa.');
    return;
  }

  try {
    const blob = new Blob([listaComprasAtual.markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `lista_compras_${planoAtual ? planoAtual.dias : 7}dias.md`;
    document.body.appendChild(a);
    a.click();

    // Atraso seguro para o Android iniciar a transferência antes de revogar o blob
    setTimeout(() => {
      if (document.body.contains(a)) {
        document.body.removeChild(a);
      }
      URL.revokeObjectURL(url);
    }, 4000);

    mostrarToast('💾 Ficheiro Markdown descarregado!');
  } catch (err) {
    console.error('Erro ao descarregar ficheiro:', err);
    mostrarToast('Erro ao descarregar ficheiro.');
  }
}

// Modal de contingência para cópia manual
window.abrirModalCopiarManual = function(texto, titulo = 'Copiar Lista') {
  if (dom.modalCopiarTitulo) dom.modalCopiarTitulo.textContent = `📋 ${titulo}`;
  if (dom.textareaCopiarManual) {
    dom.textareaCopiarManual.value = texto;
  }
  if (dom.modalCopiarManual) {
    dom.modalCopiarManual.classList.remove('hidden');
    setTimeout(() => {
      selecionarTextoCopiarManual();
    }, 150);
  }
};

window.fecharModalCopiarManual = function() {
  if (dom.modalCopiarManual) {
    dom.modalCopiarManual.classList.add('hidden');
  }
};

window.selecionarTextoCopiarManual = function() {
  if (dom.textareaCopiarManual) {
    dom.textareaCopiarManual.focus();
    dom.textareaCopiarManual.select();
    dom.textareaCopiarManual.setSelectionRange(0, dom.textareaCopiarManual.value.length);
    try {
      const copiou = document.execCommand('copy');
      if (copiou) {
        mostrarToast('📋 Texto copiado com sucesso!');
      }
    } catch (e) {
      // Mantém selecionado para cópia manual via menu móvel
    }
  }
};

// ==========================================
// SELEÇÃO MANUAL DE REFEIÇÕES
// ==========================================
function renderizarSelecaoManual() {
  dom.listaSelecaoManual.innerHTML = '';
  catalogoReceitas.forEach(r => {
    const item = document.createElement('div');
    item.className = 'manual-pick-item';

    const count = config.escolhasManuais[r.id] || 0;

    item.innerHTML = `
      <span class="manual-pick-name">${r.titulo}</span>
      <div class="manual-pick-counter">
        <button type="button" class="btn-counter btn-sm" onclick="ajustarEscolhaManual('${r.id}', -1)">-</button>
        <span id="manual-val-${r.id}" class="counter-value font-medium">${count}</span>
        <button type="button" class="btn-counter btn-sm" onclick="ajustarEscolhaManual('${r.id}', 1)">+</button>
      </div>
    `;
    dom.listaSelecaoManual.appendChild(item);
  });
}

window.ajustarEscolhaManual = function(recId, delta) {
  const atual = config.escolhasManuais[recId] || 0;
  const novo = Math.max(0, atual + delta);
  config.escolhasManuais[recId] = novo;
  const el = document.getElementById(`manual-val-${recId}`);
  if (el) el.textContent = novo;
};

// ==========================================
// TROCA DE REFEIÇÃO (MODAL)
// ==========================================
window.abrirModalTrocar = function(recId, titulo) {
  receitaParaTrocar = recId;
  dom.modalTrocarOrigem.textContent = titulo;

  dom.selectNovaReceita.innerHTML = '';
  catalogoReceitas.forEach(r => {
    if (r.id !== recId) {
      const opt = document.createElement('option');
      opt.value = r.id;
      opt.textContent = `${r.titulo} (${r.doses} doses)`;
      dom.selectNovaReceita.appendChild(opt);
    }
  });

  dom.modalTrocar.classList.remove('hidden');
};

window.fecharModalTrocar = function() {
  dom.modalTrocar.classList.add('hidden');
  receitaParaTrocar = null;
};

async function confirmarTrocaRefeicao() {
  const novaRecId = dom.selectNovaReceita.value;
  if (!receitaParaTrocar || !novaRecId) return;

  try {
    const res = await fetch('/api/trocar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        remover: receitaParaTrocar,
        adicionar: novaRecId
      })
    });
    const data = await res.json();
    if (data.sucesso) {
      planoAtual = data.plano;
      listaComprasAtual = data.lista_compras;
      renderizarPlano(planoAtual);
      renderizarListaCompras(listaComprasAtual, planoAtual);
      fecharModalTrocar();
      mostrarToast(`🔄 Substituído por ${data.adicionado}!`);
    } else {
      mostrarToast(`❌ ${data.erro || 'Erro ao trocar'}`);
    }
  } catch (err) {
    console.error(err);
    mostrarToast('Erro de comunicação com o servidor.');
  }
}

// ==========================================
// CATÁLOGO DE RECEITAS E DETALHES
// ==========================================
function renderizarCatalogo(receitas) {
  dom.gridCatalogo.innerHTML = '';
  if (receitas.length === 0) {
    dom.gridCatalogo.innerHTML = '<p class="text-muted">Nenhuma receita encontrada com estes filtros.</p>';
    return;
  }

  receitas.forEach(r => {
    const card = document.createElement('div');
    card.className = 'recipe-card';

    const cats = r.categoria && r.categoria.length > 0 ? r.categoria.join(', ') : 'Geral';
    const tempo = r.tempo_total || `${r.tempo_preparacao || ''} ${r.tempo_cozedura ? '+ ' + r.tempo_cozedura : ''}`.trim() || 'Rápido';

    card.innerHTML = `
      <div>
        <h3 class="recipe-card-title">${r.titulo}</h3>
        <div class="recipe-meta-row">
          <span>👥 ${r.doses} doses</span>
          <span>⏱️ ${tempo}</span>
          <span>🏷️ ${cats}</span>
        </div>
      </div>
      <div class="recipe-card-actions">
        <button class="btn btn-outline btn-sm flex-1" onclick="verDetalhesReceita('${r.id}')">
          👁️ Ver
        </button>
        <button class="btn btn-secondary btn-sm flex-1" onclick="abrirModalEditar('${r.id}')">
          ✏️ Editar
        </button>
      </div>
    `;

    dom.gridCatalogo.appendChild(card);
  });
}

function filtrarCatalogo() {
  const termo = dom.filtroPesquisa.value.toLowerCase().trim();
  const catPill = document.querySelector('#filtro-categorias .pill.active');
  const catFiltro = catPill ? catPill.getAttribute('data-cat').toLowerCase() : '';

  const filtradas = catalogoReceitas.filter(r => {
    const matchTermo = !termo || r.titulo.toLowerCase().includes(termo);
    const matchCat = !catFiltro || (r.categoria && r.categoria.some(c => c.toLowerCase().includes(catFiltro)));
    return matchTermo && matchCat;
  });

  renderizarCatalogo(filtradas);
}

window.verDetalhesReceita = async function(recId) {
  try {
    const res = await fetch(`/api/receitas/${recId}`);
    const data = await res.json();
    if (!data.sucesso) {
      mostrarToast('Receita não encontrada.');
      return;
    }
    const r = data.receita;
    receitaAtualVisualizada = r.id;
    dom.modalRecTitulo.textContent = r.titulo;

    let html = `
      <div class="recipe-meta-row mb-4">
        <span><strong>Doses base:</strong> ${r.doses} pessoas</span>
        ${r.tempo_preparacao ? `<span><strong>Prep:</strong> ${r.tempo_preparacao}</span>` : ''}
        ${r.tempo_cozedura ? `<span><strong>Cozedura:</strong> ${r.tempo_cozedura}</span>` : ''}
        ${r.dificuldade ? `<span><strong>Dificuldade:</strong> ${r.dificuldade}</span>` : ''}
      </div>
      
      <h4 class="mb-2">📋 Ingredientes:</h4>
      <ul class="mb-4" style="padding-left: 20px; line-height: 1.8;">
        ${r.ingredientes.map(i => `<li>${i.texto} <span class="badge-tag">${i.categoria}</span></li>`).join('')}
      </ul>

      <h4 class="mb-2">👩‍🍳 Modo de Preparação:</h4>
      <ol class="mb-4" style="padding-left: 20px; line-height: 1.8;">
        ${r.instrucoes.map(inst => `<li>${inst.replace(/^\d+\.\s*/, '')}</li>`).join('')}
      </ol>
    `;

    if (r.notas && r.notas.length > 0) {
      html += `
        <h4 class="mb-2">💡 Notas:</h4>
        <ul style="padding-left: 20px; line-height: 1.6;">
          ${r.notas.map(n => `<li>${n.replace(/^-\s*/, '')}</li>`).join('')}
        </ul>
      `;
    }

    dom.modalRecCorpo.innerHTML = html;
    dom.modalReceita.classList.remove('hidden');
  } catch (err) {
    console.error(err);
    mostrarToast('Erro ao carregar detalhes da receita.');
  }
};

window.fecharModalReceita = function() {
  dom.modalReceita.classList.add('hidden');
};

window.editarReceitaAtual = function() {
  if (receitaAtualVisualizada) {
    const idParaEditar = receitaAtualVisualizada;
    fecharModalReceita();
    abrirModalEditar(idParaEditar);
  }
};

// ==========================================
// EDIÇÃO DE RECEITA (MODAL)
// ==========================================
window.abrirModalEditar = async function(recId) {
  try {
    const res = await fetch(`/api/receitas/${recId}`);
    const data = await res.json();
    if (!data.sucesso) {
      mostrarToast('Erro ao carregar receita para edição.');
      return;
    }

    const r = data.receita;
    dom.editRecId.value = r.id;
    dom.editRecTitulo.value = r.titulo;
    dom.editRecDoses.value = r.doses;
    dom.editRecPrep.value = r.tempo_preparacao || '';
    dom.editRecCoz.value = r.tempo_cozedura || '';
    dom.editRecDificuldade.value = r.dificuldade || 'Fácil';
    dom.editRecCategoria.value = r.categoria_str || (Array.isArray(r.categoria) ? r.categoria.join(', ') : '');
    dom.editRecIngredientes.value = r.ingredientes_bruto || '';
    dom.editRecInstrucoes.value = r.instrucoes_bruto || '';
    dom.editRecNotas.value = r.notas_bruto || '';

    dom.modalEditarTitulo.textContent = `✏️ Editar Receita: ${r.titulo}`;
    dom.modalEditar.classList.remove('hidden');
  } catch (err) {
    console.error(err);
    mostrarToast('Erro ao abrir editor de receita.');
  }
};

window.fecharModalEditar = function() {
  dom.modalEditar.classList.add('hidden');
};

function configurarFormularioEditarReceita() {
  dom.formEditarReceita.addEventListener('submit', async (e) => {
    e.preventDefault();

    const recId = dom.editRecId.value;
    if (!recId) return;

    const payload = {
      titulo: dom.editRecTitulo.value.trim(),
      doses: parseInt(dom.editRecDoses.value, 10),
      tempo_preparacao: dom.editRecPrep.value.trim(),
      tempo_cozedura: dom.editRecCoz.value.trim(),
      dificuldade: dom.editRecDificuldade.value,
      categoria: dom.editRecCategoria.value.trim(),
      ingredientes: dom.editRecIngredientes.value.trim(),
      instrucoes: dom.editRecInstrucoes.value.trim(),
      notas: dom.editRecNotas.value.trim()
    };

    try {
      dom.btnSalvarEdicao.disabled = true;
      dom.btnSalvarEdicao.innerHTML = '<span>⏳</span> A guardar...';

      const res = await fetch(`/api/receitas/${recId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.sucesso) {
        mostrarToast(`✅ ${data.mensagem}`);
        fecharModalEditar();
        await carregarCatalogo();
        await carregarPlanoAtual();
      } else {
        mostrarToast(`❌ ${data.erro || 'Erro ao atualizar receita'}`);
      }
    } catch (err) {
      console.error(err);
      mostrarToast('Erro de comunicação ao atualizar receita.');
    } finally {
      dom.btnSalvarEdicao.disabled = false;
      dom.btnSalvarEdicao.innerHTML = '<span>💾</span> Guardar Alterações';
    }
  });
}

// ==========================================
// FORMULÁRIO DE NOVA RECEITA
// ==========================================
function configurarFormularioNovaReceita() {
  dom.formNovaReceita.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      titulo: document.getElementById('rec-titulo').value.trim(),
      doses: parseInt(document.getElementById('rec-doses').value, 10),
      tempo_preparacao: document.getElementById('rec-prep').value.trim(),
      tempo_cozedura: document.getElementById('rec-coz').value.trim(),
      dificuldade: document.getElementById('rec-dificuldade').value,
      categoria: document.getElementById('rec-categoria').value.trim(),
      ingredientes: document.getElementById('rec-ingredientes').value.trim(),
      instrucoes: document.getElementById('rec-instrucoes').value.trim(),
      notas: document.getElementById('rec-notas').value.trim()
    };

    try {
      const res = await fetch('/api/receitas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.sucesso) {
        mostrarToast(`✅ ${data.mensagem}`);
        dom.formNovaReceita.reset();
        await carregarCatalogo();
        ativarSeparador('tab-receitas');
      } else {
        mostrarToast(`❌ ${data.erro || 'Erro ao guardar receita'}`);
      }
    } catch (err) {
      console.error(err);
      mostrarToast('Erro de comunicação ao gravar receita.');
    }
  });
}
