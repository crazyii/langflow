from typing import Dict, Any
import pandas as pd
from pathlib import Path
from langflow.custom import Component
from langflow.template import Input, Output
from langflow.field_typing import Text, DataFrame

class TextFileParserComponent(Component):
    display_name = "Text File Parser"
    description = "Parse text file into DataFrame with chapter, title and content columns"
    documentation = "https://docs.langflow.org/components/custom"
    icon = "📄"

    inputs = [
        Input(
            name="file_path",
            display_name="File Path",
            field_type="file",
            required=True,
            placeholder="Input your file path",
            file_types=[".txt"],
            info="Path to the text file to parse (supports .txt files)",
        ),
        Input(
            name="delimiter",
            display_name="Delimiter",
            field_type="str",
            required=False,
            default="----",
            placeholder="Enter delimiter",
            info="Delimiter to split text sections (default: ----)",
        ),
    ]

    outputs = [
        Output(
            display_name="DataFrame",
            name="dataframe",
            method="process_file",
        ),
    ]

    def process_file(self) -> DataFrame:
        """Process the text file and return a DataFrame."""
        # Read the file content
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Split content by delimiter
        sections = content.split(self.delimiter)
        
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
        
        # Update component status
        self.status = f"Processed {len(data)} chapters"
        
        return df