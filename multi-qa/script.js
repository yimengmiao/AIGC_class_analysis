// 定义API相关参数
const apiUrl = 'https://your-api-server.com/v1/chat/completions'; // 替换为您的API服务器地址
const apiKey = 'token-abc123'; // 替换为您的API密钥
const modelName = 'qwen2_5-32b-instruct'; // 替换为您的模型名称

// 初始化对话历史，包含系统消息
let conversationHistory = [
    {"role": "system", "content": "You are a great ai assistant."}
];

// 绑定发送按钮的点击事件
document.getElementById('send-button').addEventListener('click', sendMessage);

// 发送消息函数
async function sendMessage() {
    const userInput = document.getElementById('user-input').value.trim();
    if (!userInput) return;

    // 显示用户消息
    appendMessage('用户', userInput);

    // 将用户消息添加到对话历史
    conversationHistory.push({"role": "user", "content": userInput});

    // 清空输入框
    document.getElementById('user-input').value = '';

    // 发送请求并处理流式响应
    await fetchStreamingResponse(conversationHistory);
}

// 添加消息到聊天记录显示区域
function appendMessage(sender, message) {
    const chatHistory = document.getElementById('chat-history');

    // 创建消息容器
    const messageElement = document.createElement('div');
    messageElement.className = 'message';

    // 创建消息内容
    const senderElement = document.createElement('strong');
    senderElement.innerText = `${sender}: `;
    const contentElement = document.createElement('span');
    contentElement.innerText = message;

    // 组装消息元素
    messageElement.appendChild(senderElement);
    messageElement.appendChild(contentElement);

    // 添加到聊天记录
    chatHistory.appendChild(messageElement);

    // 滚动到底部
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// 处理流式响应
async function fetchStreamingResponse(messages) {
    // 构建请求体
    const requestBody = {
        model: modelName,
        messages: messages,
        temperature: 0.8, // 可根据需要调整
        stream: true,
        extra_body: {
            'repetition_penalty': 1,
            'stop_token_ids': [] // 如果有需要，可添加停止标记ID
        }
    };

    try {
        // 发送请求
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`, // 使用您的API密钥
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            console.error('响应错误', response.statusText);
            appendMessage('系统', '请求失败，请稍后重试。');
            return;
        }

        // 读取响应流
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let done = false;
        let assistantMessage = '';

        // 创建助手消息的占位符
        const assistantMessageElement = document.createElement('div');
        assistantMessageElement.className = 'message';
        const senderElement = document.createElement('strong');
        senderElement.innerText = '助手: ';
        const contentElement = document.createElement('span');
        contentElement.innerText = '';
        assistantMessageElement.appendChild(senderElement);
        assistantMessageElement.appendChild(contentElement);
        document.getElementById('chat-history').appendChild(assistantMessageElement);

        // 逐步读取数据流
        while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;
            if (value) {
                const chunkValue = decoder.decode(value, { stream: true });
                const lines = chunkValue.split('\n');

                // 处理每一行数据
                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (trimmedLine.startsWith('data: ')) {
                        const data = trimmedLine.slice('data: '.length);
                        if (data === '[DONE]') {
                            done = true;
                            break;
                        } else {
                            try {
                                const parsedData = JSON.parse(data);
                                const content = parsedData.choices[0].delta.content || '';
                                assistantMessage += content;

                                // 更新助手消息内容
                                contentElement.innerText = assistantMessage;
                            } catch (err) {
                                console.error('解析JSON错误:', err);
                            }
                        }
                    }
                }
            }
        }

        // 将助手消息添加到对话历史
        conversationHistory.push({"role": "assistant", "content": assistantMessage});

    } catch (error) {
        console.error('请求异常:', error);
        appendMessage('系统', '发生错误，请检查网络连接。');
    }
}
