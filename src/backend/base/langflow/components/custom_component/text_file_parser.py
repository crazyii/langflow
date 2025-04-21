from typing import Dict, Any, Union
import pandas as pd
from pathlib import Path
from langflow.custom.custom_component.component import Component
from langflow.inputs.inputs import FileInput, StrInput

class TextFileParserComponent(Component):
    display_name: str = "Text File Parser"
    description: str = "Parse text file into DataFrame with chapter, title and content columns"
    icon: str = "📄"
    
    def __init__(self, _code: str = None, _user_id: str = None) -> None:
        super().__init__(_code=_code, _user_id=_user_id)
    
    def build_config(self):
        return {
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

    def build(self, file_path: str, delimiter: str = "----") -> Dict[str, Any]:
        """Build the component."""
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