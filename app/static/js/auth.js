// 认证相关脚本

// 初始化认证页面
function initAuthPage() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await handleLogin();
        });
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await handleRegister();
        });
    }
}

// 处理登录
async function handleLogin() {
    const form = document.getElementById('login-form');
    const username = form?.querySelector('input[name="username"]')?.value?.trim();
    const password = form?.querySelector('input[name="password"]')?.value;
    const loginButton = document.getElementById('login-button');
    const messageDiv = document.getElementById('message');
    
    // 显示加载状态
    const originalText = loginButton.innerHTML;
    showLoading(loginButton);
    messageDiv.innerHTML = '';
    
    try {
        if (!username || !password) {
            messageDiv.innerHTML = `<div class="error">请输入用户名和密码</div>`;
            return;
        }
        console.log('登录请求数据:', { username, password });
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        console.log('登录响应状态:', response.status);
        
        const result = await response.json().catch(() => ({}));
        console.log('登录响应数据:', result);

        if (!response.ok) {
            const msg = (result.detail && (result.detail.error_message || result.detail)) || '登录失败';
            messageDiv.innerHTML = `<div class="error">${msg}</div>`;
            return;
        }
        
        if (result.success) {
            // 登录成功
            messageDiv.innerHTML = `<div class="success">${result.message}</div>`;
            // 存储会话ID到cookie
            if (result.session_id) {
                document.cookie = `session_id=${result.session_id}; path=/; max-age=3600`;
            }
            // 跳转到首页
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            // 登录失败
            messageDiv.innerHTML = `<div class="error">${result.message || '登录失败'}</div>`;
        }
    } catch (error) {
        messageDiv.innerHTML = `<div class="error">登录失败，请稍后重试</div>`;
        console.error('登录失败:', error);
    } finally {
        // 恢复按钮状态
        hideLoading(loginButton, originalText);
    }
}

// 处理注册
async function handleRegister() {
    const form = document.getElementById('register-form');
    const username = form?.querySelector('input[name="username"]')?.value?.trim();
    const email = form?.querySelector('input[name="email"]')?.value?.trim();
    const password = form?.querySelector('input[name="password"]')?.value;
    const registerButton = document.getElementById('register-button');
    const messageDiv = document.getElementById('message');
    
    // 显示加载状态
    const originalText = registerButton.innerHTML;
    showLoading(registerButton);
    messageDiv.innerHTML = '';
    
    try {
        if (!username || !email || !password) {
            messageDiv.innerHTML = `<div class="error">请填写用户名、邮箱和密码</div>`;
            return;
        }
        // 基础邮箱格式校验
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            messageDiv.innerHTML = `<div class="error">邮箱格式不正确</div>`;
            return;
        }
        // 基础密码强度
        if (password.length < 6) {
            messageDiv.innerHTML = `<div class="error">密码至少 6 位</div>`;
            return;
        }
        console.log('注册请求数据:', { username, email, password });
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        console.log('注册响应状态:', response.status);
        
        const result = await response.json().catch(() => ({}));
        console.log('注册响应数据:', result);

        if (!response.ok) {
            // FastAPI 422/401 等通常返回 detail
            const msg = (result.detail && (result.detail.error_message || result.detail)) || '注册失败';
            messageDiv.innerHTML = `<div class="error">${msg}</div>`;
            return;
        }
        
        if (result.success) {
            // 注册成功
            messageDiv.innerHTML = `<div class="success">${result.message}</div>`;
            // 跳转到登录页面
            setTimeout(() => {
                window.location.href = '/api/auth/login';
            }, 1000);
        } else {
            // 注册失败
            messageDiv.innerHTML = `<div class="error">${result.message || '注册失败'}</div>`;
        }
    } catch (error) {
        messageDiv.innerHTML = `<div class="error">注册失败，请稍后重试</div>`;
        console.error('注册失败:', error);
    } finally {
        // 恢复按钮状态
        hideLoading(registerButton, originalText);
    }
}

// 显示加载动画
function showLoading(button) {
    button.innerHTML = '<div class="loading"></div> 处理中...';
    button.disabled = true;
}

// 隐藏加载动画
function hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

// 当DOM加载完成后执行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initAuthPage();
    });
} else {
    initAuthPage();
}
