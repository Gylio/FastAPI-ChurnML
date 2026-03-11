// 监控可视化页面脚本

// 初始化监控页面
function initMonitorPage() {
    // 加载ECharts库
    loadECharts().then(() => {
        // 初始化图表
        initRequestChart();
        initAccuracyChart();
        initErrorChart();

         // 初始化模型版本管理
        initModelVersionManagement();
        
        // 定时更新数据
        setInterval(() => {
            updateCharts();
        }, 5000); // 每5秒更新一次
    });
}

// 初始化模型版本管理
function initModelVersionManagement() {
    console.log('开始初始化模型版本管理');
    
    // 检查DOM元素是否存在
    const select = document.getElementById('model-version');
    const switchButton = document.getElementById('switch-model-btn');
    const statusDiv = document.getElementById('model-status');
    
    console.log('模型版本下拉框:', select);
    console.log('切换模型按钮:', switchButton);
    console.log('模型状态div:', statusDiv);
    
    // 获取模型版本列表
    console.log('开始获取模型版本列表');
    fetchModelVersions();
    
    // 绑定切换模型按钮事件
    if (switchButton) {
        switchButton.addEventListener('click', async () => {
            await switchModel();
        });
    }
}

// 获取模型版本列表
async function fetchModelVersions() {
    console.log('开始获取模型版本列表');
    try {
        const response = await fetch('/api/model/version');
        console.log('获取模型版本列表响应:', response);
        if (!response.ok) {
            throw new Error('获取模型版本失败');
        }
        const data = await response.json();
        console.log('获取模型版本列表数据:', data);
        
        // 填充模型版本下拉框
        const select = document.getElementById('model-version');
        console.log('获取模型版本下拉框:', select);
        if (select) {
            select.innerHTML = '';
            console.log('模型版本数量:', data.versions.length);
            data.versions.forEach(version => {
                const option = document.createElement('option');
                option.value = version.version;
                option.textContent = `v${version.version} - ${version.filename}`;
                select.appendChild(option);
                console.log('添加模型版本选项:', option.textContent);
            });
        }
        
        // 更新当前模型状态
        updateModelStatus(data.current_version);
    } catch (error) {
        console.error('获取模型版本失败:', error);
    }
}

// 更新模型状态
function updateModelStatus(currentVersion) {
    const statusDiv = document.getElementById('model-status');
    if (statusDiv) {
        statusDiv.innerHTML = `<div class="result-value">当前模型: v${currentVersion || '未加载'}</div>`;
    }
}

// 切换模型
async function switchModel() {
    const select = document.getElementById('model-version');
    const switchButton = document.getElementById('switch-model-btn');
    
    if (!select) return;
    
    const selectedVersion = parseInt(select.value);
    if (isNaN(selectedVersion)) {
        alert('请选择有效的模型版本');
        return;
    }
    
    // 显示加载状态
    const originalText = switchButton.innerHTML;
    switchButton.innerHTML = '<div class="loading"></div> 切换中...';
    switchButton.disabled = true;
    
    try {
        const response = await fetch('/api/model/switch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ version: selectedVersion })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.error_message || '切换模型失败');
        }
        
        const data = await response.json();
        
        // 更新模型状态
        updateModelStatus(data.current_version);
        
        // 显示成功消息
        alert(`模型切换成功！当前模型版本: v${data.current_version}`);
        
        // 重新获取模型版本列表
        fetchModelVersions();
    } catch (error) {
        console.error('切换模型失败:', error);
        alert(`切换模型失败: ${error.message}`);
    } finally {
        // 恢复按钮状态
        switchButton.innerHTML = originalText;
        switchButton.disabled = false;
    }
}

// 加载ECharts库
function loadECharts() {
    return new Promise((resolve, reject) => {
        if (typeof echarts !== 'undefined') {
            console.log('ECharts已经加载');
            resolve();
            return;
        }
        
        console.log('开始加载ECharts库');
        let script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js';
        script.onload = function() {
            console.log('ECharts CDN加载成功');
            resolve();
        };
        script.onerror = function(error) {
            console.error('ECharts CDN加载失败，尝试使用本地版本', error);
            // 尝试使用本地ECharts库
            script = document.createElement('script');
            script.src = '/static/js/echarts.min.js';
            script.onload = function() {
                console.log('ECharts本地版本加载成功');
                resolve();
            };
            script.onerror = function(error) {
                console.error('ECharts本地版本加载失败', error);
                // 即使ECharts加载失败，也继续执行，只是图表无法显示
                resolve();
            };
            document.head.appendChild(script);
        };
        document.head.appendChild(script);
    });
}

// 初始化请求量趋势图表
function initRequestChart() {
    const chartDom = document.getElementById('request-chart');
    if (chartDom && typeof echarts !== 'undefined') {
        try {
            const myChart = echarts.init(chartDom);
            
            const option = {
                title: {
                    text: '请求量趋势',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis'
                },
                legend: {
                    data: ['总请求数', '成功请求数', '失败请求数'],
                    bottom: 0
                },
                xAxis: {
                    type: 'category',
                    data: ['10:00', '10:05', '10:10', '10:15', '10:20', '10:25', '10:30']
                },
                yAxis: {
                    type: 'value'
                },
                series: [
                    {
                        name: '总请求数',
                        type: 'line',
                        data: [120, 132, 101, 134, 90, 230, 210],
                        smooth: true
                    },
                    {
                        name: '成功请求数',
                        type: 'line',
                        data: [110, 122, 91, 124, 80, 220, 200],
                        smooth: true
                    },
                    {
                        name: '失败请求数',
                        type: 'line',
                        data: [10, 10, 10, 10, 10, 10, 10],
                        smooth: true
                    }
                ]
            };
            
            myChart.setOption(option);
            
            // 保存图表实例
            window.requestChart = myChart;
            console.log('请求量趋势图表初始化成功');
        } catch (error) {
            console.error('请求量趋势图表初始化失败', error);
        }
    } else if (chartDom) {
        console.warn('ECharts未加载，无法初始化请求量趋势图表');
    }
}

