/**
 * Sistema de Chamados - Colégio Mauá
 * JavaScript Vanilla - Frontend completo
 */

document.addEventListener('DOMContentLoaded', function() {

    // ═══════════════════════════════════════════════════════════════
    // PROTEÇÃO: Evitar que links abram em nova aba indevidamente
    // ═══════════════════════════════════════════════════════════════
    document.querySelectorAll('a[target="_blank"]').forEach(function(link) {
        link.removeAttribute('target');
    });

    // Remover qualquer <base target="_blank"> se existir
    const baseTag = document.querySelector('base[target]');
    if (baseTag) {
        baseTag.removeAttribute('target');
    }

    // ── Sidebar Toggle ──
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const isMobile = function() { return window.innerWidth <= 768; };

    // Desktop: toggle collapsed
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            if (isMobile()) {
                // Mobile: toggle active (abre/fecha sidebar)
                sidebar.classList.toggle('active');
                if (sidebarOverlay) sidebarOverlay.classList.toggle('active');
            } else {
                // Desktop: toggle collapsed (recolhe/expande)
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            }
        });

        // Restaurar estado desktop
        if (!isMobile() && localStorage.getItem('sidebarCollapsed') === 'true') {
            sidebar.classList.add('collapsed');
        }
    }

    // Mobile: botão hamburguer abre sidebar
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.add('active');
            sidebar.classList.remove('collapsed');
            if (sidebarOverlay) sidebarOverlay.classList.add('active');
        });
    }

    // Overlay fecha sidebar
    if (sidebarOverlay && sidebar) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    // Fechar sidebar ao clicar em link (mobile)
    document.querySelectorAll('.sidebar-nav a').forEach(function(link) {
        link.addEventListener('click', function() {
            if (isMobile()) {
                sidebar.classList.remove('active');
                if (sidebarOverlay) sidebarOverlay.classList.remove('active');
            }
        });
    });

    // Ajustar ao redimensionar janela
    window.addEventListener('resize', function() {
        if (!isMobile()) {
            sidebar.classList.remove('active');
            if (sidebarOverlay) sidebarOverlay.classList.remove('active');
            if (localStorage.getItem('sidebarCollapsed') === 'true') {
                sidebar.classList.add('collapsed');
            } else {
                sidebar.classList.remove('collapsed');
            }
        } else {
            sidebar.classList.remove('collapsed');
        }
    });

    // ── Flash Messages Auto Dismiss ──
    const flashMessages = document.querySelectorAll('.flash[data-auto-dismiss]');
    flashMessages.forEach(function(flash) {
        setTimeout(function() {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(function() {
                flash.remove();
            }, 300);
        }, 5000);
    });

    // ── Flash Close Button ──
    document.querySelectorAll('.flash-close').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const flash = this.closest('.flash');
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(function() {
                flash.remove();
            }, 300);
        });
    });

    // ── Toggle Password Visibility ──
    document.querySelectorAll('.toggle-password').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // ── Notifications Dropdown ──
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationsDropdown = document.getElementById('notificationsDropdown');

    if (notificationBtn && notificationsDropdown) {
        notificationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationsDropdown.classList.toggle('active');
            if (notificationsDropdown.classList.contains('active')) {
                carregarNotificacoes();
            }
        });

        document.addEventListener('click', function(e) {
            if (!notificationsDropdown.contains(e.target) && !notificationBtn.contains(e.target)) {
                notificationsDropdown.classList.remove('active');
            }
        });
    }

    // ── Mark All Notifications Read ──
    const markAllReadBtn = document.getElementById('markAllRead');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            fetch('/notificacoes/ler-todas', { method: 'POST' })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success) {
                        atualizarContadorNotificacoes(0);
                        notificationsDropdown.classList.remove('active');
                    }
                });
        });
    }

    // ── Carregar contador de notificações ──
    atualizarContadorNotificacoes();
    setInterval(atualizarContadorNotificacoes, 5000); // Atualizar a cada 5s

    // ── Scroll to Top Button ──
    const scrollToTopBtn = document.getElementById('scrollToTop');
    if (scrollToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                scrollToTopBtn.classList.add('visible');
            } else {
                scrollToTopBtn.classList.remove('visible');
            }
        });
    }

    // ── File Input Label Update ──
    document.querySelectorAll('input[type="file"]').forEach(function(input) {
        input.addEventListener('change', function() {
            const label = this.nextElementSibling;
            if (label && this.files.length > 0) {
                label.innerHTML = '<i class="fas fa-file"></i> ' + this.files[0].name;
            }
        });
    });

    // ── Form Validation ──
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    valid = false;
                    field.style.borderColor = '#dc3545';
                    field.style.boxShadow = '0 0 0 3px rgba(220, 53, 69, 0.1)';
                } else {
                    field.style.borderColor = '';
                    field.style.boxShadow = '';
                }
            });

            if (!valid) {
                e.preventDefault();
                mostrarToast('Preencha todos os campos obrigatórios.', 'error');
            }
        });

        // Limpar erro ao digitar
        form.querySelectorAll('input, select, textarea').forEach(function(field) {
            field.addEventListener('input', function() {
                this.style.borderColor = '';
                this.style.boxShadow = '';
            });
        });
    });

    // ── Smooth scroll para âncoras ──
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

