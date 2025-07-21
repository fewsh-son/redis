import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Article configuration
    ARTICLE_KEY_PREFIX = "article:"
    TIME_ZSET_KEY = "time"
    SCORE_ZSET_KEY = "score"
    VOTED_KEY_PREFIX = "voted:"
    
    # Group configuration
    GROUPS_SET_PREFIX = "groups:"  # groups:programming
    GROUP_SCORE_PREFIX = "score:"  # score:programming
    GROUP_TIME_PREFIX = "time:"    # time:programming
    
    # Voting configuration
    UPVOTED_KEY_PREFIX = "upvoted:"    # upvoted:article_id
    DOWNVOTED_KEY_PREFIX = "downvoted:"  # downvoted:article_id
    USER_VOTES_PREFIX = "user_votes:"   # user_votes:user_id 