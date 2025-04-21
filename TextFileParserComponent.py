    def load_files(self) -> list[Data]:
        """返回Data对象列表，每个章节对应一个Data对象"""
        if not isinstance(self.message, Message) or not self.message.files:
            raise ValueError("需要包含文件的Message对象")
        
        file_path = self.message.files[0]
        data, content = self._process_file(file_path)
        
        # 创建Data对象列表，每个章节一个Data对象
        data_objects = []
        for chapter in data:
            data_objects.append(Data(
                data={
                    "text": chapter,  # 单个章节的数据
                    "type": "text",
                    "name": f"{Path(file_path).stem}_{chapter['chapter']}",  # 为每个章节创建唯一名称
                    "size": len(chapter['content']),
                    "dataframe": [chapter],  # 单个章节的数据作为列表
                    "chapters": 1,  # 每个Data对象只包含一个章节
                    "path": str(file_path)
                }
            ))
        
        return data_objects 