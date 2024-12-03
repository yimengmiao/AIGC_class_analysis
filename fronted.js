const { spawn } = require('child_process');
const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

// 启动 Python 脚本，传递命令行参数
const pythonProcess = spawn('python', [
    'test1.py',                          // 脚本名
    '--grade', '2',                      // 参数 --grade 2
    '--subject', '语文',                 // 参数 --subject "语文"
    '--task', '教学效果',                 // 参数 --task "教学效果"
    '--analysis_text',                   // 参数 --analysis_text
    `老师：请袁艺开始你啊上课，声音要响亮啊，同学们好，请坐真棒。昨天呀，我们一起学习了课文八。老师：今天 猴，反犬旁，旁边是一个单立人，中间有没有一个短竖啊？老师：那么昨天在作业当中，方老师看到有人加了一竖，那就不对了，变成错别字了，明白了吗？好，现在用眼睛看，用心记住这个字，猴猴猴子。老师：每天通过学习啊，我们知道了这个猴子啊，种了一些果树，它分别种了什么树呢？谁来说说，于凯，你来说说看。学生：嗯，好的。`
]);

// 设置 WebSocket 服务
const wss = new WebSocket.Server({ port: 8081 });
let wsClient = null;

wss.on('connection', (ws) => {
    console.log('WebSocket client connected');
    wsClient = ws;
});

// 创建一个 HTTP 服务器来托管 HTML 文件
const server = http.createServer((req, res) => {
    if (req.url === '/') {
        // 返回 HTML 页面
        const html = fs.readFileSync(path.join(__dirname, 'output.html'), 'utf-8');
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(html);
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

// 监听 Python 脚本的标准输出
let outputBuffer = '';

pythonProcess.stdout.on('data', (data) => {
    const content = data.toString('utf-8'); // 明确设置编码为 UTF-8
    console.log(`Received: ${content}`); // 打印到控制台

    // 更新页面内容
    outputBuffer += content;
    updateHTML(outputBuffer);

    // 如果有 WebSocket 客户端，发送更新内容
    if (wsClient) {
        wsClient.send(content);
    }
});

// 监听 Python 脚本的错误输出
pythonProcess.stderr.on('data', (data) => {
    console.error(`Error: ${data}`);
});

// 监听 Python 脚本的退出事件
pythonProcess.on('close', (code) => {
    console.log(`Python script exited with code ${code}`);
});

// 启动 HTTP 服务器
server.listen(8080, () => {
    console.log('Server running at http://127.0.0.1:8080/');
});

// 更新 HTML 文件内容
function updateHTML(content) {
    const htmlTemplate = `
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Python Stream Output</title>
        </head>
        <body>
            <div id="output" style="font-size: 18px; white-space: pre-wrap;">
                ${content}
            </div>
            <script>
                // WebSocket 实现自动刷新
                const ws = new WebSocket('ws://127.0.0.1:8081');
                ws.onmessage = (event) => {
                    const outputDiv = document.getElementById('output');
                    outputDiv.textContent += event.data; // 动态追加新内容
                };
            </script>
        </body>
        </html>
    `;

    // 写入 HTML 文件
    fs.writeFileSync(path.join(__dirname, 'output.html'), htmlTemplate, 'utf-8');
}
