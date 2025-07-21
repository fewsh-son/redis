# Redis Session Management Implementation Guide

## Token Validation and Updates

Checking the token isn't very exciting, because all of the interesting stuff happens when we're updating the token itself.

For the visit, we'll update the login HASH for the user and record the current timestamp for the token in the ZSET of recent users. If the user was viewing an item, we also add the item to the user's recently viewed ZSET and trim that ZSET if it grows past 25 items. The function that does all of this can be seen next.

## Performance Benefits

And you know what? That's it. We've now recorded when a user with the given session last viewed an item and what item that user most recently looked at. On a server made in the last few years, you can record this information for at least 20,000 item views every second, which is more than three times what we needed to perform against the database. This can be made even faster, which we'll talk about later. But even for this version, we've improved performance by 10–100 times over a typical relational database in this context.

## Data Cleanup Strategy

Over time, memory use will grow, and we'll want to clean out old data. As a way of limiting our data, we'll only keep the most recent 10 million sessions. For our cleanup, we'll fetch the size of the ZSET in a loop. If the ZSET is too large, we'll fetch the oldest items up to 100 at a time (because we're using timestamps, this is just the first 100 items in the ZSET), remove them from the recent ZSET, delete the login tokens from the login HASH, and delete the relevant viewed ZSETs. If the ZSET isn't too large, we'll sleep for one second and try again later. The code for cleaning out old sessions is shown next.

## Scale Analysis

How could something so simple scale to handle five million users daily? Let's check the numbers. If we expect five million unique users per day, then in two days (if we always get new users every day), we'll run out of space and will need to start deleting tokens. In one day there are 24 × 3600 = 86,400 seconds, so there are 5 million / 86,400 < 58 new sessions every second on average. If we ran our cleanup function every second (as our code implements), we'd clean up just under 60 tokens every second. But this code can actually clean up more than 10,000 tokens per second across a network, and over 60,000 tokens per second locally, which is 150–1,000 times faster than we need.

## Cleanup Functions Implementation Notes

This and other examples in this book will sometimes include cleanup functions like listing 2.3. Depending on the cleanup function, it may be written to be run as a daemon process (like listing 2.3), to be run periodically via a cron job, or even to be run during every execution (section 6.3 actually includes the cleanup operation as part of an "acquire" operation). As a general rule, if the function includes a `while not QUIT:` line, it's supposed to be run as a daemon, though it could probably be modified to be run periodically, depending on its purpose.

## Technical Implementation Details

Inside listing 2.3, you'll notice that we called three functions with a syntax similar to `conn.delete(*vtokens)`. Basically, we're passing a sequence of arguments to the underlying function without previously unpacking the arguments. For further details on the semantics of how this works, you can visit the Python language tutorial website by visiting this short url: http://mng.bz/8I7W.

## Alternative Approaches

As you learn more about Redis, you'll likely discover that some of the solutions we present aren't the only ways to solve the problem. In this case, we could omit the recent ZSET, store login tokens as plain key-value pairs, and use Redis EXPIRE to set a future date or time to clean out both sessions and our recently viewed ZSETs. But using EXPIRE prevents us from explicitly limiting our session information to 10 million users, and prevents us from performing abandoned shopping cart analysis during session expiration, if necessary in the future.

## Known Limitations and Race Conditions

The cleanup function has a race condition where it's technically possible for a user to manage to visit the site in the same fraction of a second when we were deleting their information. We're not going to worry about that here because it's unlikely, and because it won't cause a significant change in the data we're recording (aside from requiring that the user log in again). We'll talk about guarding against race conditions and about how we can even speed up the deletion operation in chapters 3 and 4.

---

## Key Implementation Requirements

### Data Structures Needed:
- **Login HASH**: Store user login information
- **Recent Users ZSET**: Track recent user sessions with timestamps
- **Recently Viewed ZSET**: Store up to 25 recently viewed items per user

### Core Functions to Implement:
1. **Token Update Function**: Update login hash, record timestamp, manage recently viewed items
2. **Cleanup Daemon**: Remove old sessions, maintain 10 million session limit
3. **Session Validation**: Check and update token status

### Performance Targets:
- Handle 20,000+ item views per second
- Cleanup 10,000+ tokens per second (network) / 60,000+ tokens per second (local)
- Support 5 million daily unique users
- 10-100x performance improvement over traditional databases
