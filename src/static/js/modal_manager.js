/**
 * 模态框管理器 - 增强版（解决闪烁问题特别优化版）
 * 
 * 用于统一管理所有Bootstrap模态框的位置和行为，解决模态框位置频繁变动导致的闪烁问题。
 * 通过插入自定义CSS样式和直接DOM操作相结合的方式，确保模态框位置绝对稳定。
 */

// 立即执行函数，防止变量污染全局作用域
(function() {
    // 模态框管理器
    const ModalManager = {
        /**
         * 初始化模态框管理器
         */
        init: function() {
            // 添加全局CSS样式
            this.injectGlobalCSS();
            
            // 覆盖Bootstrap的模态框默认行为
            this.overrideBootstrapModal();
            
            // 在DOM加载完成后绑定事件
            document.addEventListener('DOMContentLoaded', function() {
                // 立即修复所有已存在的模态框
                ModalManager.fixAllModals();
                
                // 设置事件监听
                ModalManager.setupEventListeners();
            });
            
            console.info("模态框管理器(强化版)已初始化 - 闪烁修复专用版");
        },
        
        /**
         * 注入全局CSS样式
         */
        injectGlobalCSS: function() {
            const styleElement = document.createElement('style');
            styleElement.id = 'modal-manager-styles';
            styleElement.textContent = `
                /* 禁用所有模态框的过渡动画和变换 */
                .modal, 
                .modal.fade,
                .modal.fade.show,
                .modal-dialog,
                .modal-backdrop,
                .modal-content,
                .modal *, 
                #deployConfirmModal,
                #deployConfirmModal * {
                    animation: none !important;
                    transition: none !important;
                    transform: none !important;
                }
                
                /* 特别处理确认部署对话框 */
                #deployConfirmModal,
                div[id^="confirmModal"],
                div[id^="deployConfirmModal"] {
                    padding: 0 !important;
                }
                
                /* 固定模态框位置的核心样式 - 高优先级 */
                .modal-dialog,
                .modal-dialog[data-position-fixed="true"],
                .modal-dialog[data-position-fixed-done="true"],
                #deployConfirmModal .modal-dialog,
                div[id^="confirmModal"] .modal-dialog,
                div[id^="deployConfirmModal"] .modal-dialog,
                .modal.show .modal-dialog {
                    position: fixed !important;
                    top: 30% !important;
                    left: 50% !important;
                    margin: 0 !important;
                    transform: translateX(-50%) !important;
                    width: auto !important;
                    max-width: 500px !important;
                    min-width: 300px !important;
                }
                
                /* 移除Bootstrap的默认模态框动画 */
                .modal.fade .modal-dialog {
                    transition: none !important;
                    transform: translateX(-50%) !important;
                }
                
                /* 禁用背景淡入淡出 */
                .modal-backdrop,
                .modal-backdrop.fade,
                .modal-backdrop.fade.show {
                    transition: none !important;
                }
                
                /* 移除内容过渡 */
                .modal-content {
                    transition: none !important;
                }
                
                /* 确保模态框在显示时立即可见 */
                .modal.show {
                    display: block !important;
                    opacity: 1 !important;
                }
            `;
            
            // 尝试移除旧样式（如果存在）
            const oldStyle = document.getElementById('modal-manager-styles');
            if (oldStyle) {
                oldStyle.remove();
            }
            
            // 添加新样式到头部
            document.head.appendChild(styleElement);
        },
        
        /**
         * 覆盖Bootstrap的模态框默认行为
         */
        overrideBootstrapModal: function() {
            // 如果Bootstrap已加载，尝试覆盖其模态框行为
            if (window.bootstrap && window.bootstrap.Modal) {
                const originalShow = window.bootstrap.Modal.prototype.show;
                window.bootstrap.Modal.prototype.show = function() {
                    // 调用原始show方法
                    const result = originalShow.apply(this, arguments);
                    
                    // 立即修复模态框位置
                    const modalElement = this._element;
                    if (modalElement) {
                        // 使用RAF确保在下一帧应用，解决渲染时机问题
                        requestAnimationFrame(function() {
                            ModalManager.fixModalPosition(modalElement);
                        });
                    }
                    
                    return result;
                };
            }
        },
        
        /**
         * 设置事件监听器
         */
        setupEventListeners: function() {
            // 修复所有模态框 - 窗口大小改变时
            window.addEventListener('resize', ModalManager.fixAllModals);
            
            // 捕获阶段监听模态框打开事件 - 在Bootstrap处理之前
            document.addEventListener('show.bs.modal', function(event) {
                ModalManager.fixModalPosition(event.target);
                
                // 阻止事件冒泡，避免多次处理
                event.stopPropagation();
            }, true);
            
            // 模态框显示后再次修复位置
            document.addEventListener('shown.bs.modal', function(event) {
                ModalManager.fixModalPosition(event.target);
            });
            
            // 修复确认部署对话框的特殊处理
            const deployConfirmBtn = document.querySelector('[data-bs-target="#deployConfirmModal"]');
            if (deployConfirmBtn) {
                deployConfirmBtn.addEventListener('click', function() {
                    setTimeout(function() {
                        const modal = document.getElementById('deployConfirmModal');
                        if (modal) {
                            ModalManager.fixModalPosition(modal);
                        }
                    }, 0);
                });
            }
            
            // 使用MutationObserver监听DOM变化，处理动态添加的模态框
            if (window.MutationObserver) {
                const observer = new MutationObserver(function(mutations) {
                    let needsFixing = false;
                    
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'childList') {
                            mutation.addedNodes.forEach(function(node) {
                                if (node.nodeType === 1) {
                                    if (node.classList && node.classList.contains('modal')) {
                                        needsFixing = true;
                                    } else if (node.querySelector && node.querySelector('.modal')) {
                                        needsFixing = true;
                                    }
                                }
                            });
                        } else if (mutation.type === 'attributes') {
                            if (mutation.target.classList && 
                                mutation.target.classList.contains('modal') && 
                                mutation.attributeName === 'class') {
                                needsFixing = true;
                            }
                        }
                    });
                    
                    if (needsFixing) {
                        ModalManager.fixAllModals();
                    }
                });
                
                observer.observe(document.body, { 
                    childList: true, 
                    subtree: true,
                    attributes: true,
                    attributeFilter: ['class', 'style']
                });
            }
        },
        
        /**
         * 修复所有模态框的位置
         */
        fixAllModals: function() {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(function(modal) {
                ModalManager.fixModalPosition(modal);
            });
        },
        
        /**
         * 修复单个模态框的位置
         * @param {HTMLElement} modal - 模态框元素
         */
        fixModalPosition: function(modal) {
            if (!modal) return;
            
            // 标记模态框为已处理
            modal.setAttribute('data-position-fixed-done', 'true');
            
            // 获取对话框
            const dialog = modal.querySelector('.modal-dialog');
            if (!dialog) return;
            
            // 标记对话框
            dialog.setAttribute('data-position-fixed', 'true');
            dialog.setAttribute('data-position-fixed-done', 'true');
            
            // 直接设置内联样式，确保最高优先级
            dialog.style.cssText = `
                position: fixed !important;
                top: 30% !important;
                left: 50% !important;
                transform: translateX(-50%) !important;
                margin: 0 !important;
                transition: none !important;
                animation: none !important;
            `;
            
            // 禁用模态框的所有动画
            modal.style.cssText += `
                transition: none !important;
                animation: none !important;
            `;
            
            // 特殊处理模态框内容
            const content = dialog.querySelector('.modal-content');
            if (content) {
                content.style.cssText = `
                    transition: none !important;
                    animation: none !important;
                `;
            }
            
            // 对于确认部署对话框进行特殊处理
            if (modal.id === 'deployConfirmModal' || modal.id.startsWith('confirmModal')) {
                dialog.style.maxWidth = '500px';
                dialog.style.minWidth = '300px';
            }
        },
        
        /**
         * 创建和显示确认对话框
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
            
            // 创建模态框元素
            const modalId = 'dynamicConfirmModal-' + Math.floor(Math.random() * 1000000);
            const modalHtml = `
                <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true" data-position-fixed-done="true">
                    <div class="modal-dialog" data-position-fixed="true" data-position-fixed-done="true">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${settings.title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                            </div>
                            <div class="modal-body">
                                <p>${settings.message}</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary cancel-btn" data-bs-dismiss="modal">${settings.cancelText}</button>
                                <button type="button" class="btn btn-primary confirm-btn">${settings.confirmText}</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 添加到文档
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // 获取模态框元素
            const modalElement = document.getElementById(modalId);
            
            // 修复模态框位置
            ModalManager.fixModalPosition(modalElement);
            
            // 创建模态框实例
            const modal = new bootstrap.Modal(modalElement);
            
            // 绑定确认按钮事件
            const confirmBtn = modalElement.querySelector('.confirm-btn');
            confirmBtn.addEventListener('click', function() {
                settings.onConfirm();
                modal.hide();
            });
            
            // 绑定取消按钮事件（可选）
            const cancelBtn = modalElement.querySelector('.cancel-btn');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', function() {
                    settings.onCancel();
                });
            }
            
            // 模态框关闭后移除DOM元素
            modalElement.addEventListener('hidden.bs.modal', function() {
                setTimeout(function() {
                    modalElement.remove();
                }, 300);
            });
            
            // 显示模态框
            modal.show();
            
            // 使用RAF确保在下一帧再次修复位置
            requestAnimationFrame(function() {
                ModalManager.fixModalPosition(modalElement);
            });
            
            return modal;
        }
    };
    
    // 将ModalManager暴露为全局变量
    window.ModalManager = ModalManager;
    
    // 自动初始化
    ModalManager.init();
})(); 