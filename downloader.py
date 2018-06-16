#!/usr/bin/env python2
import re
import urllib2
import mechanize
import getpass
import os
import cgi
import time
import sys

# Prompts
WEBSITE_STR = "Please enter the website to download: "
USR_STR = "Please enter the user name: "
PASSWORD_STR = "Please enter the password: "
ATTRIBUTE_STR = "Please enter the attribute to search: "
VALUE_STR = "Please enter the value: "
KEY_STR = "Please enter the keyword to search: "
LAYER_STR = "Do you want to search the next layer? [y/N] "
SEARCH_OPT_STR = ("Please enter search option (default to 2): "
                  "\n1) search by attribute 2) search by keyword: ")
LOGIN_STR = "Do you want to login? [y/N] "

# A routine to login a website.
def login(br):
  # Check if login needed.
  if len(br.forms()) == 0:
    login = raw_input(LOGIN_STR)
    if login == 'y':
      br.follow_link(url_regex=re.compile('login'))
    else:
      return

  while True:
    # Select html form and fill in the login name and password.
    br.select_form(nr=0)
    ori_name = br.form.name
    br.form.find_control(type='text').value = getpass.getpass(USR_STR)
    br.form.find_control(type='password').value = getpass.getpass(PASSWORD_STR)
    br.submit()

    # check login status by comparing the forms
    if len(br.forms()) == 0 or ori_name != list(br.forms())[0].name:
      print "Successfully log in!\n"
      return br
    else:
      print "User name or password is not correct!\n"

# This function asks user input for searching option.
def ask_option():
  global attri, value
  while True:
    option = raw_input(SEARCH_OPT_STR)
    if option == '1':
      attri = raw_input(ATTRIBUTE_STR)
      value = raw_input(VALUE_STR)
      if not attri or not value:
        print "Attribute and value cannot be empty!!!\n"
      else:
        break
    else:
      value = raw_input(KEY_STR)
      if not value:
        print "Keyword cannot be empty!!!\n"
      else:
        attri = 'string'
        break;

# This function simulates the links method of the mechanize.Browser class with
# standardized parameters.
def find_links(url, br, attri, value):
  br.open(url)
  if attri == 'string':
    link_list = br.links(text_regex=re.compile(value))
  else:
    link_list = br.links(predicate=lambda link: (attri, value) in link.attrs)
  return link_list

# A routine to download a file from a link by simulating a click on it.
def download(br, link):
  global size
  linkUrl = link.absolute_url
  try:
    response = br.open(linkUrl)
  except Exception as e:
    print "\x1b[2K\rUnexpected error: " + str(e)
    return

  # Extract filename from either the header or url.
  cdheader = response.info().getheader('Content-Disposition')
  if cdheader:
      value, params = cgi.parse_header(cdheader)
      filename  = params["filename"]
  else:
      filename = urllib2.unquote(os.path.basename(response.geturl()))
  sys.stdout.write("\x1b[2K\rDownloading " + filename)
  sys.stdout.flush()

  # Write the content to local file.
  f = open(filename, "w") # open a local file
  f.write(response.read()) # write the response content to disk
  f.close()
  size += os.path.getsize(filename)

try:
  global attri, value, size
  url = raw_input(WEBSITE_STR)
  br = mechanize.Browser()
  br.open(url)
  br = login(br)

  while True:
    # Search the first layer.
    ask_option()
    links = list(find_links(url, br, attri, value))
    if len(links) == 0:
      print "No result found!\n"
      f = open("htmldoc", "w")
      f.write(br.response().read())
      f.close()
      continue

    # Search the second layer.
    layer = raw_input(LAYER_STR)
    if layer == 'y':
      print
      ask_option()
      print("Searching...")
      print("Please be patience.")
      start = time.time()
      link_url = map(lambda x: x.absolute_url, links)
      links = []
      for url in link_url:
        links += find_links(url, br, attri, value)
      end = time.time()
      print "Search using time", "%.2f" % (end - start), "seconds.\n"

    if len(links) == 0:
      print "No result found!\n"
      continue
    else:
      print str(len(links)) + " results found!\n"

    # Download all the files.
    size = 0
    start = time.time()
    for link in links:
      download(br, link)
    end = time.time()
    print "\x1b[2K\r" + "="*80 + "\n"
    print "Download using time", "%.2f" % (end - start), "seconds."
    print "Total size of files downloaded:",
    if size/pow(2, 10) == 0:
      print str(size), "bytes.\n"
    elif size/pow(2, 20) == 0:
      print str(size/pow(2, 10)), "KBs.\n"
    else:
      print str(size/pow(2, 20)), "MBs.\n"
except EOFError:
  print
except KeyboardInterrupt:
  print
except mechanize._mechanize.BrowserStateError:
  print "URL not valid!"
except mechanize._mechanize.LinkNotFoundError:
  print "Cannot find link!"
