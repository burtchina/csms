/**
 * 静态模态框管理器 - 轻量高效版 v2
 * 解决确认部署对话框频繁闪烁问题，全新优化方案
 * 通过DOM预处理和样式预加载，彻底消除闪烁
 */

(function() {
    // 直接在页面加载时执行
    const StaticModalManager = {
        // 模态框位置标准配置
        config: {
            // 模态框垂直位置（从顶部计算）
            topPosition: '30vh',
            // 模态框最大宽度
            maxWidth: '500px',
            // 模态框最小宽度
            minWidth: '300px',
            // 背景透明度
            backdropOpacity: '0.5',
            // 部署确认模态框ID
            deployConfirmId: 'deployConfirmModal',
        },
        
        // 已处理模态框缓存
        processedModals: new Set(),
        
        /**
         * 初始化管理器
         */
        init: function() {
            // 禁用所有Bootstrap模态框动画
            this.disableBootstrapModalAnimations();
            
            // 注入关键样式（预先加载，确保在模态框创建前样式已应用）
            this.injectCriticalStyles();
            
            // 覆盖Bootstrap模态框功能
            this.overrideBootstrapModal();
            
            // 提前处理页面上已存在的模态框
            this.preProcessExistingModals();
            
            // 设置关键事件监听
            this.setupMinimalListeners();
        },
        
        /**
         * 彻底禁用Bootstrap模态框动画
         */
        disableBootstrapModalAnimations: function() {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                try {
                    // 禁用过渡动画
                    bootstrap.Modal.Default.backdrop = 'static';
                    bootstrap.Modal.Default.keyboard = false;
                    bootstrap.Modal.Default.focus = false;
                } catch (e) {
                    console.error('[StaticModalManager] 无法禁用Bootstrap动画', e);
                }
            }
        },
        
        /**
         * 注入关键CSS样式（高优先级，确保覆盖其他样式）
         */
        injectCriticalStyles: function() {
            // 如果已经存在，先移除
            const existingStyle = document.getElementById('static-modal-critical-styles');
            if (existingStyle) existingStyle.remove();
            
            const style = document.createElement('style');
            style.id = 'static-modal-critical-styles';
            style.innerHTML = `
                /* 关键样式：禁用模态框动画，但保留交互功能 */
                .modal,
                .modal-dialog,
                .modal-content,
                .modal-backdrop,
                .fade,
                .modal.fade .modal-dialog,
                [class*="modal"],
                [class*="modal"] *,
                .fade * {
                    -webkit-transition: none !important;
                    -moz-transition: none !important;
                    -o-transition: none !important;
                    transition: none !important;
                    animation: none !important;
                    animation-duration: 0s !important;
                }
                
                /* 确保背景显示正确 */
                .modal-backdrop.show,
                .modal-backdrop.fade.show {
                    opacity: ${this.config.backdropOpacity} !important;
                    background: #000 !important;
                }
                
                /* 锁定确认部署模态框位置，但保留交互功能 */
                #${this.config.deployConfirmId}.show {
                    display: block !important;
                    visibility: visible !important;
                    pointer-events: auto !important; /* 确保可以点击 */
                }
                
                /* 锁定对话框位置，但保留交互功能 */
                #${this.config.deployConfirmId} .modal-dialog {
                    position: fixed !important;
                    top: ${this.config.topPosition} !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    margin: 0 !important;
                    width: auto !important;
                    max-width: ${this.config.maxWidth} !important;
                    min-width: ${this.config.minWidth} !important;
                    pointer-events: auto !important; /* 确保可以点击 */
                }
                
                /* 确保模态框内容和按钮可以点击 */
                #${this.config.deployConfirmId} .modal-content,
                #${this.config.deployConfirmId} .modal-body,
                #${this.config.deployConfirmId} .modal-footer,
                #${this.config.deployConfirmId} button {
                    pointer-events: auto !important;
                    cursor: pointer !important;
                }
                
                /* 确保模态框正确显示 */
                body.modal-open {
                    overflow: hidden;
                    padding-right: 0 !important;
                }
            `;
            
            // 确保样式立即应用
            document.head.appendChild(style);
        },
        
        /**
         * 预处理已存在的模态框（页面加载时）
         */
        preProcessExistingModals: function() {
            // 在DOM准备好后立即处理
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.processModalElements();
                });
            } else {
                this.processModalElements();
            }
        },
        
        /**
         * 处理页面上所有模态框元素
         */
        processModalElements: function() {
            // 特别处理确认部署模态框
            const deployModal = document.getElementById(this.config.deployConfirmId);
            if (deployModal) {
                // 标记为预处理过
                this.processedModals.add(deployModal.id);
            }
        },
        
        /**
         * 设置最小必要的事件监听
         */
        setupMinimalListeners: function() {
            // 处理模态框触发按钮
            const deployBtns = document.querySelectorAll(`[data-bs-target="#${this.config.deployConfirmId}"]`);
            deployBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    // 点击按钮后稍微延迟处理，确保Bootstrap模态框完全初始化
                    setTimeout(() => {
                        const modal = document.getElementById(this.config.deployConfirmId);
                        if (modal) {
                            this.makeModalClickable(modal);
                        }
                    }, 50);
                });
            });
            
            // 模态框显示事件
            document.addEventListener('shown.bs.modal', (event) => {
                if (event.target && event.target.id === this.config.deployConfirmId) {
                    this.makeModalClickable(event.target);
                }
            });
        },
        
        /**
         * 确保模态框可点击
         */
        makeModalClickable: function(modal) {
            if (!modal) return;
            
            // 1. 确保模态框显示
            modal.classList.add('show');
            modal.style.display = 'block';
            
            // 2. 确保模态框可点击
            modal.style.pointerEvents = 'auto';
            
            // 3. 确保对话框可点击
            const dialog = modal.querySelector('.modal-dialog');
            if (dialog) {
                dialog.style.pointerEvents = 'auto';
            }
            
            // 4. 确保内容可点击
            const content = modal.querySelector('.modal-content');
            if (content) {
                content.style.pointerEvents = 'auto';
            }
            
            // 5. 特别处理按钮
            const buttons = modal.querySelectorAll('button');
            buttons.forEach(button => {
                button.style.pointerEvents = 'auto';
                button.style.cursor = 'pointer';
            });
            
            // 6. 确保背景正确显示
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.classList.add('show');
                backdrop.style.opacity = this.config.backdropOpacity;
            }
            
            // 7. 确保body状态正确
            document.body.classList.add('modal-open');
        },
        
        /**
         * 覆盖Bootstrap模态框方法
         */
        overrideBootstrapModal: function() {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                try {
                    // 保存原始方法
                    const originalShow = bootstrap.Modal.prototype.show;
                    const originalHide = bootstrap.Modal.prototype.hide;
                    const manager = this;
                    
                    // 重写显示方法
                    bootstrap.Modal.prototype.show = function() {
                        const modalElement = this._element;
                        
                        // 特殊处理部署确认模态框
                        if (modalElement && modalElement.id === manager.config.deployConfirmId) {
                            // 立即修复位置，避免任何计算导致的闪烁
                            manager.fixModalImmediately(modalElement);
                        }
                        
                        // 对所有模态框应用基本样式
                        if (modalElement) {
                            modalElement.style.display = 'block';
                            modalElement.classList.add('show');
                        }
                        
                        // 调用原始方法
                        originalShow.apply(this, arguments);
                        
                        // 再次确保样式正确
                        if (modalElement && modalElement.id === manager.config.deployConfirmId) {
                            // 用RAF确保在下一帧再次修复，双保险
                            requestAnimationFrame(() => {
                                manager.fixModalImmediately(modalElement);
                            });
                        }
                    };
                    
                    // 重写隐藏方法，确保干净清理
                    bootstrap.Modal.prototype.hide = function() {
                        const modalElement = this._element;
                        
                        // 立即隐藏，避免任何过渡
                        if (modalElement) {
                            modalElement.style.display = 'none';
                        }
                        
                        // 调用原始方法
                        originalHide.apply(this, arguments);
                    };
                } catch (e) {
                    console.error('[StaticModalManager] 无法覆盖Bootstrap Modal', e);
                }
            }
        },
        
        /**
         * 检查模态框是否可见
         */
        isModalVisible: function(modal) {
            return modal && (
                modal.classList.contains('show') ||
                window.getComputedStyle(modal).display !== 'none'
            );
        },
        
        /**
         * 预修复模态框位置（DOM创建时）
         */
        preFixModalPosition: function(modal) {
            if (!modal) return;
            
            // 标记为已处理
            modal.setAttribute('data-static-modal', 'true');
            
            // 确保对话框元素也有正确标记
            const dialog = modal.querySelector('.modal-dialog');
            if (dialog) {
                dialog.setAttribute('data-static-dialog', 'true');
            }
        },
        
        /**
         * 立即修复模态框位置（显示前/显示时）
         * 使用直接样式注入而非样式表，确保最高优先级
         */
        fixModalImmediately: function(modal) {
            if (!modal || modal.id !== this.config.deployConfirmId) return;
            
            // 立即应用内联样式（最高优先级）
            modal.style.cssText = `
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                z-index: 1050 !important;
                display: block !important;
                margin: 0 !important;
                padding: 0 !important;
                outline: 0 !important;
                overflow-x: hidden !important;
                overflow-y: auto !important;
                transition: none !important;
                transform: none !important;
                animation: none !important;
            `;
            
            // 固定对话框位置
            const dialog = modal.querySelector('.modal-dialog');
            if (dialog) {
                dialog.style.cssText = `
                    position: fixed !important;
                    top: ${this.config.topPosition} !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    margin: 0 !important;
                    width: auto !important;
                    max-width: ${this.config.maxWidth} !important;
                    min-width: ${this.config.minWidth} !important;
                    z-index: 1051 !important;
                    outline: 0 !important;
                    transition: none !important;
                    animation: none !important;
                `;
            }
            
            // 确保内容无动画
            const content = modal.querySelector('.modal-content');
            if (content) {
                content.style.cssText = `
                    transition: none !important;
                    animation: none !important;
                    transform: none !important;
                    box-shadow: 0 5px 15px rgba(0,0,0,.5) !important;
                `;
            }
            
            // 立即添加显示类
            modal.classList.add('show');
        },
        
        /**
         * 公共API：修复确认部署模态框
         * 可从外部调用
         */
        fixDeployConfirmModal: function(modal) {
            // 获取模态框元素
            const deployModal = modal || document.getElementById(this.config.deployConfirmId);
            if (!deployModal) {
                console.error('[ModalManager] 无法找到部署确认模态框');
                return;
            }
            
            console.log('[ModalManager] 正在修复部署确认模态框:', deployModal.id);
            
            // 确保模态框显示
            deployModal.classList.add('show');
            deployModal.style.display = 'block';
            
            // 增强z-index确保模态框在最顶层
            deployModal.style.zIndex = '2000';
            
            // 确保鼠标事件能够传递
            deployModal.style.pointerEvents = 'auto';
            
            // 特别强化处理模态框内部元素
            const elements = deployModal.querySelectorAll('.modal-dialog, .modal-content, .modal-header, .modal-body, .modal-footer, button');
            elements.forEach(el => {
                // 确保元素可点击和可见
                el.style.pointerEvents = 'auto';
                el.style.visibility = 'visible';
                el.style.opacity = '1';
                
                // 对所有按钮特殊处理
                if (el.tagName === 'BUTTON') {
                    el.style.cursor = 'pointer';
                    el.style.zIndex = '2010'; // 确保按钮在最上层
                    
                    // 清除可能干扰点击的属性
                    el.disabled = false;
                    
                    // 为按钮添加高亮效果，确保用户知道它们是可交互的
                    el.addEventListener('mouseover', function() {
                        this.style.opacity = '0.9';
                    });
                    el.addEventListener('mouseout', function() {
                        this.style.opacity = '1';
                    });
                }
                
                // 对对话框特殊处理
                if (el.classList.contains('modal-dialog')) {
                    el.style.position = 'relative';
                    el.style.margin = '10vh auto';
                    el.style.zIndex = '2005';
                    el.style.transform = 'none';
                }
            });
            
            // 确保背景不会阻挡点击
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.style.pointerEvents = 'none';
            } else {
                // 如果没有背景，创建一个不会阻挡点击的背景
                const newBackdrop = document.createElement('div');
                newBackdrop.className = 'modal-backdrop fade show';
                newBackdrop.style.opacity = '0.5';
                newBackdrop.style.pointerEvents = 'none';
                newBackdrop.style.zIndex = '1999';
                document.body.appendChild(newBackdrop);
            }
            
            // 检查并修复按钮的事件监听器
            const confirmBtn = deployModal.querySelector('#confirmDeployBtn');
            const cancelBtn = deployModal.querySelector('#cancelDeployBtn');
            
            if (confirmBtn) {
                // 确保确认按钮有事件监听器并且可见可点击
                console.log('[ModalManager] 确认部署按钮:', confirmBtn);
                confirmBtn.style.display = 'inline-block';
                confirmBtn.style.opacity = '1';
                confirmBtn.style.pointerEvents = 'auto';
                confirmBtn.style.cursor = 'pointer';
                confirmBtn.disabled = false;
            }
            
            if (cancelBtn) {
                // 确保取消按钮有事件监听器并且可见可点击
                console.log('[ModalManager] 取消部署按钮:', cancelBtn);
                cancelBtn.style.display = 'inline-block';
                cancelBtn.style.opacity = '1';
                cancelBtn.style.pointerEvents = 'auto';
                cancelBtn.style.cursor = 'pointer';
                cancelBtn.disabled = false;
            }
            
            console.log('[ModalManager] 部署确认模态框修复完成');
        },
        
        /**
         * 显示自定义确认对话框
         */
        showConfirm: function(options) {
            // 默认选项
            const defaults = {
                title: '确认',
                message: '确定要执行此操作吗？',
                onConfirm: function() {},
                onCancel: function() {},
                confirmText: '确认',
                cancelText: '取消'
            };
            
            // 合并选项
            const settings = Object.assign({}, defaults, options);
            
            // 创建唯一ID
            const modalId = 'static-modal-' + Date.now();
            
            // 创建HTML - 确保元素可点击
            const modalHtml = `
                <div class="modal fade show" id="${modalId}" tabindex="-1" role="dialog" aria-hidden="true" style="
                    display: block;
                    position: fixed; 
                    top: 0; 
                    left: 0; 
                    right: 0; 
                    bottom: 0; 
                    z-index: 1050; 
                    pointer-events: auto;">
                    <div class="modal-dialog" role="document" style="
                        position: fixed; 
                        top: ${this.config.topPosition}; 
                        left: 50%; 
                        transform: translateX(-50%); 
                        margin: 0; 
                        max-width: ${this.config.maxWidth}; 
                        min-width: ${this.config.minWidth}; 
                        z-index: 1051; 
                        pointer-events: auto;">
                        <div class="modal-content" style="pointer-events: auto;">
                            <div class="modal-header">
                                <h5 class="modal-title">${settings.title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭" style="cursor: pointer; pointer-events: auto;"></button>
                            </div>
                            <div class="modal-body">
                                <p>${settings.message}</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary cancel-btn" style="cursor: pointer; pointer-events: auto;">${settings.cancelText}</button>
                                <button type="button" class="btn btn-primary confirm-btn" style="cursor: pointer; pointer-events: auto;">${settings.confirmText}</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-backdrop fade show" style="opacity: ${this.config.backdropOpacity};"></div>
            `;
            
            // 添加到文档
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // 获取DOM元素
            const modalEl = document.getElementById(modalId);
            const backdropEl = document.querySelector('.modal-backdrop:last-child');
            
            // 锁定body滚动
            document.body.classList.add('modal-open');
            document.body.style.overflow = 'hidden';
            
            // 绑定事件
            const closeModal = () => {
                if (modalEl) {
                    modalEl.style.display = 'none';
                    modalEl.classList.remove('show');
                }
                
                if (backdropEl) {
                    backdropEl.style.display = 'none';
                    backdropEl.classList.remove('show');
                }
                
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                
                // 延迟移除DOM元素
                setTimeout(() => {
                    if (modalEl) modalEl.remove();
                    if (backdropEl) backdropEl.remove();
                }, 100);
            };
            
            // 确认按钮
            const confirmBtn = modalEl.querySelector('.confirm-btn');
            if (confirmBtn) {
                confirmBtn.onclick = function() {
                    settings.onConfirm();
                    closeModal();
                };
            }
            
            // 取消按钮和关闭按钮
            const cancelBtn = modalEl.querySelector('.cancel-btn');
            const closeBtn = modalEl.querySelector('.btn-close');
            
            if (cancelBtn) {
                cancelBtn.onclick = function() {
                    settings.onCancel();
                    closeModal();
                };
            }
            
            if (closeBtn) {
                closeBtn.onclick = closeModal;
            }
            
            // ESC键关闭
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    settings.onCancel();
                    closeModal();
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
            
            return {
                close: closeModal
            };
        }
    };
    
    // 暴露为全局变量
    window.ModalManager = StaticModalManager;
    window.StaticModalManager = StaticModalManager;
    
    // 立即初始化
    StaticModalManager.init();
})(); 