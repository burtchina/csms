/**
 * 用户头像生成工具
 * 为没有自定义头像的用户生成基于文字和颜色的默认头像
 */

document.addEventListener('DOMContentLoaded', function() {
    // 生成所有用户头像
    generateUserAvatars();
});

/**
 * 为所有用户头像容器生成头像
 */
function generateUserAvatars() {
    // 查找所有头像容器
    const avatarContainers = document.querySelectorAll('.user-avatar-circle, .user-avatar-circle-sm');
    
    // 遍历容器生成头像
    avatarContainers.forEach(container => {
        const textElement = container.querySelector('.avatar-text, .avatar-text-sm');
        if (textElement) {
            // 获取用户名首字母
            const initial = textElement.textContent.trim();
            
            // 生成随机但固定的颜色（基于文本）
            const backgroundColor = generateColorFromText(initial);
            
            // 设置背景颜色
            container.style.backgroundColor = backgroundColor;
            
            // 计算并设置文本颜色（深色背景用白色文本，浅色背景用深色文本）
            const textColor = isLightColor(backgroundColor) ? '#333333' : '#ffffff';
            textElement.style.color = textColor;
        }
    });
}

/**
 * 根据文本生成一致的颜色
 * @param {string} text 输入文本
 * @returns {string} 16进制颜色代码
 */
function generateColorFromText(text) {
    // 为确保相同文本总是生成相同的颜色，使用简单的散列函数
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
        hash = text.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // 转换为RGB颜色
    const r = (hash & 0xFF0000) >> 16;
    const g = (hash & 0x00FF00) >> 8;
    const b = hash & 0x0000FF;
    
    // 提高饱和度和亮度，确保颜色鲜艳
    const hsl = rgbToHsl(r, g, b);
    hsl[1] = Math.min(1, hsl[1] + 0.3); // 提高饱和度
    
    // 转换回RGB
    const rgb = hslToRgb(hsl[0], hsl[1], hsl[2]);
    
    // 转换为16进制
    return '#' + 
        ((1 << 24) + (rgb[0] << 16) + (rgb[1] << 8) + rgb[2])
        .toString(16)
        .slice(1);
}

/**
 * 检查颜色是否偏浅色
 * @param {string} color 16进制颜色代码
 * @returns {boolean} 如果是浅色返回true，深色返回false
 */
function isLightColor(color) {
    // 转换hex为rgb
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    // 计算亮度 (根据人眼对RGB颜色的感知权重)
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    
    // 亮度大于125认为是浅色
    return brightness > 125;
}

/**
 * 将RGB转换为HSL
 */
function rgbToHsl(r, g, b) {
    r /= 255;
    g /= 255;
    b /= 255;
    
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;
    
    if (max === min) {
        h = s = 0; // 灰色
    } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        
        h /= 6;
    }
    
    return [h, s, l];
}

/**
 * 将HSL转换为RGB
 */
function hslToRgb(h, s, l) {
    let r, g, b;
    
    if (s === 0) {
        r = g = b = l; // 灰色
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
} 