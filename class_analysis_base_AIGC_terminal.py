import os
import time
import argparse
from model_api_handler import ModelAPI


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description="基于AIGC的课堂分析任务")

    # 添加命令行参数
    parser.add_argument('--grade', type=int, required=True, help='年级')
    parser.add_argument('--subject', type=str, required=True, help='学科名称')
    parser.add_argument('--task', type=str, required=True, help='任务描述')
    parser.add_argument('--analysis_text', type=str, required=True, help='待分析文本')
    parser.add_argument('--use_files', type=bool, default=True, help='是否使用文件方式处理（默认为True）')

    return parser.parse_args()


def main(grade, subject, task, analysis_text, use_files=True):
    start_time = time.time()

    # 根据task找到对应的class_stand_text_file_path和bc_knowledge_file_paths
    prompt_file_path = os.path.join("基于AIGC的课堂分析（zonkey版本）", "prompt", f"{task}.txt")

    if task == "教学效果":
        bc_knowledge_file_paths = [item for item in os.listdir("基于AIGC的课堂分析（zonkey版本）/模型知识")]  # 所有文件名拼接
    else:
        bc_knowledge_file_paths = [os.path.join("基于AIGC的课堂分析（zonkey版本）", "模型知识", f"{task}.txt")]

    # 根据subject找到class_stand_text_file_path
    for item in os.listdir("基于AIGC的课堂分析（zonkey版本）/课程标准"):
        if subject in item:
            class_stand_text_file_path = os.path.join("基于AIGC的课堂分析（zonkey版本）", "课程标准", item)
            break

    prompt_file_path_new = "prompt_text.txt"
    with open(prompt_file_path_new, "w", encoding="utf-8") as f:
        # 根据grade和subject拼接成一句话：“这是一节{grade}的{subject}课” ,把这句子放到prompt中的开头
        with open(prompt_file_path, "r", encoding="utf-8") as f1:
            prompt_text = f"这是一节{grade}年级的{subject}课，" + "\n" + f1.read()
        f.write(prompt_text)

    # 保存分析文本
    analysis_data_file_path = "analysis_data.txt"
    with open(analysis_data_file_path, "w", encoding="utf-8") as f2:
        f2.write(analysis_text)

    if use_files:
        files = [analysis_data_file_path, class_stand_text_file_path] + bc_knowledge_file_paths

        params = {
            "model_family": "qwen",
            "api_key": "sk-454416d3aac549cd9bf043aa9fa2f158",  # 请替换为您的实际 API 密钥
            "prompt": prompt_text,
            "model_name": "qwen-long",  # Example model, can be changed
            "max_tokens": 1000,
            "n": 1,
            "temperature": 0.7,
            "use_files": True,
            "files": files
        }

        # 创建 ModelAPI 实例并进行分析
        model_api = ModelAPI(params)
        result = model_api.analyze()
        print("Result:", result)

        end_time = time.time()
        print("Time used:", end_time - start_time)
        return result

    else:
        params = {
            "model_family": "local",
            "api_key": "token123",  # 请替换为您的实际 API 密钥
            "prompt_file_path": prompt_file_path,
            "analysis_data_file_path": analysis_data_file_path,
            "class_stand_text_file_path": class_stand_text_file_path,
            "bc_knowledge_file_paths": bc_knowledge_file_paths,
            "model_name": "qwen2_5-32b-instruct",
            "max_tokens": 2000,
            "n": 1,
            "temperature": 0.7,
            "use_files": False,
        }

        # 调用 get_result 函数获取最终结果
        result = get_result(params)
        return result


def construct_prompt(prompt_file_path, analysis_data_file_path, class_stand_text_file_path, bc_knowledge_file_paths):
    """
    构造完整的 prompt 文本
    """
    # 读取 prompt 文件内容（无需前缀）
    with open(prompt_file_path, "r", encoding='utf-8') as f:
        prompt_content = f.read()

    # 读取待分析文本，并添加前缀
    analysis_filename = os.path.basename(analysis_data_file_path)
    analysis_data_prefix = f"{{{analysis_filename}}}的内容如下："
    with open(analysis_data_file_path, "r", encoding='utf-8') as f:
        analysis_data_content = analysis_data_prefix + f.read()

    # 读取课程标准文本，并添加前缀
    class_stand_prefix = "{新课标内容如下}："
    with open(class_stand_text_file_path, "r", encoding='utf-8') as f:
        class_stand_content = class_stand_prefix + f.read()

    # 读取背景知识文件，并添加前缀
    bc_knowledge_contents = ''
    for bc_file_path in bc_knowledge_file_paths:
        bc_filename = os.path.basename(bc_file_path)
        bc_prefix = f"{{{bc_filename}}}内容如下："
        with open(bc_file_path, "r", encoding='utf-8') as f:
            bc_content = bc_prefix + f.read()
        bc_knowledge_contents += bc_content

    # 按指定顺序组合所有内容
    full_prompt = prompt_content + analysis_data_content + class_stand_content + bc_knowledge_contents
    print("输入文本的个数：", len(full_prompt))
    return full_prompt


def get_result(params):
    """
    获取最终分析结果
    """
    # 使用 construct_prompt 函数生成 prompt 文本
    text = construct_prompt(
        prompt_file_path=params["prompt_file_path"],
        analysis_data_file_path=params["analysis_data_file_path"],
        class_stand_text_file_path=params["class_stand_text_file_path"],
        bc_knowledge_file_paths=params["bc_knowledge_file_paths"]
    )

    # 将生成的 prompt 文本添加到 params 中
    params["prompt"] = text  # 这里是把合成的 prompt 文本放到参数中

    # 创建 ModelAPI 实例并进行分析
    model_api = ModelAPI(params)
    result = model_api.analyze()
    return result


if __name__ == '__main__':
    # 解析命令行参数
    args = parse_args()

    # 调用 main 函数，传入命令行参数
    main(args.grade, args.subject, args.task, args.analysis_text, args.use_files)
#python test1.py --grade 2 --subject "语文" --task "教学效果" --analysis_text """老师：请袁艺开始你啊上课，声音要响亮啊，同学们好，请坐真棒。昨天呀，我们一起学习了课文八。老师：今天小猴子呀要到我们班来做客了，我们来跟他打打招呼，猴子猴子，昨天在写作业的时候呀，小朋友要注意哦，这个猴，反犬旁，旁边是一个单立人，中间有没有一个短竖啊？老师：那么昨天在作业当中，方老师看到有人加了一竖，那就不对了，变成错别字了，明白了吗？好，现在用眼睛看，用心记住这个字，猴猴猴子。老师：每天通过学习啊，我们知道了这个猴子啊，种了一些果树，它分别种了什么树呢？谁来说说，于凯，你来说说看。学生：嗯，好的。""" --use_files False

