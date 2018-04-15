import re
import shelve

import praw

from credentials import redditcreds
import time
build_time = str(int(time.time()))

# Initialize reddit connection
reddit = praw.Reddit(client_id=redditcreds['id'],
                     client_secret=redditcreds['secret'],
                     password=redditcreds['password'],
                     user_agent='/r/mcservers feed archive rebuilder',
                     username=redditcreds['username'])
print('Reddit Logged in as', reddit.user.me())


# loop through new posts
def rebuild_database():
    count = 0
    shelf = shelve.open('mcservers_shelf_rebuild'+build_time+'.db', writeback=True)
    print('Checking new posts ...')
    # Loop through servers; limit=None will return 10 pages of 100 results
    for submission in reddit.subreddit('mcservers').new(limit=None):
        time = int(submission.created_utc)  # post time

        # regex match relevant part of post title
        pattern = re.compile('([^\[]*)', re.IGNORECASE)  # Does not match [Wanted] ads etc.
        titlesubstr = str(pattern.match(submission.title).group().strip())

        # Ignore posts starting with [Wanted] or otherwise unfilled title strings
        if (titlesubstr in shelf):

            prevpost = shelf[titlesubstr]  # previous post data

            # this is an old post, ignore it it
            if (time <= prevpost[0]):
                continue

            # this is a new time seeing it, update the time
            else:
                shelf[titlesubstr] = [time, submission.id]

        # first time seeing this server
        else:
            count += 1
            shelf[titlesubstr] = [time, submission.id]

    shelf.close()
    print('Rebuilt records for', count, 'servers.')

if __name__ == '__main__':
    rebuild_database()