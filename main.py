from datetime import datetime, timedelta
import requests
import json
import csv
import os
import re
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

ACCESS_TOKEN = config['FACEBOOK_GRAPH_API']['ACCESS_TOKEN']
BASE_URL = config['FACEBOOK_GRAPH_API']['BASE_URL']

def create_datetime_from_string(created_time_string):
	created_time = datetime.strptime(created_time_string, "%Y-%m-%dT%H:%M:%S+0000")
	created_time = created_time + timedelta(hours=7)
	return created_time

def get_user_friends(id = 'me', after = ''):
	fields = 'id,name,friends{id,name}'
	if after:
		fields = 'friends.after(%s){id,name}' % after
	url = '%s%s?fields=%s&access_token=%s' % (BASE_URL,id,fields,ACCESS_TOKEN)
	return requests.get(url).json()

def get_user_likes(id = 'me', after = ''):
	fields = 'likes{id,name,about,description,location,category,category_list}'
	if after:
		fields = 'likes.after(%s){id,name,about,description,location,category,category_list}' % after
	url = '%s%s?fields=%s&access_token=%s' % (BASE_URL,id,fields,ACCESS_TOKEN)
	return requests.get(url).json()

def get_page_location(page):
	if "location" in page and "country" in page["location"]:
		return page["location"]["country"]

	if re.match('[ก-ฮ]', page["name"]) != None:
		return "Thailand"

	if "about" in page:
		if re.match('[ก-ฮ]', page["about"]) != None:
			return "Thailand"
	
	if "description" in page:
		if re.match('[ก-ฮ]', page["description"]) != None:
			return "Thailand"

	return "United States"

def retreive_analyze_data(user_id, user_name):
	content = get_user_likes(user_id)

	since = datetime.today() - timedelta(days=30)
	since = datetime(since.year,since.month,since.day) # Set its time to midnight (12:00 AM)

	# Make the associated directory if it does not exist
	if not os.path.exists("collected_data/" + user_name):
		os.mkdir("collected_data/" + user_name)

	# Create associated csv file and clear existing data
	outputfile = open("collected_data/" + user_name + "/pages_you_like_posts.csv", encoding = 'utf-8', mode = "w")
	outputfile.truncate()
	outputfile.close()

	with open("collected_data/" + user_name + "/pages_you_like_posts.csv", encoding = 'utf-8', mode = "a+") as csvfile:
		spamwriter = csv.writer(csvfile)
		spamwriter.writerow(["PAGE_ID", "PAGE_NAME", "PAGE_CATEGORY", "PAGE_LOCATION", "POST_ID", "HOUR_TIME","CREATED_TIME"])
		
		while ("likes" in content):
			for like in content["likes"]["data"]:
				page_id = like["id"]
				page_name = like["name"].replace('\n', ' ').replace(',', ' ')
				page_category = like["category"]
				page_location = get_page_location(like)

				print("\t- Querying Page:" + page_name + " (" + page_id + ")");

				page_request_posts_url = '%s%s?fields=posts.since(%s).limit(100)&access_token=%s' % (BASE_URL, page_id, since, ACCESS_TOKEN)
				page_content = requests.get(page_request_posts_url).json();
				
				# There is not any posts since the last month
				if "posts" in page_content:
					page_content = page_content["posts"];
				else:
					continue;

				# There are still posts which haven't been analyzed yet
				while len(page_content["data"]):
					# Categorize each post to the corresponding time range (0 - 23)
					for post in page_content["data"]:
						created_time = create_datetime_from_string(post["created_time"]);

						# if "message" in post:
						# 	spamwriter.writerow([page_id, page_name, post['id'], post['message'], created_time.hour, post['created_time']])
						# elif "story" in post:
						# 	spamwriter.writerow([page_id, page_name, post['id'], post['story'], created_time.hour, post['created_time']])
						spamwriter.writerow([page_id, page_name, page_category, page_location, post['id'], created_time.hour, post['created_time']])
					
					# Get next batch of posts
					if "paging" in page_content:
						page_request_posts_url = page_content["paging"]["next"];
						page_content = requests.get(page_request_posts_url).json();
					else:
						break;
 
			content = get_user_likes(id = user_id, after = content["likes"]["paging"]["cursors"]["after"])

def main():
	content = get_user_friends()
	your_id = content['id']
	your_name = content['name']

	# Retreive your data 
	print("Retreiving data from " + your_name)
	retreive_analyze_data(your_id, your_name)

	# Retreive your friend datas
	while(len(content['friends']['data'])):
		for friend in  content['friends']['data']:
			print("Retreiving data from " + friend['name'])
			retreive_analyze_data(friend['id'], friend['name'])
		content = get_user_friends(your_id, content["friends"]["paging"]["cursors"]["after"])
	

if __name__ =='__main__':
	main()