// 初始化模型准确率图表
function initAccuracyChart() {
    const chartDom = document.getElementById('accuracy-chart');
    if (chartDom && typeof echarts !== 'undefined') {
        try {
            const myChart = echarts.init(chartDom);
            
            const option = {
                title: {
                    text: '模型准确率变化',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis'
                },
                yAxis: {
                    type: 'value',
                    min: 0.7,
                    max: 1
                },
                xAxis: {
                    type: 'category',
                    data: ['v1', 'v2', 'v3', 'v4', 'v5']
                },
                series: [{
                    data: [0.82, 0.85, 0.87, 0.88, 0.90],
                    type: 'line',
                    smooth: true,
                    itemStyle: {
                        color: '#3498db'
                    }
                }]
            };
            
            myChart.setOption(option);
            
            // 保存图表实例
            window.accuracyChart = myChart;
            console.log('模型准确率图表初始化成功');
        } catch (error) {
            console.error('模型准确率图表初始化失败', error);
        }
    } else if (chartDom) {
        console.warn('ECharts未加载，无法初始化模型准确率图表');
    }
}

// 初始化异常请求分布图表
function initErrorChart() {
    const chartDom = document.getElementById('error-chart');
    if (chartDom && typeof echarts !== 'undefined') {
        try {
            const myChart = echarts.init(chartDom);
            
            const option = {
                title: {
                    text: '异常请求分布',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'item'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left'
                },
                series: [
                    {
                        name: '异常类型',
                        type: 'pie',
                        radius: '60%',
                        data: [
                            {value: 30, name: '数据校验失败'},
                            {value: 15, name: '模型加载失败'},
                            {value: 10, name: '文件格式错误'},
                            {value: 5, name: '其他错误'}
                        ],
                        emphasis: {
                            itemStyle: {
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                            }
                        }
                    }
                ]
            };
            
            myChart.setOption(option);
            
            // 保存图表实例
            window.errorChart = myChart;
            console.log('异常请求分布图表初始化成功');
        } catch (error) {
            console.error('异常请求分布图表初始化失败', error);
        }
    } else if (chartDom) {
        console.warn('ECharts未加载，无法初始化异常请求分布图表');
    }
}

// 封装fetch API
async function fetchAPI(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// 更新图表数据
async function updateCharts() {
    try {
        // 获取统计数据
        const stats = await fetchAPI('/api/stats');
        
        // 更新请求量趋势图表
        if (window.requestChart) {
            // 模拟数据更新
            const now = new Date();
            const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
            
            const option = window.requestChart.getOption();
            option.xAxis[0].data.push(timeStr);
            if (option.xAxis[0].data.length > 7) {
                option.xAxis[0].data.shift();
            }
            
            option.series[0].data.push(stats.total_requests % 300);
            if (option.series[0].data.length > 7) {
                option.series[0].data.shift();
            }
            
            option.series[1].data.push(stats.successful_requests % 250);
            if (option.series[1].data.length > 7) {
                option.series[1].data.shift();
            }
            
            option.series[2].data.push(stats.failed_requests % 50);
            if (option.series[2].data.length > 7) {
                option.series[2].data.shift();
            }
            
            window.requestChart.setOption(option);
        }
        
        // 更新模型准确率图表
        if (window.accuracyChart && stats.accuracy) {
            const option = window.accuracyChart.getOption();
            if (option.series[0].data.length > 5) {
                option.series[0].data.shift();
            }
            option.series[0].data.push(stats.accuracy);
            window.accuracyChart.setOption(option);
        }
        
        // 更新统计信息
        const statsDiv = document.getElementById('stats-info');
        if (statsDiv) {
            // 只更新实时统计卡片，保留模型版本管理卡片
            const realTimeStatsCard = statsDiv.querySelector('.card:first-child');
            if (realTimeStatsCard) {
                realTimeStatsCard.innerHTML = `
                    <h3>实时统计</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label>总请求数</label>
                            <div class="result-value">${stats.total_requests}</div>
                        </div>
                        <div class="form-group">
                            <label>成功请求数</label>
                            <div class="result-value">${stats.successful_requests}</div>
                        </div>
                        <div class="form-group">
                            <label>失败请求数</label>
                            <div class="result-value">${stats.failed_requests}</div>
                        </div>
                        <div class="form-group">
                            <label>模型准确率</label>
                            <div class="result-value">${stats.accuracy ? (stats.accuracy * 100).toFixed(2) + '%' : 'N/A'}</div>
                        </div>
                        <div class="form-group">
                            <label>平均响应时间</label>
                            <div class="result-value">${(stats.average_response_time * 1000).toFixed(2)}ms</div>
                        </div>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('更新图表数据失败:', error);
    }
}

// 当DOM加载完成后执行
console.log('DOM加载状态:', document.readyState);
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOMContentLoaded事件触发');
        if (typeof initPage === 'function') {
            initPage();
        } else {
            console.log('initPage函数不存在');
        }
        initMonitorPage();
    });
} else {
    console.log('DOM已经加载完成');
    if (typeof initPage === 'function') {
        initPage();
    } else {
        console.log('initPage函数不存在');
    }
    initMonitorPage();
}
