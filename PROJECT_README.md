# Redis Voting System - Posting and Fetching Articles

Tính năng posting và fetching articles cho hệ thống voting sử dụng Redis.

## 📁 Cấu trúc Project

```
redis/
├── config.py                 # Cấu hình Redis và constants
├── requirements.txt          # Dependencies
├── main.py                   # Demo script chính
├── demo_groups.py            # Demo script cho groups
├── demo_voting.py            # Demo script cho voting system
├── utils/
│   ├── __init__.py
│   └── redis_client.py       # Redis client wrapper
├── models/
│   ├── __init__.py
│   ├── article.py            # Article model (với groups và voting support)
│   └── vote.py               # Vote model và VoteType enum
└── services/
    ├── __init__.py
    ├── article_service.py    # Service layer cho articles
    ├── group_service.py      # Service layer cho groups
    └── voting_service.py     # Service layer cho voting system
```

## 🚀 Cài đặt và Chạy

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình Redis

Tạo file `.env` (hoặc chỉnh sửa trong `config.py`):

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
# REDIS_PASSWORD=your_password_here
```

### 3. Khởi động Redis server

```bash
redis-server
```

### 4. Chạy demo

```bash
# Demo cơ bản
python main.py

# Demo groups
python demo_groups.py

# Demo voting system
python demo_voting.py

# Quick tests
python quick_test.py
python quick_test_groups.py
python quick_test_voting.py
```

## 🏗️ Kiến trúc Redis

### 1. Hash - Lưu metadata bài viết

```
Key: article:12345
Fields:
  title: "Redis Best Practices"
  link: "https://redis.io/docs"
  poster: "redis_admin"
  time: "1720000000.26"
  votes: "5"
```

### 2. ZSET - Sắp xếp theo thời gian

```
Key: time
Members:
  article:12345 -> 1720000000.26
  article:12346 -> 1720000010.50
```

### 3. ZSET - Sắp xếp theo điểm

```
Key: score
Members:
  article:12345 -> 105.2 (votes + time_bonus)
  article:12346 -> 98.7
```

### 4. SET - Danh sách người vote (sẽ dùng cho tính năng voting)

```
Key: voted:12345
Members: {user:111, user:222, user:333}
```

### 5. SET - Groups (Nhóm bài viết)

```
Key: groups:programming
Members: {article:12345, article:12346, article:12347}
```

### 6. ZSET - Score theo groups

```
Key: score:programming
Members:
  article:12345 -> 105.2
  article:12346 -> 98.7
  article:12347 -> 87.3
```

### 7. SET - Upvoted users (Voting System)

```
Key: upvoted:12345
Members: {user1, user2, user4}
```

### 8. SET - Downvoted users (Voting System)

```
Key: downvoted:12345
Members: {user3, user5}
```

### 9. HASH - User vote history (Voting System)

```
Key: user_votes:user1
Fields:
  article:12345 -> "upvote|1720000000.26"
  article:12346 -> "downvote|1720000100.50"
```

## 🔧 API Reference

### ArticleService Methods

#### Posting Articles

- `post_article(title, link, poster, groups=None)` - Đăng bài viết mới (có thể chỉ định groups)
- `delete_article(article_id)` - Xóa bài viết

#### Fetching Articles

- `get_article(article_id)` - Lấy một bài viết theo ID
- `get_articles_by_time(start, end)` - Lấy bài viết sắp xếp theo thời gian
- `get_articles_by_score(start, end)` - Lấy bài viết sắp xếp theo điểm
- `get_top_articles(limit)` - Lấy top bài viết điểm cao
- `get_recent_articles(limit)` - Lấy bài viết mới nhất
- `get_articles_in_time_range(start_time, end_time)` - Lấy bài viết trong khoảng thời gian
- `get_article_count()` - Đếm tổng số bài viết

#### Utility Methods

- `update_article_score(article_id)` - Cập nhật điểm bài viết

#### Groups Methods

- `get_articles_by_group(group_name)` - Lấy tất cả articles trong group
- `get_articles_by_group_score(group_name, start, end)` - Lấy articles trong group theo score
- `get_top_articles_in_group(group_name, limit)` - Lấy top articles trong group
- `add_article_to_group(article_id, group_name)` - Thêm article vào group
- `remove_article_from_group(article_id, group_name)` - Xóa article khỏi group

### GroupService Methods

- `get_all_groups()` - Lấy danh sách tất cả groups
- `get_group_article_count(group_name)` - Đếm số articles trong group
- `get_group_stats(group_name)` - Lấy thống kê group
- `delete_group(group_name)` - Xóa group
- `get_article_groups(article_id)` - Lấy danh sách groups của article

#### Voting Methods

- `upvote_article(user_id, article_id)` - Upvote bài viết
- `downvote_article(user_id, article_id)` - Downvote bài viết
- `remove_vote_from_article(user_id, article_id)` - Xóa vote
- `get_user_vote_for_article(user_id, article_id)` - Lấy vote của user
- `get_article_vote_stats(article_id)` - Lấy thống kê votes
- `get_article_voted_users(article_id)` - Lấy danh sách users đã vote
- `get_user_vote_history(user_id)` - Lấy lịch sử vote của user

### VotingService Methods

- `upvote(user_id, article_id)` - Upvote article
- `downvote(user_id, article_id)` - Downvote article
- `remove_vote(user_id, article_id)` - Remove vote
- `get_user_vote(user_id, article_id)` - Get user's vote
- `get_vote_stats(article_id)` - Get vote statistics
- `get_voted_users(article_id)` - Get users who voted
- `get_user_vote_history(user_id)` - Get user's vote history
- `can_user_vote(user_id, article_id)` - Check if user can vote
- `cleanup_article_votes(article_id)` - Clean up votes when deleting article

## 📊 Demo Features

Script `main.py` demo các tính năng:

1. **Posting Articles** - Đăng 5 bài viết mẫu
2. **Fetching by Time** - Lấy bài viết mới nhất
3. **Fetching by Score** - Lấy bài viết điểm cao nhất
4. **Single Article** - Lấy chi tiết một bài viết
5. **Time Range Query** - Lấy bài viết trong khoảng thời gian

Script `demo_groups.py` demo tính năng groups:

1. **Posting with Groups** - Đăng bài viết với groups
2. **Group Operations** - Thống kê và quản lý groups
3. **Fetching by Groups** - Lấy bài viết theo groups
4. **Group Management** - Thêm/xóa articles khỏi groups
5. **Cross-Group Comparison** - So sánh articles giữa các groups

Script `demo_voting.py` demo tính năng voting system:

1. **Setup Articles** - Tạo articles để demo voting
2. **Basic Voting** - Upvote/downvote cơ bản
3. **Vote Changes** - Thay đổi vote (upvote ↔ downvote)
4. **Prevent Double Voting** - Ngăn chặn vote trùng lặp
5. **Vote History** - Lịch sử vote của user
6. **Article Ranking** - Xếp hạng articles theo votes
7. **Group Voting** - Voting trong groups

## 🔄 Tính năng tiếp theo

- ✅ ~~Voting system (upvote/downvote)~~ - **COMPLETED**
- Comment system
- User authentication
- Article categories/tags
- Real-time notifications
- Article bookmarking
