// 全局变量
let monitorInterval = null;
const monitorIntervalTime = 5000; // 监控刷新间隔(毫秒)
let cpuChart = null;
let memoryChart = null;
let interfaceCharts = {};

// 调试函数
function debug(msg) {
    console.log(msg);
    const debugOutput = document.getElementById('debugOutput');
    if (debugOutput) {
        debugOutput.textContent += msg + '\n';
        debugOutput.scrollTop = debugOutput.scrollHeight;
    }
}

// 历史数据存储
const historyData = {
    timestamps: [],
    cpu: [],
    memory: [],
    interfaces: {}
};

// 时间格式化函数
function formatDateTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('zh-CN');
}

// 比特率格式化函数
function formatBitRate(bits) {
    if (bits < 1000) {
        return bits + ' bit/s';
    } else if (bits < 1000000) {
        return (bits / 1000).toFixed(2) + ' Kbit/s';
    } else if (bits < 1000000000) {
        return (bits / 1000000).toFixed(2) + ' Mbit/s';
    } else {
        return (bits / 1000000000).toFixed(2) + ' Gbit/s';
    }
}

// 初始化图表
function initCharts() {
    debug("初始化图表...");
    try {
        // CPU图表
        const cpuCtx = document.getElementById('cpuChart').getContext('2d');
        cpuChart = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU使用率 (%)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 2,
                    tension: 0.2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: '使用率 (%)'
                        }
                    }
                }
            }
        });

        // 内存图表
        const memoryCtx = document.getElementById('memoryChart').getContext('2d');
        memoryChart = new Chart(memoryCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '内存使用率 (%)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderWidth: 2,
                    tension: 0.2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: '使用率 (%)'
                        }
                    }
                }
            }
        });
        debug("图表初始化成功");
    } catch (error) {
        debug("图表初始化失败: " + error.message);
    }
}

// 更新图表数据
function updateCharts(data) {
    debug("更新图表数据...");
    debug("收到的数据: " + JSON.stringify(data).substring(0, 100) + "...");
    
    // 更新时间轴
    const timeLabel = formatDateTime(data.timestamp);
    
    // 更新CPU和内存数据
    if (historyData.timestamps.length >= 20) {
        historyData.timestamps.shift();
        historyData.cpu.shift();
        historyData.memory.shift();
    }
    
    historyData.timestamps.push(timeLabel);
    historyData.cpu.push(data.cpu);
    historyData.memory.push(data.memory);
    
    // 更新图表
    try {
        cpuChart.data.labels = historyData.timestamps;
        cpuChart.data.datasets[0].data = historyData.cpu;
        cpuChart.update();
        
        memoryChart.data.labels = historyData.timestamps;
        memoryChart.data.datasets[0].data = historyData.memory;
        memoryChart.update();
        
        debug("CPU和内存图表更新成功");
    } catch (error) {
        debug("图表更新失败: " + error.message);
    }
    
    // 更新接口数据
    updateInterfacesUI(data.interfaces);
    
    // 更新其他信息
    document.getElementById('uptime').textContent = data.uptime || '未知';
    document.getElementById('lastUpdate').textContent = timeLabel;
}

