#!/usr/bin/env python
"""
onthisday.py - jenni OnThisDay Module
Copyleft 2016, @sairukau
Licensed under GPL2.0

This module reports historical events from multiple sources
"""

import re, urllib2, time, datetime, os
from random import choice
import ConfigParser

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("Could not find BeautifulSoup library,"
                      "please install to use this module")


profiles = { 
            'computerhistoryorg'   :   ["http://www.computerhistory.org/tdih"      ,"/%B/%d/" ],
            'mobygames'             :   ["http://www.mobygames.com/stats/this-day"  ,"/%m%d/" ],
}

## General Options
conf = os.path.join(os.path.expanduser('~/.jenni'),'onthisday.conf')

def buildconfig():
    with open(conf,'w') as f:
        f.write('[options]\nuser_agent=\nchannels=[""]')

def computerhistoryorg(bs, inp):
    title = bs.find('h3', {'class' : 'title'}).getText().split()[2]
    sub = bs.find('p', {'class' : 'subtitle'}).getText().strip()
    text = bs.find('p', {'class' : None }).getText().strip()
    return "On this day in %s, %s %s" % (title, sub, "- "+text)


def mobygames(bs, inp):
    released = {}
    title = ""
    sub = ""
    text = ""
            
    year = bs.findAll('h2')
    releases = bs.findAll('ul', {'id': None, 'class': None})

    for idx, item in enumerate(releases):
        string = item.getText().strip().split('\n')
        relyear = year[idx].getText().strip()

        # push existing list into dict
        released[relyear] = string

    # set title to random
    title = choice(list(released.keys()))
    # also check if the user passed a proper yeard
    if len(inp) > 2:
        if released.has_key(inp[2]):
            title = inp[2]
        else:
            return "Data for %s is not available, available years are %s" % ( inp[2], ', '.join(sorted(released.keys())) )
    sub = choice(released[title])
    return "On this day in %s, %s" % (title, sub)

def helpthisday(jenni, input):
    """ prints a help comment listing the supported categories from the profile keys"""
    jenni.write(['PRIVMSG', input.nick], "[ONTHISDAY] Supported sites are %s (eg: !onthisday mobygames), some sites also support passing the year (eg: !onthisday mobygames 2000)" % ", ".join(profiles.keys()))

helpthisday.commands = ["help","list"]
helpthisday.rule = '\!%s' % helpthisday.commands[0]
helpthisday.priority = 'high'
helpthisday.thread = False



def onthisday(jenni, input):
    """ main function """

    # check config each time, saves reloading script
    if not os.path.exists(conf):
        buildconfig()
        jenni.say("Config created, now edit it")
        return
    else:
        config = ConfigParser.RawConfigParser()
        config.read(conf)

    try:
        user_agent = config.get('options','user_agent')
        channels = config.get('options','channels')
    except:
        jenni.say("Check configuration file")
        return

    nickqueue = []
    if input.sender.lower() in channels:
        # split input on space
        inputspl = input.split()
        
        if input.nick not in nickqueue:
            nickqueue.append(input.nick)
            
            ### select random profile from config
            profile = choice(profiles.keys())
            ### check if we passed an site arg
            if len(inputspl) > 1:
                if profiles.has_key(inputspl[1]):
                    profile = inputspl[1]
                else:
                    jenni.say("Data for %s is not available, Supported sites are %s" % ( inputspl[1], ", ".join(sorted(profiles.keys()))  ))
                    return
            url = "%s%s" % (profiles[profile][0], datetime.date.today().strftime(profiles[profile][1]))

            try:
                # reformat url
                pu = urllib2.urlparse.urlparse(url)
                topurl = "%s://%s" % (pu.scheme, pu.hostname)

                # req url
                req = urllib2.Request(url, headers={'Accept':'*/*'})
                req.add_header('User-Agent', user_agent)
                data = urllib2.urlopen(req).read()
            except urllib2.URLError as e:
                print "ERROR: %s" % e

            # find title
            bs = BeautifulSoup(data, "lxml")


            ######### START CUSTOM DATA PROCESSING
            outstr = globals()[profile](bs, inputspl)
            ######### END CUSTOM DATA PROCESSING

            # end of a sentence
            txtpcs = ""
            sentences = outstr.split('.')
            for sentence in sentences:
                tmppcs = txtpcs + sentence
                if len(tmppcs) >= 450:
                    break
                txtpcs = tmppcs + "."
                
            # output to channel 
            jenni.say(txtpcs)

            # floop prevention
            time.sleep(0.8)
            
            nickqueue.remove(input.nick)
        else:
            wrtout("%s: still processing your crap, wait until we are done" % input.nick)


onthisday.commands = ["onthisday"]
onthisday.rule = '\!%s' % onthisday.commands[0]
onthisday.priority = 'high'
onthisday.thread = False
    
if __name__ == "__main__":
    print __doc__.strip()
