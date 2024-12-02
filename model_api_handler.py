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
        self.client = self._get_client()

    def _get_base_url(self):
        if self.model_family == "glm-4":
            return "https://open.bigmodel.cn/api/paas/v4/"
        elif self.model_family == "gpt4o":
            return "https://zonekey-gpt4o.openai.azure.com/"
        elif self.model_family.startswith("qwen"):
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        elif self.model_family.startswith("local"):
            return "https://u515714-acba-8e1c52b3.bjb1.seetacloud.com:8443/v1"  # todo:当前这里是autodl.com部署的接口，未来如有自己的部署接口，更改为自己的url。
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
        user_input = self.prompt + self.text #这里是方便gpt4o的模型，需要把prompt和text拼接起来作为输入。
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
        )
        return response.choices[0].message.content

    def analyze_with_files(self, prompt, files):
        # 上传文件并返回文件 ID 列表
        file_ids = []
        for file_path in files:
            if Path(file_path).exists():
                file_object = self.client.files.create(file=Path(file_path), purpose="file-extract")
                file_ids.append(f'fileid://{file_object.id}')

        # 创建模型对话请求，结合文件 ID 和文本 prompt 将其一一对应起来
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': ','.join(file_ids)},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens,
            n=self.n,
            temperature=self.temperature,
        )
        return completion.choices[0].message.content

    def analyze(self):
        if self.use_files and self.files:
            return self.analyze_with_files(self.prompt, self.files)
        else:
            return self.analyze_text()


if __name__ == '__main__':
    # 定义参数
    params = {
        "model_family": "qwen",
        "api_key": "your_api_key_here",
        "prompt": "你的提示文本",
        "model_name": "qwen-long",  # Example model, can be changed
        "max_tokens": 1000,
        "n": 1,
        "temperature": 0.7,
        "use_files": True,
        "files": ["file1.txt", "file2.txt"]
    }

    # 创建 ModelAPI 实例并调用方法
    model_api = ModelAPI(params)
    result = model_api.analyze()
    print("Result:", result)

    # 定义参数，不使用文件，只进行文本分析
    params = {
        "model_family": "qwen",
        "api_key": "your_api_key_here",
        "prompt": "你的提示文本",
        "text": "这里是你想分析的文本内容",
        "model_name": "qwen-long",  # Example model, can be changed
        "max_tokens": 1000,
        "n": 1,
        "temperature": 0.7,
        "use_files": False  # 或者可以直接省略这个参数
    }

    # 创建 ModelAPI 实例并调用方法
    model_api = ModelAPI(params)
    result = model_api.analyze()
    print("Result:", result)
