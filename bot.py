import unirest
import praw
import re
import json
import sys
import msvcrt
import os

from threading import Thread



reddit = praw.Reddit(user_agent = 'hummingbot v1.0')

err_file = open('error_log.txt', 'a')


#-bot will search a subbreddit for comments with myanimelist.net/anime/number/name
#-the name will be extracted and looked up using hummingbird api
#-data will be formated and a quick snapshot of the anime will be posted as a reply
#-after the comment has been replied to, the comment id will be stored in a file so
# that the same comment won't be replied to on start up
def main():
	#maximum comment length to reply to
	MAX_LENGTH = 70
	#subreddit the bot will run on
	SUBREDDIT = ''
	

	running = Thread(target = KeybListener)
	running.start()

	reddit.login("username", "password")
	print "logged in.\n"

	while True:
		try:
			for comment in praw.helpers.comment_stream(reddit, SUBREDDIT, limit = 50, verbosity = 0):
				#check if the comment has been replied to already
				with open('responded_comments.txt', 'r+') as rc:
					if((re.search('myanimelist.net/anime/\d{1,5}/\w+', comment.body)) and (comment.body.count(' ') < MAX_LENGTH) and (comment.id not in rc.read())):
						anime = getName(comment.body)
						response = getData(anime)
						try:
							data = json.loads(response.raw_body)
							print "json loaded"
							bot_reply = ("#####&#009;\n\n######&#009;\n\n####&#009;\n**Title:** {0}\n\n---\n\n>"
										"**Rating:** {1}/5  \n"
										"**Age Rating:** {2}  \n"
						                "**Type:** {3}  \n"
						                "**Episodes:** {4} ({5}min each)  \n"
						                "**Genres:** {6}  \n"
						                "**Started Airing:** {7}  \n"
						                "**Finished Airing:** {8}  \n"
						                "**Synopsis:** {9}  \n"
						                "[**Poster Image:**]({10})  \n{11}\n\n---  \n"
						                "\n^^data ^^collected ^^from ^^[hummingbird.me](http://www.hummingbird.me)"
						                "  ^^|  ^^any ^^questions ^^or ^^issues ^^message ^^[me]"
						                "(http://www.reddit.com/message/compose/?to=for_hiyori)").format(data["canonical_title"].encode('utf-8'),
                	                           round(data["community_rating"], 2),
                	                           data["age_rating"],
                	                           data["type"],
                	                           data["episode_count"],
                	                           data["episode_length"],
                	                           ', '.join(data["genres"]),
                	                           data["started_airing"],
                	                           data["finished_airing"],
                	                           data["synopsis"].encode('utf-8'),
                	                           data["poster_image"],
                	                           "**Trailer:** n/a" if (data["youtube_trailer_id"] is None or (not data["youtube_trailer_id"])) 
                	                       							else "[**Trailer:**](https://www.youtube.com/watch?v=" + data["youtube_trailer_id"] + ")")
							comment.reply(bot_reply)
							#add comment id to list of replied comments
							rc.seek(0, os.SEEK_CUR)
							rc.write(comment.id + "\n")
							print "response to " + comment.id + " posted.\n"


						except Exception as err:
							print "error loading json or replying. anime probably not found...\n"
							try:
								err_file.write(comment.body + "\n")
							except IOError:
								print "IOError"
								pass

		except Exception as err:
			print err()


#extract anime name in hummingbird.me api format from myanimelist.net link
def getName(mal_link):
	n = re.search('\d{1,5}/((\w+(-|\(|:|;)?\w)*((%|!)(\w\d|\d\d|\w\w))*(\w*))', mal_link).group(1).replace('_', '-').lower()
	n = re.sub('(%(\w\d|\d\d|\w\w))', '-', n)
	n = re.sub(';', '-', n)
	n = re.sub('!', '', n)
	n = re.sub(':()', '', n)
	n = re.sub('-+', '-', n)
	return n


#returns anime data from humminbird.me 
def getData(name):
	try:
		print "fetching " + name + " data..."
		get_data = unirest.get("https://vikhyat-hummingbird-v2.p.mashape.com/anime/" + name, 
			headers={"X-Mashape-Key": "key"})
		if(get_data.code == 404):
			name = re.sub('s-', '-s-', name, 1)
			print "trying " + name + "..."
			get_data = unirest.get("https://vikhyat-hummingbird-v2.p.mashape.com/anime/" + name, 
			headers={"X-Mashape-Key": "key"})
		return get_data

	except Exception as err:
		print err()
		return None


def KeybListener():
	while True:
		if msvcrt.kbhit() and (msvcrt.getch() == 'q'):
			close_bot()


def close_bot():
	reddit.clear_authentication()
	err_file.close()
	print "\nexiting...\n"
	sys.exit()


print "starting..."
if __name__ == '__main__':
	main()
