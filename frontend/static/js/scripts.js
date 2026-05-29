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
    setInterval(atualizarContadorNotificacoes, 30000); // Atualizar a cada 30s

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
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.dataset.noLoading) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
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

    list.innerHTML = notificacoes.map(function(n) {
        return '<div class="notificacao-item notificacao-nao-lida">' +
            '<div class="notificacao-icon"><i class="fas fa-bell"></i></div>' +
            '<div class="notificacao-conteudo">' +
            '<h4 class="notificacao-titulo">' + escapeHtml(n.titulo) + '</h4>' +
            '<p class="notificacao-mensagem">' + escapeHtml(n.mensagem) + '</p>' +
            '</div></div>';
    }).join('');
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