/**
 * 头像生成器
 * 用于生成默认用户头像
 */

document.addEventListener('DOMContentLoaded', function() {
  // 查找所有缺少src的头像图片
  const avatarImages = document.querySelectorAll('.user-profile .avatar img');
  
  avatarImages.forEach(function(img) {
    // 检查图片是否存在src，如果不存在或者加载失败，生成默认头像
    img.addEventListener('error', function() {
      generateAvatar(img);
    });
    
    // 如果图片的src是占位符或默认头像路径，也生成默认头像
    if (!img.getAttribute('src') || img.getAttribute('src').includes('default-avatar')) {
      generateAvatar(img);
    }
  });
  
  /**
   * 生成默认头像并设置为图片源
   * @param {HTMLImageElement} imgElement - 图片元素
   */
  function generateAvatar(imgElement) {
    // 为用户生成唯一的颜色（基于用户名或随机）
    const username = imgElement.closest('.user-profile').querySelector('.user-info h6').textContent.trim();
    const colors = [
      '#3a4fd8', '#4caf50', '#ff9800', '#e91e63',
      '#2196f3', '#9c27b0', '#607d8b', '#ff5722'
    ];
    
    // 使用用户名计算颜色索引或随机选择
    let colorIndex = 0;
    if (username) {
      // 简单的哈希函数计算用户名对应的颜色
      for (let i = 0; i < username.length; i++) {
        colorIndex += username.charCodeAt(i);
      }
      colorIndex = colorIndex % colors.length;
    } else {
      colorIndex = Math.floor(Math.random() * colors.length);
    }
    
    const color = colors[colorIndex];
    const backgroundColor = color;
    
    // 获取用户名首字母或默认使用"用"字
    const initial = username ? username.charAt(0).toUpperCase() : '用';
    
    // 创建SVG头像
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="40" fill="${backgroundColor}" />
        <text x="40" y="40" dy="0.35em" font-family="Arial, sans-serif" font-size="40" fill="white" text-anchor="middle" dominant-baseline="middle">${initial}</text>
      </svg>
    `;
    
    // 转换为base64数据URI
    const svgBase64 = window.btoa(svg);
    const dataURI = `data:image/svg+xml;base64,${svgBase64}`;
    
    // 设置图片源
    imgElement.setAttribute('src', dataURI);
  }
}); 