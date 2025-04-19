/**
 * 校园安全管理系统主JavaScript文件
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
  // 初始化工具提示
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function(tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 初始化弹出框
  var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function(popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
  
  // 给警告框添加关闭功能
  setTimeout(function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
      setTimeout(function() {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      }, 5000);
    });
  }, 1000);

  // 侧边栏切换
  const menuToggle = document.getElementById('menu-toggle');
  const wrapper = document.getElementById('wrapper');
  
  if (menuToggle && wrapper) {
    // 强制重绘侧边栏
    setTimeout(function() {
      wrapper.style.display = 'none';
      setTimeout(function() {
        wrapper.style.display = 'flex';
      }, 10);
    }, 100);
    
    menuToggle.addEventListener('click', function(e) {
      e.preventDefault();
      wrapper.classList.toggle('toggled');
      // 强制浏览器重绘
      document.body.offsetHeight;
    });
  }

  // 检查移动设备视口，自动折叠侧边栏
  function checkViewport() {
    if (window.innerWidth < 768 && wrapper) {
      if (!wrapper.classList.contains('toggled')) {
        wrapper.classList.add('toggled');
      }
    } else {
      if (wrapper && window.innerWidth >= 768 && wrapper.classList.contains('toggled')) {
        wrapper.classList.remove('toggled');
      }
    }
  }

  // 初始检查
  checkViewport();

  // 窗口大小改变时重新检查
  window.addEventListener('resize', checkViewport);
  
  // 修复Win11下可能的布局问题
  function fixLayoutIssues() {
    const sidebar = document.getElementById('sidebar-wrapper');
    const pageContent = document.getElementById('page-content-wrapper');
    
    if (sidebar && pageContent) {
      // 强制刷新DOM计算
      sidebar.style.display = 'none';
      sidebar.offsetHeight; // 触发重排
      sidebar.style.display = 'block';
      
      pageContent.style.display = 'none';
      pageContent.offsetHeight; // 触发重排
      pageContent.style.display = 'flex';
    }
  }
  
  // 尝试修复布局
  setTimeout(fixLayoutIssues, 500);
}); 