// ── Loading state em botões de submit ──
document.querySelectorAll('form').forEach(function(form) {

    form.addEventListener('submit', function(e) {

        /*
         * Não ativar o carregamento quando outro validador
         * já bloqueou o envio (ex.: senha em branco no login).
         * checkValidity também considera o required e o tipo e-mail,
         * inclusive quando o form usa novalidate.
         */
        if (form.id === 'chatwaForm' || e.defaultPrevented) {
            return;
        }

        if (!form.checkValidity()) {
            e.preventDefault();
            // O botão continua habilitado para permitir corrigir os campos.
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');

        if (submitBtn && !submitBtn.dataset.noLoading && !submitBtn.disabled) {
            submitBtn.dataset.originalText = submitBtn.innerHTML;
            submitBtn.innerHTML =
                '<i class="fas fa-spinner fa-spin"></i> Processando...';
            submitBtn.disabled = true;
        }

    });

});

    // ── DataTables-like sorting (simples) ──
    document.querySelectorAll('.data-table th[data-sort]').forEach(function(th) {
        th.style.cursor = 'pointer';
        th.addEventListener('click', function() {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const colIndex = Array.from(th.parentElement.children).indexOf(th);
            const sortDir = th.dataset.sortDir === 'asc' ? 'desc' : 'asc';

            // Resetar outros headers
            table.querySelectorAll('th[data-sort]').forEach(function(h) {
                h.dataset.sortDir = '';
                h.querySelector('.sort-icon')?.remove();
            });

            th.dataset.sortDir = sortDir;
            th.innerHTML += ' <span class="sort-icon"><i class="fas fa-sort-' + (sortDir === 'asc' ? 'up' : 'down') + '"></i></span>';

            rows.sort(function(a, b) {
                const aVal = a.children[colIndex].textContent.trim();
                const bVal = b.children[colIndex].textContent.trim();
                return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            });

            rows.forEach(function(row) {
                tbody.appendChild(row);
            });
        });
    });
});

/**
 * Scroll to top - função global
 */
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Atualiza o contador de notificações na interface
 */
function atualizarContadorNotificacoes(count) {
    if (typeof count === 'number') {
        atualizarBadge(count);
        return;
    }

    fetch('/api/notificacoes/nao-lidas')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            atualizarBadge(data.count);
            atualizarDropdown(data.notificacoes);
        })
        .catch(function(err) {
            console.error('Erro ao carregar notificações:', err);
        });
}

function atualizarBadge(count) {
    const badges = document.querySelectorAll('#notifCount, #topNotifCount');
    badges.forEach(function(badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    });
}

