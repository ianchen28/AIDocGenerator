# service/src/doc_agent/core/file_parser.py

from typing import Any, Literal, Optional

from doc_agent.core.logger import logger


def parse_context_files(
    context_files: list[dict[str, Any]],
    task_id: str,
    mode: Literal["outline", "document"] = "outline"
) -> tuple[list[str], list[str], list[str], Optional[str]]:
    """
    解析用户上传的context_files，提取各种类型的文件token
    
    Args:
        context_files: 上下文文件列表
        task_id: 任务ID
        mode: 解析模式，"outline" 或 "document"
        
    Returns:
        tuple: (user_data_reference_files, user_style_guide_content, user_requirements_content, user_outline_file)
        user_outline_file 只在 outline 模式下返回非空值
    """
    user_data_reference_files: list[str] = []
    user_style_guide_content: list[str] = []
    user_requirements_content: list[str] = []
    user_outline_file: Optional[str] = None

    if not context_files:
        logger.info(f"Task {task_id}: 没有context_files需要解析")
        return (user_data_reference_files, user_style_guide_content,
                user_requirements_content, user_outline_file)

    logger.info(f"Task {task_id}: 开始解析 {len(context_files)} 个context_files")

    for file in context_files:
        try:
            file_token = file.get("attachmentFileToken")
            if not file_token:
                logger.warning(
                    f"Task {task_id}: 文件缺少attachmentFileToken: {file}")
                continue

            if mode == "outline":
                # 大纲生成模式：使用 attachmentType 字段
                ocr_file_token = file.get("attachmentOCRResultToken")
                attachment_type = file.get("attachmentType")

                if attachment_type == 0:  # 用户上传大纲文件
                    user_outline_file = ocr_file_token if ocr_file_token else file_token
                elif attachment_type == 1:  # 数据参考文件
                    user_data_reference_files.append(file_token)
                elif attachment_type == 2:  # 样式指南
                    user_style_guide_content.append(file_token)
                elif attachment_type == 3:  # 需求文档
                    user_requirements_content.append(file_token)

            else:  # mode == "document"
                # 文档生成模式：使用布尔字段
                if file.get("isContentRefer") == 1:
                    user_data_reference_files.append(file_token)
                elif file.get("isStyleImitative") == 1:
                    user_style_guide_content.append(file_token)
                elif file.get("isWritingRequirement") == 1:
                    user_requirements_content.append(file_token)

        except Exception as e:
            logger.error(f"Task {task_id}: 解析文件失败: {e}")

    logger.info(
        f"Task {task_id}: 解析完成 - 数据参考文件: {len(user_data_reference_files)}, "
        f"样式指南: {len(user_style_guide_content)}, 需求文档: {len(user_requirements_content)}"
    )

    return (user_data_reference_files, user_style_guide_content,
            user_requirements_content, user_outline_file)


# 为了向后兼容，保留原有的函数名作为别名
def parse_context_files_outline(
        context_files: list[dict[str, Any]],
        task_id: str) -> tuple[list[str], list[str], list[str], str]:
    """解析用户上传的context_files，提取各种类型的文件token（大纲生成专用）"""
    result = parse_context_files(context_files, task_id, "outline")
    return result[0], result[1], result[2], result[3] or ""


def parse_context_files_document(
        context_files: list[dict],
        task_id: str) -> tuple[list[str], list[str], list[str]]:
    """解析用户上传的context_files，提取各种类型的文件token（文档生成专用）"""
    result = parse_context_files(context_files, task_id, "document")
    return result[0], result[1], result[2]
