from typing import Dict, Any, Union
import pandas as pd
from pathlib import Path
from langflow.custom import CustomComponent
from langflow.interface.tools.constants import FILE_TOOLS_TYPE
from langflow.inputs import FileInput, StrInput

class TextFileParserComponent(CustomComponent):
    display_name: str = "Text File Parser"
    description: str = "Parse text file into DataFrame with chapter, title and content columns"
    icon: str = "📄"
    
    def __init__(self):
        super().__init__()
        self.input_keys = ["file_path", "delimiter"]
        self.output_keys = ["dataframe"]
        
        self.inputs = {
            "file_path": FileInput(
                display_name="File Path",
                description="Path to the text file to parse (supports .txt files)",
                required=True,
                file_types=[".txt"],
            ),
            "delimiter": StrInput(
                display_name="Delimiter",
                description="Delimiter to split text sections (default: ----)",
                default="----",
                required=False,
            ),
        }
        
        self.outputs = {
            "dataframe": {
                "type": "DataFrame",
                "description": "DataFrame containing parsed text data with columns: chapter, title, content",
            }
        }

    def build(self) -> Dict[str, Any]:
        """Build the component."""
        file_path = self.get_input("file_path")
        delimiter = self.get_input("delimiter")
        
        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Split content by delimiter
        sections = content.split(delimiter)
        
        # Process each section
        data = []
        for i, section in enumerate(sections, 1):
            if not section.strip():
                continue
                
            # Split section into lines
            lines = section.strip().split("\n")
            
            # Extract title from first non-empty line
            title = next((line.strip() for line in lines if line.strip()), "")
            
            # Join remaining lines as content
            content = "\n".join(line.strip() for line in lines[1:] if line.strip())
            
            data.append({
                "chapter": f"Chapter {i}",
                "title": title,
                "content": content
            })
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        return {"dataframe": df} 