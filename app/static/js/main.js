// 主页面脚本

// 导航栏切换
function setupNavigation() {
    const navLinks = document.querySelectorAll('.navbar-nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 移除所有激活状态
            navLinks.forEach(item => item.classList.remove('active'));
            // 添加当前激活状态
            this.classList.add('active');
        });
    });
}

// 通用的API请求函数
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '请求失败');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API请求错误:', error);
        throw error;
    }
}

// 显示加载动画
function showLoading(element) {
    element.innerHTML = '<div class="loading"></div> 处理中...';
    element.disabled = true;
}

// 隐藏加载动画
function hideLoading(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
}

// 显示错误信息
function showError(element, message) {
    element.innerHTML = `<div class="error">${message}</div>`;
}

// 显示成功信息
function showSuccess(element, message) {
    element.innerHTML = `<div class="success">${message}</div>`;
}

// 初始化页面
function initPage() {
    setupNavigation();
}

// 当DOM加载完成后执行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
} else {
    initPage();
}
