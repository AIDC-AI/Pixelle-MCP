# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import requests
import tempfile
import os
import mimetypes
from contextlib import contextmanager
from typing import Generator, List, Union, overload
from core import logger
from utils.os_util import get_data_path


TEMP_DIR = get_data_path("temp")
os.makedirs(TEMP_DIR, exist_ok=True)


@overload
def download_files(file_urls: str, suffix: str = None, auto_cleanup: bool = True, cookies: dict = None) -> Generator[str, None, None]:
    ...


@overload
def download_files(file_urls: List[str], suffix: str = None, auto_cleanup: bool = True, cookies: dict = None) -> Generator[List[str], None, None]:
    ...


@contextmanager
def download_files(file_urls: Union[str, List[str]], suffix: str = None, auto_cleanup: bool = True, cookies: dict = None) -> Generator[Union[str, List[str]], None, None]:
    """
    从 URL 下载文件到临时文件的上下文管理器
    
    Args:
        file_urls: 单个 URL 字符串或 URL 列表
        suffix: 临时文件后缀名，如果不指定则尝试从 URL 推断
        auto_cleanup: 是否自动清理临时文件，默认为 True
        cookies: 请求时使用的 cookies，默认为 None
        
    Yields:
        str: 如果输入是 str，返回临时文件路径
        List[str]: 如果输入是 List[str]，返回临时文件路径列表
        
    自动清理所有临时文件
    """
    is_single_url = isinstance(file_urls, str)
    url_list = [file_urls] if is_single_url else file_urls
    
    temp_file_paths = []
    try:
        for url in url_list:
            # 从 URL 下载文件
            logger.info(f"正在从 URL 下载文件: {url}")
            response = requests.get(url, timeout=30, cookies=cookies)
            response.raise_for_status()
            
            # 确定文件后缀
            file_suffix = suffix
            if not file_suffix:
                # 尝试从 URL 推断后缀
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if filename and '.' in filename:
                    file_suffix = '.' + filename.split('.')[-1]
                else:
                    # 如果从URL路径无法获取扩展名，尝试从响应头获取
                    file_suffix = get_ext_from_content_type(response.headers.get('Content-Type', ''))
                    if not file_suffix:
                        file_suffix = '.tmp'  # 默认后缀
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix, dir=TEMP_DIR) as temp_file:
                temp_file.write(response.content)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_file_paths.append(temp_file.name)
        
        logger.info(f"已下载 {len(temp_file_paths)} 个文件到临时文件")
        
        # 根据输入类型返回对应类型
        if is_single_url:
            yield temp_file_paths[0]
        else:
            yield temp_file_paths
        
    except requests.RequestException as e:
        logger.error(f"下载文件失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"处理文件时发生错误: {str(e)}")
        raise
    finally:
        if auto_cleanup:
            cleanup_temp_files(temp_file_paths)


@contextmanager
def create_temp_file(suffix: str = '.tmp') -> Generator[str, None, None]:
    """
    创建临时文件的上下文管理器
    
    Args:
        suffix: 临时文件后缀名
        
    Yields:
        str: 临时文件路径
        
    自动清理临时文件
    """
    temp_file_path = None
    try:        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=TEMP_DIR) as temp_file:
            temp_file_path = temp_file.name
        
        logger.debug(f"创建临时文件: {temp_file_path}")
        yield temp_file_path
        
    finally:
        if temp_file_path:
            cleanup_temp_files(temp_file_path)


def get_ext_from_content_type(content_type: str) -> str:
    """从Content-Type响应头获取文件扩展名"""
    if not content_type:
        return ""
    
    # 解析Content-Type，去掉参数部分
    mime_type = content_type.split(';')[0].strip()
    
    # 使用标准库的 mimetypes.guess_extension
    ext = mimetypes.guess_extension(mime_type)
    
    # 优化一些常见的扩展名（mimetypes有时返回不太常见的）
    if ext:
        # 优化JPEG扩展名
        if mime_type == 'image/jpeg' and ext in ['.jpe', '.jpeg']:
            ext = '.jpg'
        # 优化TIFF扩展名  
        elif mime_type == 'image/tiff' and ext == '.tiff':
            ext = '.tif'
        
        logger.debug(f"从Content-Type '{content_type}' 获取到扩展名: {ext}")
        return ext
    else:
        logger.debug(f"未知的Content-Type: {content_type}")
        return ""


def cleanup_temp_files(file_paths: Union[str, List[str]]) -> None:
    """
    清理临时文件的工具函数
    
    Args:
        file_paths: 单个文件路径或文件路径列表
    """
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.debug(f"已清理临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败 {file_path}: {str(e)}") 