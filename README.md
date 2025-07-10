# Voting on articles

# Article example: 

## Sử dụng redis HASH để lưu trữ thông tin bài viết: (Metadata: title, link, poster, time, vote ...)
    - article:92876 ----------------hash

    - Tại sao lại dùng hash: 

        - Metadata là dữ liệu dạng "key → value",  mỗi bài viết là một object có nhiều trường nhỏ.
            # Cách tệ (dùng nhiều string key):
            SET article:123:title "Redis Voting System"
            SET article:123:link "https://..."
            SET article:123:votes 42

            # Cách tốt (hash):
            HMSET article:123 title "Redis Voting System" link "https://..." votes 42

        - Truy cập nhanh từng field
            HGET article:123 title (Chỉ lấy title)
            HINCRBY article:123 votes 1 (Tăng vote)

            → Không cần load toàn bộ object → nhanh & tiết kiệm băng thông.

        - Dễ xoá 
            DEL article:123

            → Xóa sạch toàn bộ metadata chỉ với 1 key.

    - Khi nào KHÔNG nên dùng Hash?
        
        - Nếu bài viết có nội dung lớn (HTML, markdown) → nên lưu nội dung chính ở hệ thống khác (VD: DB, MinIO, S3…)
        - Nếu không cần truy cập từng trường → có thể gộp tất cả thành 1 chuỗi JSON (SET key json)



## Sử dụng redis ZSET để lưu time hoặc score
    - time-----------------zset
    (article:85738  | 275317372.26)
    (article:34374  | 275317356.21)
    ...
    (article:85738  | 274317371.26)

    - Tại sao lại dùng ZSET cho time và score: 

        - Tự động sắp xếp theo score hoặc timestamp

            ZSET lưu dữ liệu theo:
                Member: ví dụ article:123
                Score: số thực (float) dùng để sắp xếp

        - Cập nhật score/time cực nhanh

            Khi người dùng vote: ZINCRBY article:score 1 article:123
            Hoặc khi tạo bài viết mới: ZADD article:time 1720000000 article:123

            → Cập nhật mà không cần sắp xếp lại — Redis duy trì thứ tự nội bộ rất hiệu quả (O(log N)).

        - Hỗ trợ lọc theo thời gian + điểm

## Sử dụng redis set để lưu người vote: 
    - voted:12123 --------- set

    - Tại sao lại dùng SET cho người vote:

        - Redis SET là tập hợp các phần tử không trùng lặp, rất phù hợp với việc lưu danh sách user đã vote
        - Kiểm tra user đã vote chưa (rất nhanh): Thời gian truy cập: O(1) → cực nhanh, phù hợp cho hệ thống realtime
        - Hỗ trợ rút lại vote (nếu cần)

    - Vì sao không dùng các kiểu dữ liệu khác?
        - List	    Cho phép trùng lặp → không ngăn được double-vote
        - Hash	    Không tự lọc trùng → phải kiểm tra thủ công
        - ZSet	    Dư thừa (có score mà không cần ở đây)
        - String	Không lưu được nhiều user → không mở rộng


# Follow  when user voted: 

    Ví dụ người dùng 11111 bỏ phiếu cho bài viết 12345

    score --------------------- zset       ----------->           score --------------------- zset
    (article:12345  | 275317356.21)                              (article:12345  | 275317415.21)
    
    voted:12345 --------------- set                               voted:12345 --------------- set 
        (user: 12121)                      ----------->                 (user: 12121)
        (user: 34331)                                                   (user: 11111)
            ...                                                               ...

