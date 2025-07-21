#!/usr/bin/env python3
"""
Demo script cho tính năng Groups
"""

from services.article_service import ArticleService
from services.group_service import GroupService
from utils.redis_client import redis_client
import time

def print_separator(title: str):
    """In dòng phân cách đẹp"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_article_with_groups(article, index: int = None):
    """In thông tin bài viết với groups"""
    prefix = f"{index}. " if index is not None else "  "
    groups_str = f"🏷️  Groups: {', '.join(article.groups)}" if article.groups else "🏷️  Groups: None"
    
    print(f"{prefix}📰 {article.title}")
    print(f"    🔗 Link: {article.link}")
    print(f"    👤 Poster: {article.poster}")
    print(f"    ⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(article.time_created))}")
    print(f"    👍 Votes: {article.votes}")
    print(f"    ⭐ Score: {article.get_score():.2f}")
    print(f"    {groups_str}")
    print(f"    🆔 ID: {article.id}")
    print()

def demo_posting_articles_with_groups():
    """Demo đăng bài viết với groups"""
    print_separator("🚀 DEMO POSTING ARTICLES WITH GROUPS")
    
    service = ArticleService()
    
    # Danh sách bài viết với groups
    articles_with_groups = [
        {
            "title": "Python Best Practices 2024",
            "link": "https://python-best-practices.com",
            "poster": "python_expert",
            "groups": ["programming", "python"]
        },
        {
            "title": "Redis Performance Optimization",
            "link": "https://redis-performance.dev",
            "poster": "db_admin",
            "groups": ["programming", "database", "redis"]
        },
        {
            "title": "JavaScript ES2024 Features",
            "link": "https://js-es2024.com",
            "poster": "js_developer",
            "groups": ["programming", "javascript"]
        },
        {
            "title": "Docker Container Security",
            "link": "https://docker-security.guide",
            "poster": "devops_engineer",
            "groups": ["devops", "security"]
        },
        {
            "title": "Machine Learning with Python",
            "link": "https://ml-python.ai",
            "poster": "data_scientist",
            "groups": ["programming", "python", "ai"]
        },
        {
            "title": "Cloud Architecture Patterns",
            "link": "https://cloud-patterns.com",
            "poster": "cloud_architect",
            "groups": ["cloud", "architecture"]
        }
    ]
    
    posted_ids = []
    
    for i, article_data in enumerate(articles_with_groups, 1):
        print(f"Đăng bài viết {i}/{len(articles_with_groups)}...")
        article_id = service.post_article(
            title=article_data["title"],
            link=article_data["link"],
            poster=article_data["poster"],
            groups=article_data["groups"]
        )
        posted_ids.append(article_id)
        
        # Delay nhỏ để có sự khác biệt về thời gian
        time.sleep(0.1)
    
    print(f"\n✅ Đã đăng thành công {len(posted_ids)} bài viết với groups!")
    return posted_ids

def demo_group_operations():
    """Demo các operations với groups"""
    print_separator("🏷️  DEMO GROUP OPERATIONS")
    
    service = ArticleService()
    group_service = GroupService()
    
    # Lấy tất cả groups
    all_groups = group_service.get_all_groups()
    print(f"📋 Tất cả groups: {', '.join(all_groups)}")
    
    # Thống kê từng group
    print(f"\n📊 THỐNG KÊ GROUPS:")
    for group_name in all_groups:
        stats = group_service.get_group_stats(group_name)
        print(f"  🏷️  {group_name}:")
        print(f"     - Số bài viết: {stats['article_count']}")
        print(f"     - Score cao nhất: {stats['highest_score']:.2f}")
        print(f"     - Score thấp nhất: {stats['lowest_score']:.2f}")
        print()

def demo_fetching_by_groups():
    """Demo lấy bài viết theo groups"""
    print_separator("🔍 DEMO FETCHING BY GROUPS")
    
    service = ArticleService()
    group_service = GroupService()
    
    # Lấy bài viết theo từng group
    all_groups = group_service.get_all_groups()
    
    for group_name in all_groups[:3]:  # Chỉ demo 3 groups đầu tiên
        print(f"\n🏷️  ARTICLES IN GROUP: {group_name.upper()}")
        
        # Lấy top 3 bài viết trong group
        top_articles = service.get_top_articles_in_group(group_name, limit=3)
        
        if top_articles:
            print(f"   📈 Top {len(top_articles)} bài viết điểm cao nhất:")
            for i, article in enumerate(top_articles, 1):
                print_article_with_groups(article, i)
        else:
            print("   ❌ Không có bài viết nào trong group này")

def demo_group_management():
    """Demo quản lý groups"""
    print_separator("⚙️  DEMO GROUP MANAGEMENT")
    
    service = ArticleService()
    group_service = GroupService()
    
    # Lấy một bài viết để test
    recent_articles = service.get_recent_articles(limit=1)
    
    if recent_articles:
        article = recent_articles[0]
        print(f"🎯 Bài viết test: {article.title}")
        print(f"   Groups hiện tại: {', '.join(article.groups) if article.groups else 'None'}")
        
        # Thêm vào group mới
        new_group = "testing"
        print(f"\n➕ Thêm vào group '{new_group}'...")
        success = service.add_article_to_group(article.id, new_group)
        
        if success:
            # Lấy lại article để xem groups mới
            updated_article = service.get_article(article.id)
            print(f"   Groups sau khi thêm: {', '.join(updated_article.groups)}")
            
            # Xóa khỏi group
            print(f"\n➖ Xóa khỏi group '{new_group}'...")
            service.remove_article_from_group(article.id, new_group)
            
            # Lấy lại article
            final_article = service.get_article(article.id)
            print(f"   Groups sau khi xóa: {', '.join(final_article.groups) if final_article.groups else 'None'}")

def demo_cross_group_comparison():
    """Demo so sánh articles across groups"""
    print_separator("🔄 DEMO CROSS-GROUP COMPARISON")
    
    service = ArticleService()
    
    # So sánh top articles giữa 2 groups
    groups_to_compare = ["programming", "python"]
    
    for group_name in groups_to_compare:
        print(f"\n🏆 TOP 2 ARTICLES IN {group_name.upper()}:")
        top_articles = service.get_top_articles_in_group(group_name, limit=2)
        
        if top_articles:
            for i, article in enumerate(top_articles, 1):
                print_article_with_groups(article, i)
        else:
            print("   ❌ Không có bài viết nào")

def main():
    """Hàm main chạy demo"""
    print_separator("🎉 REDIS VOTING SYSTEM - GROUPS DEMO")
    
    # Kiểm tra kết nối Redis
    if not redis_client.ping():
        print("❌ Không thể kết nối Redis! Vui lòng kiểm tra:")
        print("   - Redis server đã chạy chưa?")
        print("   - Cấu hình connection trong config.py")
        return
    
    print("✅ Kết nối Redis thành công!")
    
    try:
        # Chạy các demo
        demo_posting_articles_with_groups()
        demo_group_operations()
        demo_fetching_by_groups()
        demo_group_management()
        demo_cross_group_comparison()
        
        print_separator("🎊 DEMO GROUPS HOÀN THÀNH")
        print("Tất cả tính năng grouping articles đã hoạt động!")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình demo: {str(e)}")
        raise
    
    finally:
        # Đóng kết nối Redis
        redis_client.close()

if __name__ == "__main__":
    main() 