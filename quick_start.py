#!/usr/bin/env python3
"""
Video Downloader - 快速入门示例
"""

import asyncio
from video_downloader import VideoDownloader
from video_downloader.models import DownloadOptions


async def example_1_simple_download():
    """示例1: 最简单的下载"""
    print("=" * 50)
    print("示例1: 最简单的下载")
    print("=" * 50)
    
    downloader = VideoDownloader()
    
    # 替换成你要下载的视频 URL
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    
    result = await downloader.download(url)
    
    if result.success:
        print(f"✅ 下载成功！")
        print(f"📁 文件路径: {result.file_path}")
    else:
        print(f"❌ 下载失败: {result.error_message}")


async def example_2_custom_options():
    """示例2: 自定义下载选项"""
    print("\n" + "=" * 50)
    print("示例2: 自定义下载选项")
    print("=" * 50)
    
    downloader = VideoDownloader()
    
    # 自定义下载选项
    options = DownloadOptions(
        output_dir="./my_videos",  # 输出目录
        quality="1080P",           # 画质
        filename_template="{author}_{title}"  # 文件名模板
    )
    
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    result = await downloader.download(url, options)
    
    if result.success:
        print(f"✅ 下载成功！")
        print(f"📁 文件路径: {result.file_path}")


async def example_3_batch_download():
    """示例3: 批量下载"""
    print("\n" + "=" * 50)
    print("示例3: 批量下载")
    print("=" * 50)
    
    downloader = VideoDownloader()
    
    # 多个视频 URL
    urls = [
        "https://www.bilibili.com/video/BV1xx411c7mD",
        "https://www.bilibili.com/video/BV1yy411c7mE",
        # 添加更多 URL...
    ]
    
    options = DownloadOptions(output_dir="./batch_downloads")
    batch_result = await downloader.batch_download(urls, options)
    
    print(f"✅ 成功: {batch_result.successful}")
    print(f"❌ 失败: {batch_result.failed}")
    print(f"📊 总计: {batch_result.total}")


async def example_4_metadata_only():
    """示例4: 只获取视频信息"""
    print("\n" + "=" * 50)
    print("示例4: 只获取视频信息（不下载）")
    print("=" * 50)
    
    downloader = VideoDownloader()
    
    url = "https://www.bilibili.com/video/BV1xx411c7mD"
    metadata = await downloader.extract_metadata(url)
    
    print(f"📺 标题: {metadata.title}")
    print(f"👤 作者: {metadata.author}")
    print(f"⏱️  时长: {metadata.duration} 秒")
    print(f"📅 日期: {metadata.upload_date}")
    print(f"🎬 平台: {metadata.platform}")


async def main():
    """主函数"""
    print("\n🎬 Video Downloader - 快速入门示例\n")
    
    # 运行示例（取消注释你想运行的示例）
    
    # await example_1_simple_download()
    # await example_2_custom_options()
    # await example_3_batch_download()
    await example_4_metadata_only()  # 默认运行示例4（不会真正下载）
    
    print("\n" + "=" * 50)
    print("✨ 示例运行完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
