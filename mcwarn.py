import asyncio
import re
import shelve

import discord
import praw

from credentials import redditcreds, discordcreds

# Initialize reddit connection
reddit = praw.Reddit(client_id=redditcreds['id'],
                     client_secret=redditcreds['secret'],
                     password=redditcreds['password'],
                     user_agent='/r/mcservers feed',
                     username=redditcreds['username'])
print('Reddit Logged in as', reddit.user.me())

# Initialize discord client
client = discord.Client()

async def check_posts():
    """ A loop that checks the 10 newest posts and sleeps for a bit """
    await client.wait_until_ready()
    while not client.is_closed:
        shelf = shelve.open('mcservers_shelf.db', writeback=True)

        # The time of the last processed post
        # TODO: something better here..
        if '__lastpost__' in shelf:
            last_post = shelf['__lastpost__']
        else:
            last_post = 0

        print('Checking ...')
        # TODO: Trigger a 'bot is typing' in Discord while checking..?

        # Build a quick list of the submissions we're checking
        submissions = []
        for asubmission in reddit.subreddit('mcservers').new(limit=10):
            submissions.append(asubmission)

        # Reverse the list so we check the older posts first
        for submission in reversed(submissions):

            time = int(submission.created_utc)  # post time

            # Is this a new post? Compare time with last post we've seen
            if time > last_post:

                # Update last seen post time
                shelf['__lastpost__'] = time
                last_post = time

                # Announce this post to feed channel
                await send_message(chan_feed, '<http://redd.it/' + str(submission.id) + '/> ' + submission.title)

                # regex match relevant part of post titlej for server ads
                pattern = re.compile('([^\[]*)', re.IGNORECASE)
                titlesubstr = str(pattern.match(submission.title).group().strip())

                if (titlesubstr): # this is a server ad

                    # Check if this post is too soon ..
                    time = int(submission.created_utc)  # this post time
                    try:
                        prevpost = shelf[titlesubstr]  # previous post data
                        delta = time - prevpost[0]  # time between posts
                        # 597600 = 7 days less 2 hours: prevent warnings for topics just about at the limit
                        if (delta < 597600):
                            # send warning message
                            await send_message(chan_warn, titlesubstr + ' <http://redd.it/' + str(
                                submission.id) + '/> posted too soon. previous: <http://redd.it/' + prevpost[
                                                   1] + '/> ' + duration_string_format(delta) + ' ago')

                    except KeyError:
                        # pass key error exceptions, this happens when a titlesubstr is new/not in the shelf yet
                        pass

                    # store this post
                    shelf[titlesubstr] = [time, submission.id]

        shelf.close()
        await asyncio.sleep(10)  # sleep for 10 seconds


async def send_message(channel, message):
    """ Send a message to Discord. """
    await client.wait_until_ready()
    await client.send_message(channel, message)


@client.event
async def on_ready():
    """ Discord Client ready event... enter main loop task """
    print('Discord Logged in as', client.user.name, 'ID:', client.user.id)
    global chan_warn
    global chan_feed
    global chan_log
    chan_warn = client.get_channel('403496655455911937')  # #warnings channel
    chan_feed = client.get_channel('403496751677308941')  # #mcservers-feed channel
    #chan_log = client.get_channel('403496630390620161')   # #bot-log channel
    #await send_message(chan_log, 'Bot started.')
    try:
        client.loop.run_until_complete(check_posts())
    except:
        pass

def duration_string_format(delta):
    """ Pass me an integer and get a nice string with the corresponding duration """
    minutes, seconds = divmod(delta, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    ds = '' if (days == 1) else 's'
    hs = '' if (hours == 1) else 's'
    ms = '' if (minutes == 1) else 's'
    fdays = '' if (days == 0) else '{0} day{1}, '.format(days, ds)
    fhours = '' if (hours == 0) else '{0} hour{1}, '.format(hours, hs)
    return '{0}{1}{2} minute{3}'.format(fdays, fhours, minutes, ms)


def start_discord():
    """ Create Task loop and start Discord client """
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(client.start(discordcreds['client_token']))
    except:
        pass
    finally:
        loop.close()


if __name__ == '__main__':
    start_discord()
