from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import toml  # type: ignore[import-untyped]
from loguru import logger

from langflow.custom import Component
from langflow.io import BoolInput, DataFrameInput, HandleInput, MessageTextInput, MultilineInput, Output
from langflow.schema import DataFrame

if TYPE_CHECKING:
    from langchain_core.runnables import Runnable


class BatchRunComponent(Component):
    """
    批量处理组件，用于对数据框中的数据进行批量处理
    主要功能：对数据框的每一行应用语言模型，并收集处理结果
    """
    display_name = "Batch Run"  # 组件显示名称
    description = "Runs an LLM over each row of a DataFrame's column. If no column is set, the entire row is passed."  # 组件描述
    icon = "List"  # 组件图标
    beta = True  # 标记为测试版

    # 定义组件的输入参数
    inputs = [
        # 语言模型输入
        HandleInput(
            name="model",
            display_name="Language Model",
            info="Connect the 'Language Model' output from your LLM component here.",
            input_types=["LanguageModel"],
            required=True,
        ),
        # 系统消息输入
        MultilineInput(
            name="system_message",
            display_name="Instructions",
            info="Multi-line system instruction for all rows in the DataFrame.",
            required=False,
        ),
        # 数据框输入
        DataFrameInput(
            name="df",
            display_name="DataFrame",
            info="The DataFrame whose column (specified by 'column_name') we'll treat as text messages.",
            required=True,
        ),
        # 列名输入
        MessageTextInput(
            name="column_name",
            display_name="Column Name",
            info=(
                "The name of the DataFrame column to treat as text messages. "
                "If empty, all columns will be formatted in TOML."
            ),
            required=False,
            advanced=False,
        ),
        # 输出列名输入
        MessageTextInput(
            name="output_column_name",
            display_name="Output Column Name",
            info="Name of the column where the model's response will be stored.",
            value="model_response",
            required=False,
            advanced=True,
        ),
        # 元数据开关
        BoolInput(
            name="enable_metadata",
            display_name="Enable Metadata",
            info="If True, add metadata to the output DataFrame.",
            value=False,
            required=False,
            advanced=True,
        ),
    ]

    # 定义组件的输出
    outputs = [
        Output(
            display_name="DataFrame",
            name="batch_results",
            method="run_batch",
            info="A DataFrame with all original columns plus the model's response column.",
        ),
    ]

    def _format_row_as_toml(self, row: dict[str, Any]) -> str:
        """
        将数据行转换为TOML格式的字符串
        
        Args:
            row: 包含列名和值的字典
            
        Returns:
            str: TOML格式的字符串
        """
        formatted_dict = {str(col): {"value": str(val)} for col, val in row.items()}
        return toml.dumps(formatted_dict)

    def _create_base_row(
        self, original_row: dict[str, Any], model_response: str = "", batch_index: int = -1
    ) -> dict[str, Any]:
        """
        创建基础行数据，包含原始列和模型响应
        
        Args:
            original_row: 原始行数据
            model_response: 模型响应文本
            batch_index: 批次索引
            
        Returns:
            dict: 包含原始数据和模型响应的新行
        """
        row = original_row.copy()
        row[self.output_column_name] = model_response
        row["batch_index"] = batch_index
        return row

    def _add_metadata(
        self, row: dict[str, Any], *, success: bool = True, system_msg: str = "", error: str | None = None
    ) -> None:
        """
        为行数据添加元数据信息
        
        Args:
            row: 要添加元数据的行
            success: 处理是否成功
            system_msg: 系统消息
            error: 错误信息（如果有）
        """
        if not self.enable_metadata:
            return

        if success:
            row["metadata"] = {
                "has_system_message": bool(system_msg),
                "input_length": len(row.get("text_input", "")),
                "response_length": len(row[self.output_column_name]),
                "processing_status": "success",
            }
        else:
            row["metadata"] = {
                "error": error,
                "processing_status": "failed",
            }

    async def run_batch(self) -> DataFrame:
        """
        批量处理数据框中的每一行数据
        
        Returns:
            DataFrame: 包含处理结果的新数据框
            
        Raises:
            ValueError: 当指定的列不存在时
            TypeError: 当输入类型不正确时
        """
        model: Runnable = self.model
        system_msg = self.system_message or ""
        df: DataFrame = self.df
        col_name = self.column_name or ""

        # 验证输入数据
        if not isinstance(df, DataFrame):
            msg = f"Expected DataFrame input, got {type(df)}"
            raise TypeError(msg)

        if col_name and col_name not in df.columns:
            msg = f"Column '{col_name}' not found in the DataFrame. Available columns: {', '.join(df.columns)}"
            raise ValueError(msg)

        try:
            # 准备要处理的文本数据
            if col_name:
                user_texts = df[col_name].astype(str).tolist()
            else:
                user_texts = [
                    self._format_row_as_toml(cast(dict[str, Any], row)) for row in df.to_dict(orient="records")
                ]

            total_rows = len(user_texts)
            logger.info(f"Processing {total_rows} rows with batch run")

            # 准备对话数据
            conversations = [
                [{"role": "system", "content": system_msg}, {"role": "user", "content": text}]
                if system_msg
                else [{"role": "user", "content": text}]
                for text in user_texts
            ]

            # 配置模型
            model = model.with_config(
                {
                    "run_name": self.display_name,
                    "project_name": self.get_project_name(),
                    "callbacks": self.get_langchain_callbacks(),
                }
            )

            # 处理数据并跟踪进度
            responses_with_idx = list(
                zip(
                    range(len(conversations)),
                    await model.abatch(list(conversations)),
                    strict=True,
                )
            )

            # 按索引排序以保持顺序
            responses_with_idx.sort(key=lambda x: x[0])

            # 构建最终结果
            rows: list[dict[str, Any]] = []
            for idx, (original_row, response) in enumerate(
                zip(df.to_dict(orient="records"), responses_with_idx, strict=False)
            ):
                response_text = response[1].content if hasattr(response[1], "content") else str(response[1])
                row = self._create_base_row(
                    cast(dict[str, Any], original_row), model_response=response_text, batch_index=idx
                )
                self._add_metadata(row, success=True, system_msg=system_msg)
                rows.append(row)

                # 记录进度
                if (idx + 1) % max(1, total_rows // 10) == 0:
                    logger.info(f"Processed {idx + 1}/{total_rows} rows")

            logger.info("Batch processing completed successfully")
            return DataFrame(rows)

        except (KeyError, AttributeError) as e:
            # 处理错误情况
            logger.error(f"Data processing error: {e!s}")
            error_row = self._create_base_row({col: "" for col in df.columns}, model_response="", batch_index=-1)
            self._add_metadata(error_row, success=False, error=str(e))
            return DataFrame([error_row])
