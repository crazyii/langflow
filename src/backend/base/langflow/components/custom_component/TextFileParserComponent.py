from typing import Dict, Any, List
import pandas as pd
from pathlib import Path
import json
from langflow.custom import Component
from langflow.template import Input, Output
from langflow.field_typing import Text
from langflow.schema.message import Message
from langflow.schema.data import Data
from langflow.schema.dataframe import DataFrame
from langflow.base.data.utils import parse_text_file_to_data

class TextFileParserComponent(Component):
    display_name = "文本文件解析器"
    description = "从聊天输入消息中解析文本文件，并转换为带有章节、标题和内容列的DataFrame"
    documentation = "https://docs.langflow.org/components/custom"
    icon = "📄"

    inputs = [
        Input(
            name="message",
            display_name="聊天消息",
            field_type="str",
            required=True,
            info="从Chat Input接收的包含文件的消息",
            input_types=["Message"]
        ),
        Input(
            name="delimiter",
            display_name="分隔符",
            field_type="str",
            required=False,
            default="----",
            placeholder="输入分隔符",
            info="用于分割文本段落的分隔符（默认: ----）",
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="load_files"),
        Output(display_name="DataFrame", name="dataframe", method="load_dataframe"),
        Output(display_name="Message", name="message2", method="load_message"),
    ]

    def _process_file(self, file_path: str) -> tuple[list[Dict], str]:
        """处理单个文件并返回数据和内容"""
        import pdb; pdb.set_trace() # 进入调试模式

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = content.split(self.delimiter)
        data = []
        for i, section in enumerate(sections, 1):
            if not section.strip():
                continue
                
            lines = section.strip().split("\n")
            title = next((line.strip() for line in lines if line.strip()), "")
            section_content = "\n".join(line.strip() for line in lines[1:] if line.strip())
            
            data.append({
                "chapter": f"第{i}章",
                "title": title,
                "content": section_content
            })
        
        return data, content

    def load_files(self) -> list[Data]:
        """返回Data对象列表，每个章节对应一个Data对象"""
        import pdb; pdb.set_trace() # 进入调试模式

        if not isinstance(self.message, Message) or not self.message.files:
            raise ValueError("需要包含文件的Message对象")
        
        file_path = self.message.files[0]
        data, content = self._process_file(file_path)
        
        # 创建Data对象列表，每个章节一个Data对象
        data_objects = []
        for chapter in data:
            # 直接使用字符串作为text属性，而不是字典
            data_object = Data(text=json.dumps(chapter, ensure_ascii=False))
            # 添加其他元数据作为data属性
            data_object.data = {
                "type": "text",
                "name": f"{Path(file_path).stem}_{chapter['chapter']}",
                "size": len(chapter['content']),
                "dataframe": [chapter],
                "chapters": 1,
                "content": chapter['content'],
                "path": str(file_path)
            }
            data_objects.append(data_object)
        
        return data_objects

    def load_dataframe(self) -> DataFrame:
        """返回DataFrame对象"""
        import pdb; pdb.set_trace() # 进入调试模式

        if not isinstance(self.message, Message) or not self.message.files:
            raise ValueError("需要包含文件的Message对象")
        
        file_path = self.message.files[0]
        data, _ = self._process_file(file_path)
        
        return DataFrame(data)

    def load_message(self) -> Message:
        import pdb; pdb.set_trace() # 进入调试模式

        """返回Message对象"""
        if not isinstance(self.message, Message) or not self.message.files:
            raise ValueError("需要包含文件的Message对象")
        
        file_path = self.message.files[0]
        data, content = self._process_file(file_path)
        
        return Message(
            content=f"成功处理文件 {Path(file_path).name}，共 {len(data)} 个章节",
            type="text",
            additional_kwargs={
                "file_path": str(file_path),
                "total_chapters": len(data),
                "total_size": len(content),
                "dataframe": data
            }
        )