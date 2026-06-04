/* ═══════════════════════════════════════════════════════════════
   PWA - Sistema de Chamados Colégio Mauá
   Registro do Service Worker, atualizações e utilidades offline
   ═══════════════════════════════════════════════════════════════ */

(function() {
    'use strict';

    const PWA = {
        sw: null,
        isOnline: navigator.onLine,
        updateAvailable: false,
        deferredPrompt: null,

        // Inicializar PWA
        init() {
            this.registerServiceWorker();
            this.setupNetworkListeners();
            this.setupInstallPrompt();
            this.setupUpdateUI();
            this.setupPeriodicSync();
        },

        // ═══════════════════════════════════════════════════════════════
        // REGISTRO DO SERVICE WORKER
        // ═══════════════════════════════════════════════════════════════
        async registerServiceWorker() {
            if (!('serviceWorker' in navigator)) {
                console.log('[PWA] Service Worker não suportado');
                return;
            }

            try {
               const registration = await navigator.serviceWorker.register('/static/sw.js', {
                    scope: '/'
                });

                console.log('[PWA] SW registrado:', registration.scope);
                this.sw = registration;

                // Monitorar atualizações
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    if (!newWorker) return;

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // Nova versão disponível
                            this.showUpdateNotification();
                        }
                    });
                });

                // Verificar se há atualização ao carregar
                await registration.update();

            } catch (error) {
                console.error('[PWA] Falha ao registrar SW:', error);
            }
        },

        // ═══════════════════════════════════════════════════════════════
        // NOTIFICAÇÃO DE ATUALIZAÇÃO
        // ═══════════════════════════════════════════════════════════════
        showUpdateNotification() {
            if (this.updateAvailable) return;
            this.updateAvailable = true;

            // Criar toast de atualização
            const toast = document.createElement('div');
            toast.className = 'pwa-update-toast';
            toast.innerHTML = `
                <div class="pwa-update-content">
                    <i class="fas fa-sync-alt"></i>
                    <span>Nova versão disponível!</span>
                </div>
                <div class="pwa-update-actions">
                    <button class="pwa-btn-update" onclick="PWA.applyUpdate()">
                        <i class="fas fa-download"></i> Atualizar
                    </button>
                    <button class="pwa-btn-dismiss" onclick="PWA.dismissUpdate()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            document.body.appendChild(toast);

            // Auto-dismiss após 30 segundos
            setTimeout(() => this.dismissUpdate(), 30000);
        },

        applyUpdate() {
            if (!this.sw) return;

            // Enviar mensagem para o SW skipWaiting
            this.sw.waiting?.postMessage({ type: 'SKIP_WAITING' });

            // Recarregar quando o novo SW assumir controle
            navigator.serviceWorker.addEventListener('controllerchange', () => {
                window.location.reload();
            });
        },

        dismissUpdate() {
            const toast = document.querySelector('.pwa-update-toast');
            if (toast) {
                toast.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => toast.remove(), 300);
            }
            this.updateAvailable = false;
        },

        // ═══════════════════════════════════════════════════════════════
        // LISTENERS DE REDE
        // ═══════════════════════════════════════════════════════════════
        setupNetworkListeners() {
            window.addEventListener('online', () => {
                this.isOnline = true;
                this.showNetworkStatus('online');
                this.syncData();
            });

            window.addEventListener('offline', () => {
                this.isOnline = false;
                this.showNetworkStatus('offline');
            });
        },

        showNetworkStatus(status) {
            // Remover toast anterior se existir
            const existing = document.querySelector('.pwa-network-toast');
            if (existing) existing.remove();

            const toast = document.createElement('div');
            toast.className = `pwa-network-toast ${status}`;
            toast.innerHTML = status === 'online'
                ? '<i class="fas fa-wifi"></i> Conexão restaurada'
                : '<i class="fas fa-wifi-slash"></i> Sem conexão - Modo offline';

            document.body.appendChild(toast);

            // Auto-dismiss
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, status === 'online' ? 3000 : 5000);
        },

        // ═══════════════════════════════════════════════════════════════
        // PROMPT DE INSTALAÇÃO
        // ═══════════════════════════════════════════════════════════════
        setupInstallPrompt() {
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                this.deferredPrompt = e;
                this.showInstallButton();
            });

            // Se já estiver instalado, esconder botão
            window.addEventListener('appinstalled', () => {
                this.deferredPrompt = null;
                this.hideInstallButton();
                console.log('[PWA] App instalado!');
            });
        },

        showInstallButton() {
            // Verificar se já mostramos o prompt recentemente
            const lastPrompt = localStorage.getItem('pwa_install_dismissed');
            if (lastPrompt && Date.now() - parseInt(lastPrompt) < 7 * 24 * 60 * 60 * 1000) {
                return; // Não incomodar por 7 dias
            }

            const btn = document.createElement('button');
            btn.className = 'pwa-install-btn';
            btn.innerHTML = '<i class="fas fa-download"></i> Instalar App';
            btn.onclick = () => this.promptInstall();
            document.body.appendChild(btn);
        },

        hideInstallButton() {
            const btn = document.querySelector('.pwa-install-btn');
            if (btn) btn.remove();
        },

        async promptInstall() {
            if (!this.deferredPrompt) return;

            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;

            if (outcome === 'dismissed') {
                localStorage.setItem('pwa_install_dismissed', Date.now().toString());
            }

            this.deferredPrompt = null;
            this.hideInstallButton();
        },

        // ═══════════════════════════════════════════════════════════════
        // SINCRONIZAÇÃO DE DADOS
        // ═══════════════════════════════════════════════════════════════
        async syncData() {
            if (!('sync' in this.sw)) {
                console.log('[PWA] Background Sync não suportado');
                return;
            }

            try {
                await this.sw.sync.register('sync-outbox');
                console.log('[PWA] Sync registrado');
            } catch (err) {
                console.warn('[PWA] Falha ao registrar sync:', err);
            }
        },

        // ═══════════════════════════════════════════════════════════════
        // PERIODIC BACKGROUND SYNC
        // ═══════════════════════════════════════════════════════════════
        async setupPeriodicSync() {
            if (!('periodicSync' in this.sw)) {
                console.log('[PWA] Periodic Sync não suportado');
                return;
            }

            try {
                const status = await navigator.permissions.query({
                    name: 'periodic-background-sync'
                });

                if (status.state === 'granted') {
                    await this.sw.periodicSync.register('check-notifications', {
                        minInterval: 15 * 60 * 1000 // 15 minutos
                    });
                    console.log('[PWA] Periodic sync registrado');
                }
            } catch (err) {
                console.warn('[PWA] Falha no periodic sync:', err);
            }
        },

        // ═══════════════════════════════════════════════════════════════
        // UTILIDADES
        // ═══════════════════════════════════════════════════════════════
        async getSWVersion() {
            if (!this.sw) return null;

            return new Promise((resolve) => {
                const channel = new MessageChannel();
                channel.port1.onmessage = (e) => resolve(e.data?.version);
                this.sw.active?.postMessage({ type: 'GET_VERSION' }, [channel.port2]);
            });
        },

        async clearCaches() {
            if (!this.sw) return;

            return new Promise((resolve) => {
                const channel = new MessageChannel();
                channel.port1.onmessage = (e) => resolve(e.data?.cleared);
                this.sw.active?.postMessage({ type: 'CLEAR_CACHES' }, [channel.port2]);
            });
        },

        // Verificar se está rodando como PWA instalado
        isStandalone() {
            return window.matchMedia('(display-mode: standalone)').matches ||
                   window.navigator.standalone === true;
        }
    };

    // Expor globalmente
    window.PWA = PWA;

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => PWA.init());
    } else {
        PWA.init();
    }
})();
