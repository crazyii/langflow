from loguru import logger
import json
from typing import Dict, Any, List
from langflow.custom import Component
from langflow.io import MessageInput, Output
from langflow.schema import Data
from langflow.schema.message import Message


class MessageToListDataComponent(Component):
    display_name = "Message to List<Data>"
    description = "从Message的text字段中提取JSON中的chapters并转换为Data对象列表"
    icon = "message-square-share"
    name = "MessagetoData"

    inputs = [
        MessageInput(
            name="message",
            display_name="Message",
            info="包含chapters数据的Message对象",
        ),
    ]

    outputs = [
        Output(display_name="List<Data>", name="fdata", method="convert_message_to_data_list"),
    ]

    def convert_message_to_data_list(self) -> list[Data]:
        if not isinstance(self.message, Message):
            logger.error("输入不是Message对象")
            return []
        
        # 获取Message的text字段
        message_text = ""
        if hasattr(self.message, "text") and self.message.text:
            message_text = self.message.text
        else:
            logger.warning("Message没有text内容")
            return []
        
        # 从文本中提取JSON字符串
        # 根据日志可知text中的JSON是包含在```json和```之间的
        try:
            # 提取JSON部分
            if "```json" in message_text and "```" in message_text:
                json_text = message_text.split("```json")[1].split("```")[0].strip()
            else:
                json_text = message_text
                
            # 解析JSON
            parsed_data = json.loads(json_text)
            
            # 获取chapters数组
            if "chapters" not in parsed_data:
                logger.warning(f"解析的JSON中不包含'chapters'字段，可用键: {parsed_data.keys()}")
                return []
                
            chapters = parsed_data["chapters"]
            
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            return []
        
        # 验证chapters是列表
        if not isinstance(chapters, list):
            logger.error(f"chapters不是列表。类型: {type(chapters)}")
            return []
            
        # 转换每个chapter为Data对象
        processed_chapters = list()
        for chapter in chapters:
            articles = chapter.get("articles", [])
            for article in articles:
                # 提取章节的关键信息
                article_data = {
                    "chapter_title": chapter.get("chapterTitle", ""),
                    "chapter_number": chapter.get("chapter_number", ""),
                    "articleNumber": chapter.get("articleNumber", ""),
                    "articleTitle": article.get("articleTitle", ""),
                    "articleContent": article.get("articleContent", "")
                }
                
                # 创建Data对象
                data_obj = Data(data=article_data)
                processed_chapters.append(data_obj)

        return processed_chapters