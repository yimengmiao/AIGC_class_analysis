from pathlib import Path

from openai import OpenAI


class ModelAPI:
    def __init__(self, params):
        self.model_family = params.get('model_family', '').lower()
        if not self.model_family:
            raise ValueError("Parameter 'model_family' is required.")

        self.api_key = params.get('api_key')
        if not self.api_key:
            raise ValueError("Parameter 'api_key' is required.")

        self.base_url = params.get('base_url') or self._get_base_url()
        self.api_version = params.get('api_version', "")
        self.text = params.get('text', '')
        self.prompt = params.get('prompt', '')
        self.model = params.get('model_name')
        if not self.model:
            raise ValueError("Parameter 'model' is required.")

        self.max_tokens = params.get('max_tokens', 1000)
        self.n = params.get('n', 1)
        self.temperature = params.get('temperature', 0.7)
        self.use_files = params.get('use_files', False)
        self.files = params.get('files', [])
        self.stream = params.get('stream', False)  # 默认不开启流式输出
        self.client = self._get_client()

    def _get_base_url(self):
        if self.model_family == "glm-4":
            return "https://open.bigmodel.cn/api/paas/v4/"
        elif self.model_family == "gpt4o":
            return "https://zonekey-gpt4o.openai.azure.com/"
        elif self.model_family.startswith("qwen"):
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        elif self.model_family.startswith("local"):
            return "https://u515714-acba-8e1c52b3.bjb1.seetacloud.com:8443/v1"
        else:
            raise ValueError(f"Unsupported model family: {self.model_family}")

    def _get_client(self):
        if self.model_family == "glm-4" or self.model_family.startswith("qwen") or self.model_family.startswith(
                "local"):
            return OpenAI(api_key=self.api_key, base_url=self.base_url)
        elif self.model_family == "gpt4o":
            from openai import AzureOpenAI
            return AzureOpenAI(api_key=self.api_key, azure_endpoint=self.base_url, api_version=self.api_version)
        else:
            raise ValueError(f"Unsupported model family: {self.model_family}")

    def analyze_text(self):
        user_input = self.prompt + self.text
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "你是一个乐于助人的小助手"},
                {"role": "user", "content": user_input}
            ],
            max_tokens=self.max_tokens,
            n=self.n,
            temperature=self.temperature,
            stream=self.stream  # 使用实例化时的 stream 参数
        )
        if self.stream:
            return self._stream_response(response)
        else:
            return response.choices[0].message.content

    def analyze_with_files(self, prompt, files):
        file_ids = []
        for file_path in files:
            if Path(file_path).exists():
                file_object = self.client.files.create(file=Path(file_path), purpose="file-extract")
                file_ids.append(f'fileid://{file_object.id}')

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': ','.join(file_ids)},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens,
            n=self.n,
            temperature=self.temperature,
            stream=self.stream  # 使用实例化时的 stream 参数

        )
        if self.stream:

            return self._stream_response(completion)
        else:
            return completion.choices[0].message.content

    def _stream_response(self, response):

        for chunk in response:  # 逐块接收数据
            if hasattr(chunk, 'choices'):
                # 获取 delta 的 content 属性内容
                delta = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                print(delta, end="", flush=True)  # 实时打印输出
            print()  # 输出结束后换行

    def analyze(self):
        if self.use_files and self.files:
            return self.analyze_with_files(self.prompt, self.files)
        else:
            return self.analyze_text()


if __name__ == '__main__':
    # 测试非流式输出
    params = {
        "model_family": "qwen",
        "api_key": "your_api_key_here",
        "prompt": "你的提示文本",
        "model_name": "qwen-long",
        "max_tokens": 1000,
        "n": 1,
        "temperature": 0.7,
        "use_files": False,
        "text": "这里是非流式输出的示例文本。",
        "stream": False  # 不使用流式输出
    }

    model_api = ModelAPI(params)
    result = model_api.analyze()
    print("非流式输出结果:", result)

    # 测试流式输出
    params["stream"] = True  # 启用流式输出
    params["text"] = "这里是流式输出的示例文本。"
    model_api = ModelAPI(params)
    result = model_api.analyze()
    print("流式输出最终结果:", result)