function atualizarDropdown(notificacoes) {
    const list = document.getElementById('notificationsList');
    if (!list) return;

    if (!notificacoes || notificacoes.length === 0) {
        list.innerHTML = '<div class="notification-empty">Nenhuma notificação nova</div>';
        return;
    }

    list.replaceChildren();
    notificacoes.forEach(function (n) {
        const item = document.createElement('a');
        item.className = 'notificacao-item notificacao-nao-lida';
        const endereco = typeof n.link === 'string' ? n.link : '';
        // A notificação nunca pode redirecionar para um domínio externo.
        let destino = '/notificacoes';
        if (/^\/chamados\/\d+(?:[?#].*)?$/.test(endereco)) destino = endereco;
        item.href = destino;
        item.style.cssText = 'display:flex;text-decoration:none;color:inherit;cursor:pointer;';
        const icone = document.createElement('div');
        icone.className = 'notificacao-icon';
        icone.innerHTML = '<i class="fas fa-bell"></i>';
        const conteudo = document.createElement('div');
        conteudo.className = 'notificacao-conteudo';
        const titulo = document.createElement('h4');
        titulo.className = 'notificacao-titulo';
        titulo.textContent = n.titulo || 'Notificação';
        const mensagem = document.createElement('p');
        mensagem.className = 'notificacao-mensagem';
        mensagem.textContent = n.mensagem || '';
        conteudo.append(titulo, mensagem);
        item.append(icone, conteudo);
        item.addEventListener('click', function () {
            // A navegação continua mesmo se a requisição falhar.
            if (Number.isInteger(n.id)) {
                fetch('/notificacoes/' + n.id + '/ler', {
                    method: 'POST', credentials: 'same-origin', keepalive: true
                }).catch(function () {});
            }
        });
        list.appendChild(item);
    });
}

function carregarNotificacoes() {
    fetch('/api/notificacoes/nao-lidas')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            atualizarDropdown(data.notificacoes);
        });
}

/**
 * Mostra um toast notification
 */
function mostrarToast(mensagem, tipo) {
    const toast = document.createElement('div');
    toast.className = 'flash flash-' + tipo;
    toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;animation:slideIn 0.3s ease;';
    toast.innerHTML = '<i class="fas fa-' + (tipo === 'success' ? 'check-circle' : 'exclamation-circle') + '"></i><span>' + escapeHtml(mensagem) + '</span>';
    document.body.appendChild(toast);

    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(function() {
            toast.remove();
        }, 300);
    }, 4000);
}

/**
 * Escape HTML para prevenir XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Formata data para exibição
 */
