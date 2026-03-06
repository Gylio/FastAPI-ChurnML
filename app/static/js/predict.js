// 单条预测页面脚本

// 初始化预测页面
function initPredictPage() {
    const predictForm = document.getElementById('predict-form');
    const predictButton = document.getElementById('predict-button');
    const resultDiv = document.getElementById('result');
    
    if (predictForm) {
        predictForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // 收集表单数据
            const formData = {
                gender: document.getElementById('gender').value,
                SeniorCitizen: parseInt(document.getElementById('SeniorCitizen').value),
                Partner: document.getElementById('Partner').value,
                Dependents: document.getElementById('Dependents').value,
                tenure: parseInt(document.getElementById('tenure').value),
                PhoneService: document.getElementById('PhoneService').value,
                MultipleLines: document.getElementById('MultipleLines').value,
                InternetService: document.getElementById('InternetService').value,
                OnlineSecurity: document.getElementById('OnlineSecurity').value,
                OnlineBackup: document.getElementById('OnlineBackup').value,
                DeviceProtection: document.getElementById('DeviceProtection').value,
                TechSupport: document.getElementById('TechSupport').value,
                StreamingTV: document.getElementById('StreamingTV').value,
                StreamingMovies: document.getElementById('StreamingMovies').value,
                Contract: document.getElementById('Contract').value,
                PaperlessBilling: document.getElementById('PaperlessBilling').value,
                PaymentMethod: document.getElementById('PaymentMethod').value,
                MonthlyCharges: parseFloat(document.getElementById('MonthlyCharges').value),
                TotalCharges: parseFloat(document.getElementById('TotalCharges').value)
            };
            
            // 显示加载动画
            const originalText = predictButton.innerHTML;
            showLoading(predictButton);
            
            try {
                // 发送API请求
                const result = await fetchAPI('/api/predict', {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });
                
                // 显示结果
                displayResult(resultDiv, result);
            } catch (error) {
                showError(resultDiv, `预测失败: ${error.message}`);
            } finally {
                // 隐藏加载动画
                hideLoading(predictButton, originalText);
            }
        });
    }
}

// 显示预测结果
function displayResult(element, result) {
    element.innerHTML = `
        <div class="result">
            <h3>预测结果</h3>
            <div class="result-item">
                <span class="result-label">预测标签:</span>
                <span class="result-value">${result.prediction === 'Yes' ? '流失' : '未流失'}</span>
            </div>
            <div class="result-item">
                <span class="result-label">流失概率:</span>
                <span class="result-value">${(result.probability * 100).toFixed(2)}%</span>
            </div>
            <div class="result-item">
                <span class="result-label">使用模型版本:</span>
                <span class="result-value">v${result.model_version}</span>
            </div>
            <div class="result-item">
                <span class="result-label">响应时间:</span>
                <span class="result-value">${(Date.now() - startTime).toFixed(2)}ms</span>
            </div>
        </div>
    `;
}

// 当DOM加载完成后执行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initPage();
        initPredictPage();
    });
} else {
    initPage();
    initPredictPage();
}

// 记录开始时间
let startTime = Date.now();
