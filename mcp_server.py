#!/usr/bin/env python3
"""
Video Downloader MCP Server

这是一个 MCP (Model Context Protocol) 服务器，可以被 Claude Desktop、Cline 等 AI 工具调用。
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from video_downloader import VideoDownloader
from video_downloader.models import DownloadOptions
from video_downloader.config import DownloaderConfig


class MCPServer:
    """MCP 服务器实现"""
    
    def __init__(self):
        self.downloader = VideoDownloader()
        self.version = "1.0.0"
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                result = await self.call_tool(params)
            elif method == "initialize":
                result = self.initialize(params)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """初始化 MCP 服务器"""
        return {
            "protocolVersion": "0.1.0",
            "serverInfo": {
                "name": "video-downloader",
                "version": self.version
            },
            "capabilities": {
                "tools": {}
            }
        }
    
    def list_tools(self) -> Dict[str, Any]:
        """列出所有可用的工具"""
        return {
            "tools": [
                {
                    "name": "download_video",
                    "description": "下载视频（支持 YouTube、Bilibili、Douyin、Twitter/X、Instagram 等多平台）",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "视频 URL"
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "输出目录（可选）",
                                "default": "./downloads"
                            },
                            "quality": {
                                "type": "string",
                                "description": "视频画质（可选，如 1080P、720P）",
                                "enum": ["4K", "1080P60", "1080P", "720P60", "720P", "480P", "360P"]
                            },
                            "filename_template": {
                                "type": "string",
                                "description": "文件名模板（可选，如 {author}_{title}）",
                                "default": "{title}"
                            }
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "batch_download",
                    "description": "批量下载多个视频",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "urls": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "视频 URL 列表"
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "输出目录（可选）",
                                "default": "./downloads"
                            }
                        },
                        "required": ["urls"]
                    }
                },
                {
                    "name": "get_video_info",
                    "description": "获取视频信息（不下载）",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "视频 URL"
                            }
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "list_supported_platforms",
                    "description": "列出所有支持的平台",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    
    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "download_video":
            return await self.download_video(arguments)
        elif tool_name == "batch_download":
            return await self.batch_download(arguments)
        elif tool_name == "get_video_info":
            return await self.get_video_info(arguments)
        elif tool_name == "list_supported_platforms":
            return self.list_supported_platforms()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def download_video(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """下载单个视频"""
        url = args["url"]
        output_dir = args.get("output_dir", "./downloads")
        quality = args.get("quality")
        filename_template = args.get("filename_template", "{title}")
        
        options = DownloadOptions(
            output_path=output_dir,
            quality=quality,
            filename_template=filename_template
        )
        
        result = await self.downloader.download(url, options)
        
        if result.success:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ 下载成功！\n\n"
                                f"📁 文件路径: {result.file_path}\n"
                                f"📊 文件大小: {result.file_size / 1024 / 1024:.2f} MB"
                                + (f"\n⏱️  耗时: {result.duration:.1f}s" if result.duration > 0 else "")
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ 下载失败: {result.error}"
                    }
                ],
                "isError": True
            }
    
    async def batch_download(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """批量下载视频"""
        urls = args["urls"]
        output_dir = args.get("output_dir", "./downloads")
        
        options = DownloadOptions(output_path=output_dir)
        batch_result = await self.downloader.batch_download(urls, options)
        
        success_list = []
        failed_list = []
        
        for result in batch_result.results:
            if result.success:
                success_list.append(f"✓ {result.file_path}")
            else:
                failed_list.append(f"✗ {result.error}")
        
        text = f"📊 批量下载完成\n\n"
        text += f"✅ 成功: {batch_result.successful}\n"
        text += f"❌ 失败: {batch_result.failed}\n"
        text += f"📦 总计: {batch_result.total}\n\n"
        
        if success_list:
            text += "成功列表:\n" + "\n".join(success_list) + "\n\n"
        
        if failed_list:
            text += "失败列表:\n" + "\n".join(failed_list)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
    
    async def get_video_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取视频信息"""
        url = args["url"]
        
        try:
            metadata = await self.downloader.extract_metadata(url)
            
            text = f"📺 视频信息\n\n"
            text += f"标题: {metadata.title}\n"
            text += f"作者: {metadata.author}\n"
            text += f"时长: {metadata.duration} 秒\n"
            text += f"平台: {metadata.platform}\n"
            text += f"上传日期: {metadata.upload_date}\n"
            
            if metadata.description:
                text += f"描述: {metadata.description[:100]}...\n"
            
            if metadata.quality_options:
                text += f"可用画质: {', '.join(q.name for q in metadata.quality_options)}\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ 获取视频信息失败: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    def list_supported_platforms(self) -> Dict[str, Any]:
        """列出支持的平台"""
        platforms = self.downloader.platform_manager.list_platforms()
        
        text = "📺 Supported Platforms:\n\n"
        for platform in platforms:
            text += f"• {platform}\n"

        text += "\nCoverage:\n"
        text += "✅ YouTube: full support via yt-dlp\n"
        text += "✅ Bilibili: full support via yt-dlp (fallback: custom extractor)\n"
        text += "✅ Twitter/X: full support via yt-dlp\n"
        text += "✅ Instagram: full support via yt-dlp\n"
        text += "✅ TikTok: full support via yt-dlp\n"
        text += "✅ Douyin: yt-dlp → API → Playwright fallback chain\n"
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
    
    async def run(self):
        """运行 MCP 服务器（stdio 模式）"""
        while True:
            try:
                # 从 stdin 读取请求
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                response = await self.handle_request(request)
                
                # 输出响应到 stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


async def main():
    """主函数"""
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
