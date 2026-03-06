// 监控可视化页面脚本

// 初始化监控页面
function initMonitorPage() {
    // 加载ECharts库
    loadECharts().then(() => {
        // 初始化图表
        initRequestChart();
        initAccuracyChart();
        initErrorChart();
        
        // 定时更新数据
        setInterval(() => {
            updateCharts();
        }, 5000); // 每5秒更新一次
    });
}

// 加载ECharts库
function loadECharts() {
    return new Promise((resolve, reject) => {
        if (typeof echarts !== 'undefined') {
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// 初始化请求量趋势图表
function initRequestChart() {
    const chartDom = document.getElementById('request-chart');
    if (chartDom) {
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
    }
}

// 初始化模型准确率图表
function initAccuracyChart() {
    const chartDom = document.getElementById('accuracy-chart');
    if (chartDom) {
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
    }
}

// 初始化异常请求分布图表
function initErrorChart() {
    const chartDom = document.getElementById('error-chart');
    if (chartDom) {
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
    }
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
            statsDiv.innerHTML = `
                <div class="card">
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
                </div>
            `;
        }
    } catch (error) {
        console.error('更新图表数据失败:', error);
    }
}

// 当DOM加载完成后执行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initPage();
        initMonitorPage();
    });
} else {
    initPage();
    initMonitorPage();
}
