/* ═══════════════════════════════════════════════════════════════
   PWA - Sistema de Chamados Colégio Mauá
   - Registro do Service Worker
   - Banner de instalação no TOPO (não sobrepoem o chat flutuante)
   - Toast de nova versão disponível
   - Indicador online/offline
   ═══════════════════════════════════════════════════════════════ */

(function() {
    'use strict';

    /* ── Injeta os estilos do banner/toasts (não precisa editar CSS) ── */
    const css = document.createElement('style');
    css.textContent = `
        /* ═══ CONVITE FLUTUANTE DE INSTALAÇÃO ═══ */
        .pwa-install-banner {
            position: fixed;
            top: calc(12px + env(safe-area-inset-top, 0px));
            left: 50%;
            right: auto;
            bottom: auto;
            transform: translateX(-50%);
            z-index: 5000;
            display: flex;
            align-items: center;
            gap: 12px;
            width: max-content;
            max-width: calc(100vw - 32px);
            padding: 10px 14px;
            background: #ffffff;
            border: 1px solid #e9ecef;
            border-left: 4px solid #f46c6c;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.18);
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            color: #2c3e50;
            animation: pwaBannerDown .35s ease;
        }
        @keyframes pwaBannerDown {
            from { opacity: 0; transform: translate(-50%, -20px); }
            to   { opacity: 1; transform: translate(-50%, 0); }
        }
        .pwa-install-banner.saindo {
            opacity: 0;
            transition: opacity .2s ease;
        }
        @keyframes pwaBannerUp {
            from { opacity: 1; transform: translate(-50%, 0); }
            to   { opacity: 0; transform: translate(-50%, -20px); }
        }
        .pwa-install-banner .pwa-banner-icone {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            background: rgba(244,108,108,0.12);
            color: #f46c6c;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            flex-shrink: 0;
        }
        .pwa-install-banner .pwa-banner-texto {
            flex: 1;
            min-width: 0;
            line-height: 1.3;
        }
        .pwa-install-banner .pwa-banner-texto strong {
            display: block;
            font-size: 0.9rem;
        }
        .pwa-install-banner .pwa-banner-texto span {
            font-size: 0.78rem;
            color: #7f8c8d;
        }
        .pwa-install-banner button {
            border: none;
            cursor: pointer;
            font-family: inherit;
            border-radius: 8px;
            font-weight: 600;
        }
        .pwa-install-banner .pwa-banner-instalar {
            background: #f46c6c;
            color: #fff;
            padding: 8px 14px;
            font-size: 0.85rem;
            white-space: nowrap;
            transition: background 0.2s;
        }
        .pwa-install-banner .pwa-banner-instalar:hover {
            background: #e05555;
        }
        .pwa-install-banner .pwa-banner-fechar {
            background: transparent;
            color: #95a5a6;
            width: 30px;
            height: 30px;
            font-size: 1rem;
            flex-shrink: 0;
        }
        /* iPhone/iPad: instruções claras no próprio banner, sem janela de alerta */
        .pwa-install-banner.pwa-banner-ios {
            width: min(350px, calc(100vw - 24px));
            gap: 10px;
            padding: 12px;
            align-items: flex-start;
        }
        .pwa-install-banner.pwa-banner-ios .pwa-banner-texto span {
            display: block;
            margin-top: 4px;
            line-height: 1.45;
            color: #526170;
        }
        .pwa-install-banner.pwa-banner-ios .pwa-banner-fechar {
            margin-top: -3px;
        }
        .pwa-install-banner .pwa-banner-fechar:hover {
            background: #f5f6fa;
            color: #2c3e50;
        }

        /* ═══ TOAST DE ATUALIZAÇÃO (TOPO) ═══ */
        .pwa-update-toast {
            position: fixed;
            top: 12px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 5001;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 14px;
            background: #2c3e50;
            color: #fff;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.25);
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            animation: pwaBannerDown 0.35s ease;
        }
        .pwa-update-toast .pwa-btn-update {
            background: #f46c6c;
            color: #fff;
            border: none;
            padding: 6px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.8rem;
        }
        .pwa-update-toast .pwa-btn-dismiss {
            background: transparent;
            border: none;
            color: rgba(255,255,255,0.6);
            cursor: pointer;
            font-size: 1rem;
        }

        /* ═══ TOAST DE REDE ═══ */
        .pwa-network-toast {
            position: fixed;
            top: 12px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 5002;
            padding: 8px 16px;
            border-radius: 20px;
            font-family: 'Inter', sans-serif;
            font-size: 0.82rem;
            font-weight: 500;
            transition: opacity 0.3s;
        }
        .pwa-network-toast.online  { background: #d4edda; color: #155724; }
        .pwa-network-toast.offline { background: #f8d7da; color: #721c24; }
    `;
    document.head.appendChild(css);

    const PWA = {
        sw: null,
        isOnline: navigator.onLine,
        updateAvailable: false,
        deferredPrompt: null,

        init() {
            this.registerServiceWorker();
            this.setupNetworkListeners();
            this.setupInstallPrompt();
        },

        /* ═══════════════════════════════════════════════════════
           REGISTRO DO SERVICE WORKER
           ═══════════════════════════════════════════════════════ */
        async registerServiceWorker() {
            if (!('serviceWorker' in navigator)) {
                console.log('[PWA] Service Worker não suportado');
                return;
            }

            try {
                const registration = await navigator.serviceWorker.register('/sw.js', {
                    scope: '/'
                });

                console.log('[PWA] SW registrado:', registration.scope);
                this.sw = registration;

                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    if (!newWorker) return;

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });

                await registration.update();

            } catch (error) {
                console.error('[PWA] Falha ao registrar SW:', error);
            }
        },

        /* ═══════════════════════════════════════════════════════
           TOAST DE ATUALIZAÇÃO
           ═══════════════════════════════════════════════════════ */
        showUpdateNotification() {
            if (this.updateAvailable) return;
            this.updateAvailable = true;

            const toast = document.createElement('div');
            toast.className = 'pwa-update-toast';
            toast.innerHTML = `
                <i class="fas fa-sync-alt"></i>
                <span>Nova versão disponível!</span>
                <button class="pwa-btn-update" id="pwaBtnAtualizar">Atualizar</button>
                <button class="pwa-btn-dismiss" id="pwaBtnDispensar">&times;</button>
            `;
            document.body.appendChild(toast);

            document.getElementById('pwaBtnAtualizar').onclick = () => this.applyUpdate();
            document.getElementById('pwaBtnDispensar').onclick = () => this.dismissUpdate();

            setTimeout(() => this.dismissUpdate(), 30000);
        },

        applyUpdate() {
            if (!this.sw) return;

            this.sw.waiting?.postMessage({ type: 'SKIP_WAITING' });

            navigator.serviceWorker.addEventListener('controllerchange', () => {
                window.location.reload();
            });
        },

        dismissUpdate() {
            const toast = document.querySelector('.pwa-update-toast');
            if (toast) toast.remove();
            this.updateAvailable = false;
        },

        /* ═══════════════════════════════════════════════════════
           LISTENERS DE REDE
           ═══════════════════════════════════════════════════════ */
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
            const existing = document.querySelector('.pwa-network-toast');
            if (existing) existing.remove();

            const toast = document.createElement('div');
            toast.className = `pwa-network-toast ${status}`;
            toast.innerHTML = status === 'online'
                ? '<i class="fas fa-wifi"></i> Conexão restaurada'
                : '<i class="fas fa-wifi-slash"></i> Sem conexão — Modo offline';

            document.body.appendChild(toast);

            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, status === 'online' ? 3000 : 5000);
        },

        /* ═══════════════════════════════════════════════════════
           BANNER DE INSTALAÇÃO NO TOPO
           (não cria botão flutuante → não sobrepoem o chat)
           ═══════════════════════════════════════════════════════ */
        setupInstallPrompt() {
            // Já instalado? Não mostra nada.
            if (this.isStandalone()) return;

            // O convite não fica bloqueado por uma recusa antiga.
            // A instalação continua dependendo de oferta do navegador.

            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                this.deferredPrompt = e;
                if (!this.isStandalone()) this.showInstallBanner();
            });

            window.addEventListener('appinstalled', () => {
                this.deferredPrompt = null;
                this.hideInstallBanner();
                const btn = document.getElementById('btnInstalarApp');
                if (btn) btn.style.display = 'none';
                console.log('[PWA] App instalado!');
            });

            // iOS/Safari não dispara beforeinstallprompt → mostra banner com instruções
            setTimeout(() => {
                if (this.isIos() && !this.isStandalone() && !this.deferredPrompt
                    && !document.querySelector('.pwa-install-banner')) {
                    this.showInstallBanner(true);
                }
            }, 2000);
        },

        showInstallBanner(isIos) {
            if (this.isStandalone() || document.querySelector('.pwa-install-banner')) return;

            const banner = document.createElement('div');
            banner.className = 'pwa-install-banner' + (isIos ? ' pwa-banner-ios' : '');
            banner.setAttribute('role', 'status');
            banner.innerHTML = `
                <div class="pwa-banner-icone"><i class="fas fa-${isIos ? 'mobile-alt' : 'download'}" aria-hidden="true"></i></div>
                <div class="pwa-banner-texto">
                    <strong>${isIos ? 'Adicionar à Tela de Início' : 'Instalar o aplicativo'}</strong>
                    <span>${isIos
                        ? 'Toque em Compartilhar (quadrado com seta para cima), escolha "Adicionar à Tela de Início" e depois "Adicionar".'
                        : 'Acesse o sistema direto da sua tela inicial'}</span>
                </div>
                ${isIos ? '' : '<button type="button" class="pwa-banner-instalar" id="pwaBannerInstalar">Instalar</button>'}
                <button type="button" class="pwa-banner-fechar" id="pwaBannerFechar" aria-label="Fechar aviso">&times;</button>
            `;
            document.body.appendChild(banner);

            if (!isIos) {
                document.getElementById('pwaBannerInstalar').onclick = () => this.promptInstall();
            }
            document.getElementById('pwaBannerFechar').onclick = () => this.hideInstallBanner();
            // O banner continua visível até o usuário fechar ou instalar o app.
        },

        hideInstallBanner() {
            const banner = document.querySelector('.pwa-install-banner');
            if (banner) {
                banner.classList.add('saindo');
                setTimeout(() => banner.remove(), 300);
            }
        },

        async promptInstall() {
            // iOS não oferece prompt nativo. Nunca abrir alert() ou modal no iPhone.
            if (this.isIos()) {
                this.showInstallBanner(true);
                return;
            }
            if (!this.deferredPrompt) {
                // Em navegadores sem beforeinstallprompt, não abrir aviso intrusivo.
                return;
            }

            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;

            if (outcome === 'accepted') {
                this.hideInstallBanner();
            } else {
                this.hideInstallBanner();
            }

            this.deferredPrompt = null;
        },

        isIos() {
            return /iphone|ipad|ipod/i.test(navigator.userAgent);
        },

        isStandalone() {
            return window.matchMedia('(display-mode: standalone)').matches ||
                   window.matchMedia('(display-mode: fullscreen)').matches ||
                   window.navigator.standalone === true;
        },

        /* ═══════════════════════════════════════════════════════
           BACKGROUND SYNC (quando voltar online)
           ═══════════════════════════════════════════════════════ */
        async syncData() {
            if (!this.sw || !('sync' in this.sw)) return;

            try {
                await this.sw.sync.register('sync-outbox');
            } catch (err) {
                console.warn('[PWA] Falha ao registrar sync:', err);
            }
        }
    };

    window.PWA = PWA;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => PWA.init());
    } else {
        PWA.init();
    }
})();