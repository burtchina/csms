/**
 * 校园安全管理系统 - 主要JavaScript函数
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('主程序初始化完成');
    
    // 激活当前菜单项
    activateCurrentMenuItem();
    
    // 初始化工具提示
    initTooltips();
    
    // 初始化下拉菜单
    initDropdowns();
});

/**
 * 根据当前URL激活侧边栏菜单项
 */
function activateCurrentMenuItem() {
    // 获取当前URL路径
    const currentPath = window.location.pathname;
    
    // 查找所有侧边栏菜单项
    const menuItems = document.querySelectorAll('.sidebar-item');
    
    // 遍历菜单项，检查href是否匹配当前路径
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentPath || 
            (currentPath.includes(item.getAttribute('href')) && item.getAttribute('href') !== '/')) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

/**
 * 初始化Bootstrap工具提示
 */
function initTooltips() {
    // 检查是否有Bootstrap Tooltip对象
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Tooltip !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 初始化Bootstrap下拉菜单
 */
function initDropdowns() {
    // 检查是否有Bootstrap Dropdown对象
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Dropdown !== 'undefined') {
        const dropdownTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
        dropdownTriggerList.map(function(dropdownTriggerEl) {
            return new bootstrap.Dropdown(dropdownTriggerEl);
        });
    }
}

/**
 * 格式化日期时间
 * @param {Date|string} date 日期对象或日期字符串
 * @param {boolean} includeTime 是否包含时间
 * @returns {string} 格式化后的日期时间字符串
 */
function formatDateTime(date, includeTime = true) {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    let formatted = `${year}-${month}-${day}`;
    
    if (includeTime) {
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        formatted += ` ${hours}:${minutes}`;
    }
    
    return formatted;
} 