function formatarData(dataStr) {
    if (!dataStr) return '-';
    const data = new Date(dataStr);
    if (isNaN(data.getTime())) return dataStr;
    return data.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Modais - Abrir/Fechar (funções globais)
 */
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/**
 * Toggle Setor Field (Admin Usuários)
 */
function toggleSetorField(prefix) {
    const perfilSelect = document.getElementById(prefix + '_perfil');
    const setorGroup = document.getElementById(prefix + '_setor_group');
    const setorSelect = document.getElementById(prefix + '_setor');

    if (perfilSelect && setorGroup && setorSelect) {
        const perfil = perfilSelect.value;
        if (perfil === 'setor') {
            setorGroup.style.display = 'block';
            setorSelect.required = true;
        } else {
            setorGroup.style.display = 'none';
            setorSelect.required = false;
            setorSelect.value = '';
        }
    }
}

/**
 * Abrir Editar Setor Modal
 */
function openEditSetorModal(id, nome, descricao, ativo) {
    const form = document.getElementById('formEditarSetor');
    if (form) {
        form.action = '/admin/setores/' + id + '/editar';
    }
    const nomeInput = document.getElementById('edit_nome_setor');
    const descInput = document.getElementById('edit_descricao_setor');
    const ativoInput = document.getElementById('edit_ativo_setor');

    if (nomeInput) nomeInput.value = nome;
    if (descInput) descInput.value = descricao;
    if (ativoInput) ativoInput.checked = ativo;

    openModal('modalEditarSetor');
}

/* ── Alertas flutuantes: somente notificações já autorizadas pelo servidor. ──
   O backend já filtra Notificacao por current_user.id. Não envia informações
   de chamados de outros usuários, nem consulta endpoints administrativos. */
(function () {
    'use strict';
    const userMeta = document.querySelector('meta[name="chamados-notification-user"]');
    if (!userMeta || !userMeta.content) return; // login/páginas públicas
    const storageKey = 'chamados_alertas_v1_usuario_' + userMeta.content;
    const endpoint = '/api/notificacoes/nao-lidas';
    let ativo = false;
    let baselinePronta = false;
    let vistos = new Set();

    try {
        const salvos = JSON.parse(localStorage.getItem(storageKey) || 'null');
        if (salvos && Array.isArray(salvos.ids)) {
            vistos = new Set(salvos.ids.map(String));
            baselinePronta = true;
        }
    } catch (_) { /* O modo privado pode bloquear o armazenamento. */ }

    function guardar() {
        try { localStorage.setItem(storageKey, JSON.stringify({ids: Array.from(vistos).slice(-120), time: Date.now()})); }
        catch (_) { /* não interfere na navegação */ }
    }
    function destinoSeguro(link) {
        if (typeof link !== 'string' || !link.startsWith('/') || link.startsWith('//') || link.startsWith('/\\')) return '/notificacoes';
        try { const url = new URL(link, location.origin); return url.origin === location.origin ? url.pathname + url.search + url.hash : '/notificacoes'; }
        catch (_) { return '/notificacoes'; }
    }
    function container() {
        let el = document.getElementById('chamados-alertas');
        if (!el) { el = document.createElement('div'); el.id = 'chamados-alertas'; el.setAttribute('aria-live', 'polite'); document.body.appendChild(el); }
        return el;
    }
    function alertaFlutuante(n) {
        const area = container();
        const card = document.createElement('div'); card.className = 'chamados-alerta';
        const conteudo = document.createElement('div'); conteudo.className = 'chamados-alerta-conteudo';
        conteudo.setAttribute('role', 'link'); conteudo.tabIndex = 0;
        const titulo = document.createElement('div'); titulo.className = 'chamados-alerta-titulo'; titulo.textContent = n.titulo || 'Nova atualização';
        const mensagem = document.createElement('div'); mensagem.className = 'chamados-alerta-texto'; mensagem.textContent = n.mensagem || 'Você recebeu uma nova notificação.';
        conteudo.append(titulo, mensagem);
        const fechar = document.createElement('button'); fechar.type = 'button'; fechar.className = 'chamados-alerta-fechar'; fechar.setAttribute('aria-label', 'Fechar aviso'); fechar.textContent = '×';
        fechar.addEventListener('click', () => card.remove());
        const abrir = () => { location.assign(destinoSeguro(n.link)); };
        conteudo.addEventListener('click', abrir);
        conteudo.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); abrir(); } });
        card.append(conteudo, fechar); area.prepend(card);
        while (area.childElementCount > 3) area.lastElementChild.remove();
        setTimeout(() => card.remove(), 9000);
    }
    async function alertaAndroid(n) {
        // Somente quando a pessoa JÁ autorizou notificações no navegador.
        // Não solicita permissão automaticamente nem altera a configuração existente.
        if (!('Notification' in window) || Notification.permission !== 'granted') return;
        if (!('serviceWorker' in navigator)) return;
        try {
            const reg = await navigator.serviceWorker.ready;
            await reg.showNotification(n.titulo || 'Sistema de Chamados', {
                body: n.mensagem || 'Nova atualização',
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-96x96.png',
                tag: 'chamados-notificacao-' + n.id,
                data: {url: destinoSeguro(n.link)}
            });
        } catch (err) { console.debug('Alerta do Android indisponível:', err); }
    }
    async function verificar() {
        if (ativo || document.visibilityState === 'hidden' || !navigator.onLine) return;
        ativo = true;
        try {
            const resp = await fetch(endpoint, {credentials:'same-origin', cache:'no-store', headers:{Accept:'application/json'}});
            if (!resp.ok || !(resp.headers.get('content-type') || '').includes('application/json')) return;
            const data = await resp.json();
            const registros = Array.isArray(data.notificacoes) ? data.notificacoes.filter(n => n && Number.isSafeInteger(Number(n.id))) : [];
            // Primeira leitura evita inundar a tela com notificações antigas não lidas.
            if (!baselinePronta) {
                for (const n of registros) vistos.add(String(n.id));
                baselinePronta = true; guardar(); return;
            }
            const novas = registros.filter(n => !vistos.has(String(n.id))).reverse();
            for (const n of novas) {
                vistos.add(String(n.id));
                alertaFlutuante(n);
                alertaAndroid(n);
            }
            if (novas.length) guardar();
            if (vistos.size > 120) { vistos = new Set(Array.from(vistos).slice(-120)); guardar(); }
        } catch (err) { console.debug('Consulta de novas notificações indisponível:', err); }
        finally { ativo = false; }
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', verificar, {once:true});
    else verificar();
    setInterval(verificar, 12000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) verificar(); });
    window.addEventListener('online', verificar);
})();


