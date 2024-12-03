import argparse  # 导入 argparse 模块
import os
import time

from model_api_test import ModelAPI
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class ClassroomAnalysis:
    def __init__(self, grade, subject, task, analysis_text):
        self.grade = grade
        self.subject = subject
        self.task = task
        self.analysis_text = "##分析对象\n1. {analysis_data.txt}是本节课的课堂文本信息，内容如下：\"" + analysis_text + "\"。"

    def run(self):
        start_time = time.time()

        prompt_file_path = os.path.join("基于AIGC的课堂分析（zonkey版本）", "prompt", f"{self.task}.txt")

        if self.task == "教学效果":
            bc_knowledge_file_paths = [os.path.join("基于AIGC的课堂分析（zonkey版本）", "模型知识", item) for item in
                                       os.listdir("基于AIGC的课堂分析（zonkey版本）/模型知识")]
            # 把四个背景知识的文件都拼接成一个string。
            # 教学方法.txt内容如下：
            teaching_method = f"2.{{ 教学方法.txt }}是与老师的“教学方法“相关的背景知识，内容如下: \"{open(bc_knowledge_file_paths[1], 'r', encoding='utf-8').read()}\"。" + "\n"
            # 课堂活动.txt内容如下：
            class_activity = f"3.{{ 课堂活动.txt }}是与老师在课堂上“课堂活动”的背景知识，从教学活动设计和学习活动两个维度进行描述，内容如下: \"{open(bc_knowledge_file_paths[2], 'r', encoding='utf-8').read()}\"。" + "\n"
            # 问答行为.txt内容如下：
            qa_behavior = f"4.{{ 问答行为.txt }}是与老师在课堂和学生之间“问答行为”相关的背景知识，从老师提问方式、学生回答方式、学生回答内容、老师理答方式、解决问题途径五个维度进行描述，内容如下: \"{open(bc_knowledge_file_paths[3], 'r', encoding='utf-8').read()}\"。" + "\n"
            # 教学效果.txt内容如下：
            teaching_effectiveness = f"5.{{ 教学效果.txt }}是教学效果相关的背景知识，内容如下: \"{open(bc_knowledge_file_paths[0], 'r', encoding='utf-8').read()}\"。" + "\n"
            bc_knowledge_content = teaching_effectiveness + teaching_method + class_activity + qa_behavior


        else:
            bc_knowledge_file_paths = [os.path.join("基于AIGC的课堂分析（zonkey版本）", "模型知识", f"{self.task}.txt")]
            with open(bc_knowledge_file_paths[0], "r", encoding='utf-8') as f:
                bc_knowledge_content = f"2. {{ {self.task}.txt }}描述了课堂中老师采用的教学方法的类别，内容如下: \"{f.read()}\"。"
            # todo:根据传入的{task}来分别对应模型知识的输出开头
        for item in os.listdir("基于AIGC的课堂分析（zonkey版本）/课程标准"):
            if self.subject in item:
                class_stand_text_file_path = os.path.join("基于AIGC的课堂分析（zonkey版本）", "课程标准", item)
                break
        # 课程标准文件内容读取出来
        with open(class_stand_text_file_path, "r", encoding='utf-8') as f:
            class_stand_content = f"""## 参考材料
            1. 课程标准.txt是本节课对应的课程标准，以下简称新课标，内容如下："{f.read()}"。"""

        prompt_file_path_new = "prompt_text.txt"
        with open(prompt_file_path_new, "w", encoding="utf-8") as f:
            with open(prompt_file_path, "r", encoding="utf-8") as f1:
                prompt_text = (f"这是一节{self.grade}年级的{self.subject}课。"
                               "你是一名教研员，擅长结合本节课对应学科的教育专业知识进行课例分析，"
                               "熟悉本节课对应学段、对应单元的课程标准，并能为老师的教学改进提出建设性意见。"
                               "按照下面描述的“参考资料”、“任务目标”和“执行步骤“对本节课的课堂文本{analysis_data.txt}进行分析，"
                               "并按照“输出要求”进行输出。") + "\n" + self.analysis_text + "\n" + bc_knowledge_content + "\n" + class_stand_content + "\n" + f1.read()
            f.write(prompt_text)

        # 调用模型API
        params = {
            "model_family": "qwen",
            "api_key": "sk-5610104583194c8890374e424114eff4",
            "prompt": "请根据我上传文件中的内容进行分析",
            "text": "",
            "model_name": "qwen-long",  # Example model, can be changed
            "max_tokens": 2000,
            "n": 1,
            "temperature": 0.7,
            "files": [prompt_file_path_new],
            "use_files": True,  # 或者可以直接省略这个参数
            "stream": True
        }

        # 创建 ModelAPI 实例并调用方法
        model_api = ModelAPI(params)
        result = model_api.analyze()

        end_time = time.time()
        print("Time used:", end_time - start_time)
        # todo:对返回结果result提取JOSN格式
        return result


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Classroom Analysis Program")

    parser.add_argument('--grade', type=str, required=True, help="年级")
    parser.add_argument('--subject', type=str, required=True, help="学科")
    parser.add_argument('--task', type=str, required=True, help="任务类型")
    parser.add_argument('--analysis_text', type=str, required=True, help="分析文本内容")

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    # 解析命令行参数
    args = parse_args()

    # 创建 ClassroomAnalysis 实例并运行分析
    analysis = ClassroomAnalysis(
        grade=args.grade,
        subject=args.subject,
        task=args.task,
        analysis_text=args.analysis_text,

    )
    result = analysis.run()

    print("Result:", result)
# python test1.py --grade 2 --subject "语文" --task "教学效果" --analysis_text """老师：请袁艺开始你啊上课，声音要响亮啊，同学们好，请坐真棒。昨天呀，我们一起学习了课文八。老师：今天小猴子呀要到我们班来做客了，我们来跟他打打招呼，猴子猴子，昨天在写作业的时候呀，小朋友要注意哦，这个猴，反犬旁，旁边是一个单立人，中间有没有一个短竖啊？老师：那么昨天在作业当中，方老师看到有人加了一竖，那就不对了，变成错别字了，明白了吗？好，现在用眼睛看，用心记住这个字，猴猴猴子。老师：每天通过学习啊，我们知道了这个猴子啊，种了一些果树，它分别种了什么树呢？谁来说说，于凯，你来说说看。学生：嗯，好的。"""