// 更新接口UI
function updateInterfacesUI(interfaces) {
    debug("更新接口UI...");
    const container = document.getElementById('interfacesContainer');
    
    // 首次创建接口卡片
    if (container.children.length === 0) {
        debug("创建接口卡片...");
        for (const [name, data] of Object.entries(interfaces)) {
            // 创建接口卡片
            const interfaceCol = document.createElement('div');
            interfaceCol.className = 'col-md-6 col-lg-4 mb-3';
            
            const status = data.status || 'down';
            const statusClass = status === 'up' ? 'interface-up' : 'interface-down';
            const statusText = status === 'up' ? '运行中' : '关闭';
            
            interfaceCol.innerHTML = `
                <div class="card interface-card ${statusClass}" data-interface="${name}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>${name}</span>
                        <span class="badge ${status === 'up' ? 'bg-success' : 'bg-danger'}">${statusText}</span>
                    </div>
                    <div class="card-body" style="height: 200px;">
                        <canvas id="interface-${name.replace(/[/.]/g, '-')}"></canvas>
                        <div class="mt-2 row">
                            <div class="col-6">
                                <small>输入: <span id="input-${name.replace(/[/.]/g, '-')}">0 bit/s</span></small>
                            </div>
                            <div class="col-6">
                                <small>输出: <span id="output-${name.replace(/[/.]/g, '-')}">0 bit/s</span></small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(interfaceCol);
            
            // 为每个接口创建图表
            try {
                const chartId = `interface-${name.replace(/[/.]/g, '-')}`;
                const ctx = document.getElementById(chartId).getContext('2d');
                
                // 初始化接口历史数据
                if (!historyData.interfaces[name]) {
                    historyData.interfaces[name] = {
                        input: [],
                        output: []
                    };
                }
                
                // 创建图表
                interfaceCharts[name] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: historyData.timestamps,
                        datasets: [
                            {
                                label: '输入',
                                data: historyData.interfaces[name].input,
                                borderColor: 'rgb(54, 162, 235)',
                                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                borderWidth: 2,
                                tension: 0.2,
                                fill: true
                            },
                            {
                                label: '输出',
                                data: historyData.interfaces[name].output,
                                borderColor: 'rgb(255, 159, 64)',
                                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                                borderWidth: 2,
                                tension: 0.2,
                                fill: true
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: '流量 (bit/s)'
                                }
                            }
                        }
                    }
                });
                debug(`为接口 ${name} 创建图表成功`);
            } catch (error) {
                debug(`为接口 ${name} 创建图表失败: ${error.message}`);
            }
        }
    }
    
    // 更新接口数据
    for (const [name, data] of Object.entries(interfaces)) {
        // 更新状态
        const cardEl = document.querySelector(`.interface-card[data-interface="${name}"]`);
        if (cardEl) {
            const badgeEl = cardEl.querySelector('.badge');
            if (data.status === 'up') {
                cardEl.classList.remove('interface-down');
                cardEl.classList.add('interface-up');
                badgeEl.classList.remove('bg-danger');
                badgeEl.classList.add('bg-success');
                badgeEl.textContent = '运行中';
            } else {
                cardEl.classList.remove('interface-up');
                cardEl.classList.add('interface-down');
                badgeEl.classList.remove('bg-success');
                badgeEl.classList.add('bg-danger');
                badgeEl.textContent = '关闭';
            }
        }
        
        // 更新流量数据
        const inputEl = document.getElementById(`input-${name.replace(/[/.]/g, '-')}`);
        const outputEl = document.getElementById(`output-${name.replace(/[/.]/g, '-')}`);
        
        if (inputEl && outputEl) {
            const inputRate = data.input_rate || 0;
            const outputRate = data.output_rate || 0;
            
            inputEl.textContent = formatBitRate(inputRate);
            outputEl.textContent = formatBitRate(outputRate);
            
            // 更新接口图表数据
            if (historyData.interfaces[name]) {
                if (historyData.interfaces[name].input.length >= 20) {
                    historyData.interfaces[name].input.shift();
                    historyData.interfaces[name].output.shift();
                }
                
                historyData.interfaces[name].input.push(inputRate);
                historyData.interfaces[name].output.push(outputRate);
                
                // 更新图表
                try {
                    if (interfaceCharts[name]) {
                        interfaceCharts[name].data.labels = historyData.timestamps;
                        interfaceCharts[name].data.datasets[0].data = historyData.interfaces[name].input;
                        interfaceCharts[name].data.datasets[1].data = historyData.interfaces[name].output;
                        interfaceCharts[name].update();
                        debug(`更新接口 ${name} 图表成功`);
                    }
                } catch (error) {
                    debug(`更新接口 ${name} 图表失败: ${error.message}`);
                }
            }
        }
    }
}

// 获取性能数据
function fetchData() {
    debug("开始获取数据...");
    
    // 使用完整URL路径确保能找到API
    const apiUrl = window.location.origin + '/api/data';
    debug(`请求API: ${apiUrl}`);
    
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP错误! 状态: ${response.status}`);
            }
            debug("收到API响应，正在解析...");
            return response.json();
        })
        .then(data => {
            debug("数据解析成功，开始更新图表");
            updateCharts(data);
        })
        .catch(error => {
            debug(`获取数据失败: ${error.message}`);
            alert(`获取监控数据失败: ${error.message}\n请检查控制台获取更多信息`);
            stopMonitoring(); // 出错时停止监控
        });
}

// 启动监控
function startMonitoring() {
    debug("开始启动监控...");
    
    // 显示监控区域
    document.getElementById('monitoringArea').style.display = 'block';
    
    // 初始化图表
    if (!cpuChart || !memoryChart) {
        initCharts();
    }
    
    // 立即获取一次数据
    fetchData();
    
    // 设置定时获取
    monitorInterval = setInterval(fetchData, monitorIntervalTime);
    debug(`已设置${monitorIntervalTime}ms的定时监控`);
    
    // 更新按钮状态
    document.getElementById('startMonitor').disabled = true;
    document.getElementById('stopMonitor').disabled = false;
}

// 停止监控
function stopMonitoring() {
    debug("停止监控");
    if (monitorInterval) {
        clearInterval(monitorInterval);
        monitorInterval = null;
    }
    
    // 更新按钮状态
    document.getElementById('startMonitor').disabled = false;
    document.getElementById('stopMonitor').disabled = true;
}

// 事件监听
document.addEventListener('DOMContentLoaded', function() {
    debug("页面加载完成，设置事件处理程序");
    
    // 启动监控按钮
    document.getElementById('startMonitor').addEventListener('click', function() {
        debug("点击启动监控按钮");
        startMonitoring();
    });
    
    // 停止监控按钮
    document.getElementById('stopMonitor').addEventListener('click', function() {
        debug("点击停止监控按钮");
        stopMonitoring();
    });
    
    // 刷新数据按钮
    document.getElementById('refreshData').addEventListener('click', function() {
        debug("点击刷新数据按钮");
        fetchData();
    });
    
    // 自动启动监控 - 页面加载后直接显示图表
    debug("自动启动监控");
    startMonitoring();
}); 