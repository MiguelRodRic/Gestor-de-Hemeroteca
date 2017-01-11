# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 18:17:14 2016

@author: Miguel
"""
#In this example, we want to obtain the number of views of a determined youtube video

#Library 
import urllib2

#set the url:
url = "https://www.youtube.com/watch?v=svngvOLPd5E"

#Create a request
request = urllib2.Request(url)

#Now, we can create a handle which we can read out later
handle = urllib2.urlopen(request)

#Read content
content = handle.read()

#split into array
splitted_page = content.split("<div class=\"watch-view-count\">", 1);

#Again
splitted_page = splitted_page[1].split("</div>", 1)

totalViews = splitted_page[0]

print totalViews

#As Youtube has a similar Front End for any video, this could possibly work
#for any video that you would like to know its views