// Proteção contra páginas privadas antigas restauradas pelo botão Voltar.
// Uma página restaurada do histórico precisa ser revalidada no servidor,
// especialmente após trocar de usuário ou sair do sistema.
(function () {
    'use strict';
    window.addEventListener('pageshow', function (event) {
        // Login já possui seu próprio tratamento de histórico.
        if (document.querySelector('form.auth-form')) return;
        const nav = performance.getEntriesByType('navigation')[0];
        const peloHistorico = nav && nav.type === 'back_forward';
        if (event.persisted || peloHistorico) {
            // Recarrega a URL atual e deixa o servidor conferir a sessão.
            // No reload o tipo de navegação muda para "reload", sem loop.
            window.location.reload();
        }
    });
})();


/* Menu mobile do perfil Usuário: apenas reorganiza elementos já autorizados.
   Não cria itens de navegação nem altera permissões. */
(function () {
  function organizarMenuUsuario() {
    var menu = document.getElementById('mobileUserMenu');
    if (!menu || menu.dataset.layoutPadrao === '1') return;
    var header = menu.querySelector('.mobile-user-menu-header');
    var nav = menu.querySelector('.mobile-user-nav');
    var usuario = header && header.querySelector('.user-info-mobile');
    if (!header || !nav || !usuario) return;
    menu.dataset.layoutPadrao = '1';

    // Usa o logotipo original fornecido pelo usuário, não outra versão gerada.
    var logo = document.createElement('img');
    logo.className = 'mobile-menu-logo';
    logo.alt = 'Colégio Mauá - Santa Cruz do Sul';
    logo.src = '/static/icons/logo_maua.png';
    header.insertBefore(logo, header.firstChild);

    var footer = document.createElement('div');
    footer.className = 'mobile-menu-footer';
    footer.appendChild(usuario);
    var actions = document.createElement('div');
    actions.className = 'mobile-menu-actions';

    // Move os links originais de Perfil e Sair: preserva URLs e listeners.
    var perfil = nav.querySelector('.mobile-nav-item[href*="perfil"]');
    var sair = nav.querySelector('.mobile-nav-logout');
    [perfil, sair].forEach(function (link) {
      if (!link) return;
      var descricao = link.textContent.trim();
      link.title = descricao;
      link.setAttribute('aria-label', descricao);
      Array.from(link.childNodes).forEach(function (node) {
        if (node.nodeType === 3) node.remove();
      });
      actions.appendChild(link);
    });

    // Espelha o botão de instalação já existente, respeitando sua disponibilidade.
    var original = document.getElementById('btnInstalarApp');
    if (original) {
      var instalar = document.createElement('button');
      instalar.type = 'button';
      instalar.title = 'Instalar aplicativo';
      instalar.setAttribute('aria-label', 'Instalar aplicativo');
      instalar.innerHTML = '<i class="fas fa-download" aria-hidden="true"></i>';
      instalar.addEventListener('click', function () { original.click(); });
      actions.appendChild(instalar);
      function atualizarInstalar() {
        instalar.hidden = original.style.display === 'none' || getComputedStyle(original).display === 'none';
      }
      atualizarInstalar();
      new MutationObserver(atualizarInstalar).observe(original, { attributes: true, attributeFilter: ['style', 'class'] });
    }
    footer.appendChild(actions);
    menu.appendChild(footer);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', organizarMenuUsuario);
  } else organizarMenuUsuario();
})();
