// 批量预测页面脚本

// 初始化批量预测页面
function initBatchPage() {
    const batchForm = document.getElementById('batch-form');
    const batchButton = document.getElementById('batch-button');
    const resultDiv = document.getElementById('result');
    
    if (batchForm) {
        batchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('file');
            const file = fileInput.files[0];
            
            if (!file) {
                showError(resultDiv, '请选择要上传的文件');
                return;
            }
            
            // 检查文件格式
            const fileName = file.name.toLowerCase();
            if (!fileName.endsWith('.csv') && !fileName.endsWith('.xlsx')) {
                showError(resultDiv, '仅支持CSV和Excel文件');
                return;
            }
            
            // 显示加载动画
            const originalText = batchButton.innerHTML;
            showLoading(batchButton);
            
            try {
                // 创建FormData对象
                const formData = new FormData();
                formData.append('file', file);
                
                // 发送API请求
                const response = await fetch('/api/batch-predict', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail?.error_message || '批量预测失败');
                }
                
                const result = await response.json();
                
                // 显示结果
                displayBatchResult(resultDiv, result);
            } catch (error) {
                showError(resultDiv, `批量预测失败: ${error.message}`);
            } finally {
                // 隐藏加载动画
                hideLoading(batchButton, originalText);
            }
        });
    }
}

// 显示批量预测结果
function displayBatchResult(element, result) {
    element.innerHTML = `
        <div class="batch-results">
            <h3>批量预测结果</h3>
            <div class="result-item">
                <span class="result-label">总预测数量:</span>
                <span class="result-value">${result.total_count}</span>
            </div>
            <div class="result-item">
                <span class="result-label">流失数量:</span>
                <span class="result-value">${result.churn_count}</span>
            </div>
            <div class="result-item">
                <span class="result-label">未流失数量:</span>
                <span class="result-value">${result.non_churn_count}</span>
            </div>
            
            ${result.items.length > 0 ? `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>客户ID</th>
                                <th>预测结果</th>
                                <th>流失概率</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.items.slice(0, 10).map(item => `
                                <tr>
                                    <td>${item.customerID || 'N/A'}</td>
                                    <td>${item.prediction === 'Yes' ? '流失' : '未流失'}</td>
                                    <td>${(item.probability * 100).toFixed(2)}%</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${result.items.length > 10 ? `<p>显示前10条结果，共${result.items.length}条</p>` : ''}
            ` : ''}
            
            ${result.download_url ? `
                <div style="margin-top: 20px;">
                    <a href="${result.download_url}" class="download-btn">下载完整结果</a>
                </div>
            ` : ''}
        </div>
    `;
}

// 当DOM加载完成后执行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initPage();
        initBatchPage();
    });
} else {
    initPage();
    initBatchPage();
}
