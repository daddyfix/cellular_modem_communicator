#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" ----------------------------------------------------------

    Install Modules if not installed

---------------------------------------------------------- """
import pip, time, sys
for im in ["serial", "humanfriendly", "magic", "python-dateutil", "Pillow"]:
    try:
        pkg = im
        if 'dateutil' in im:
            pkg='dateutil'
        elif 'Pillow' in im:
            pkg='PIL'
        globals()[pkg] = __import__(pkg)
    except ImportError:
        if 'Pillow' in im:
            print("Cannot install Pillow via pip install")
            print("Please install via ...")
            print("sudo apt-get install python-imaging")
            sys.exit()
        print("Installing "+im+" module...")
        pip.main(['install', im])
        time.sleep(2)


""" ------------------------------------------------------------

    Import Modules

-------------------------------------------------------------"""
# PySerial
import serial
import serial.tools

# System
import datetime
from datetime import timedelta
import dateutil
from dateutil import parser
from dateutil import tz
import inspect
import os
import logging
import glob
import json
import time

# Convertions
import humanfriendly
import magic
import PIL
from PIL import Image

#sys.exit()
# Load Python file as args
import ast

# Regex
import re

# Parse the Arguments passed to this script
import argparse

# URL/Web Functions
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import urllib.parse

# Database
import sqlite3
from sqlite3 import Error

# Run Linux Scripts
import subprocess

#Global Variables
ser = 0
debug = False
output_types = [ 'json', 'text', 'boolean' ]
default_type = 0
errorcodes =  False
textfile_holder=''
imagefile_holder=''
gConn=None
SMSAction = []
SMSForward = ''

# Paths and Log Filenames
filename = inspect.getframeinfo(inspect.currentframe()).filename
filepath = os.path.dirname(os.path.abspath(filename))+'/mms_files/'
imagepath = 'movie_posters/'
filebase = os.path.splitext(filename)[0]
logfile = 'logs/cellular_communicator.py.log'
sendlist = 'logs/text-message-sent-list.txt'
errorCodesFile = os.path.dirname(os.path.abspath(filename))+'/errorcodes.py'
atfile = os.path.dirname(os.path.abspath(filename))+'/at_commands.txt'
DBFILE = 'database/cellular_communicator.sqlite.db'

# Connection Details
default_baudrate='115200'
default_port='/dev/ttyUSB3'

logging.basicConfig(filename=logfile,level=logging.DEBUG)
#logging.debug('This message should go to the log file')
#logging.info('So should this')
#logging.warning('And this, too')

# Trim files
rc = subprocess.call("echo \"$(tail -n 150 "+logfile+")\" > "+logfile, shell=True)
rc = subprocess.call("echo \"$(tail -n 150 "+atfile+")\" > "+atfile, shell=True)
rc = subprocess.call("echo \"$(tail -n 150 "+sendlist+")\" > "+sendlist, shell=True)

"""
QUERY/SET MMS SETTINGS

Change the below to match your mobile providers settings

Each dict has 4 parts
desc - description of the AT Command
query - AT Command to query a setting
expected - search string for valid response
correct - AT Command to set the Setting to desired Params
"""
modem={}
modem[0]    = { 'desc' : 'APN details',
                    'query': 'AT+QICSGP=1', 
                    #'expected': '"fast.tmobile.com","",""', 
                    #'correct': 'AT+QICSGP=1,1,"fast.tmobile.com","","",0'}
                    'expected': '"NXTGENPHONE","",""',
                    'correct' : 'AT+QICSGP=1,1,"NXTGENPHONE","","",0'}
modem[1]    = { 'desc' : 'Context ID',
                    'query': 'AT+QMMSCFG="contextid"', 
                    'expected': '"contextid",1', 
                    'correct': 'AT+QMMSCFG="contextid",1'}
modem[2]    = { 'desc' : 'Mult Media Service Centre',
                    'query': 'AT+QMMSCFG="mmsc"', 
                    #'expected': 'mms.msg.eng.t-mobile.com/mms/wapenc', 
                    #'correct': 'AT+QMMSCFG="mmsc", "http://mms.msg.eng.t-mobile.com/mms/wapenc"'}
                    'expected': 'mmsc.mobile.att.net',
                    'correct': 'AT+QMMSCFG="mmsc", "http://mmsc.mobile.att.net"'}
modem[3]    = { 'desc' : 'Provider Proxy Details',
                    'query': 'AT+QMMSCFG="proxy"',
                    'expected': '172.26.39.1',
                    'correct': 'AT+QMMSCFG="proxy","172.26.39.1",80'}
                    #'expected': '149.254.201.135',
                    #'correct': 'AT+QMMSCFG="proxy","149.254.201.135",80'}

'''
modem[4]    = { 'desc' : 'Character Set',
                    'query': 'AT+QMMSCFG="character"', 
                    'expected': 'UTF8', 
                    'correct': 'AT+QMMSCFG="character","UTF8"'}
'''
modem[5]    = { 'desc' : 'Send Parameters',
                    'query': 'AT+QMMSCFG="sendparam"', 
                    'expected': '6,3,0,0,2,4', 
                    'correct': 'AT+QMMSCFG="sendparam",6,3,0,0,2,4'}
modem[6]    = { 'desc' : 'Support Field',
                    'query': 'AT+QMMSCFG="supportfield"', 
                    'expected': '"supportfield",0', 
                    'correct': 'AT+QMMSCFG="supportfield",0'}                
char_ascii={}
char_ascii[0]= { 'desc' : 'Character Set',
                    'query': 'AT+QMMSCFG="character"', 
                    'expected': 'ASCII', 
                    'correct': 'AT+QMMSCFG="character","ASCII"'}


""" -------------------------------------------------------

    Database Functions

-------------------------------------------------------- """
def init_db_connection():
    global gConn

    if not os.path.isfile(DBFILE):
        debug_msg("- Sqlite Database: "+DBFILE+" does not exist. Creating DB...")
        gConn = sqlite3.connect(DBFILE)
        os.chmod(DBFILE, 0o766)
        create_table()
    elif gConn == None:
        debug_msg("- SQlite File Found: "+DBFILE)
        gConn = sqlite3.connect(DBFILE)

def get_db_connection():
    if gConn == None:
        init_db_connection()
    return gConn

def close_db_connection():
    global gConn
    if gConn != None:
        debug_msg("Closing DB Connection...")
        gConn.close()
        gConn = None
    
def get_cursor():
    if gConn == None:
        init_db_connection()
    return gConn.cursor()

def create_table(commit=True):
    #cur = get_cursor()
    get_db_connection().execute(
        ''' CREATE TABLE IF NOT EXISTS send (
                                        id integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                                        recipient text,
                                        title text,
                                        message text,
                                        image text,
                                        sent integer NOT NULL DEFAULT 0,
                                        tries integer NOT NULL DEFAULT 1,
                                        start_date text,
                                        sent_date text
                                    ); ''' 
        )

def table(action, details):

    do_sql=True
    if 'insert' in action:
        data = get_tuple_values(["recipient", "title", "message", "image"], details)
        data = data + (get_date() ,)
        SQL_CMD = '''INSERT INTO send(recipient, title, message, image, start_date) VALUES(?,?,?,?,?)'''

    elif 'update' in action:
        data = get_tuple_values(["sent", "tries"], details)
        if details['sent'] == 1:
            data = data + (get_date() ,)
        else:
            data = data + ('',)
        data = data + (details['id'] ,)
        SQL_CMD = '''UPDATE send SET sent = ?, tries = ?, sent_date = ? WHERE id = ?'''

    elif 'delete' in action:
        days = int(details['days'])
        data = get_past_date(days)
        # DELETE FROM "send" WHERE "sent_date" < "2018-06-18 21:45:13"
        SQL_CMD = '''DELETE FROM send WHERE sent_date < ?'''

    else:
        do_sql=False

    if do_sql:
        # dynamically detect parameter type: tuple/list/string
        conn = get_db_connection()
        cur = get_cursor()

        debug_msg("Submitting SQL")
        debug_msg(" - "+SQL_CMD)

        do_commit = True
        if type(data) == list:
            cur.executemany(SQL_CMD, data)
        elif type(data) == tuple:
            cur.execute(SQL_CMD, data)
        elif type(data) == str:
            cur.execute(SQL_CMD, (data,))
        else:
            # unkown type
            do_commit = False
            pass
        if do_commit:
            conn.commit()
            return cur.lastrowid
    else:
        return False
        

def get_date():
    return (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def get_past_date(val):
    past = datetime.datetime.now() - timedelta(days=val)
    return (past.strftime("%Y-%m-%d %H:%M:%S"))

""" --------------------------------------------------------------
    Database Functions END
-------------------------------------------------------------- """


""" --------------------------------------------------------------

    Image Manipulatiion

--------------------------------------------------------------- """
def resize_image(filename, size=400):
     img = Image.open(filename)
     img.thumbnail((size,size))
     img.save(filename,optimize=True,quality=96)

"""
Make a list from a dictionary
"""
def get_list_values(mylist, details):

    newlist=[]
    for a in mylist:
        if a in details:
            newlist.append(details[a])

    return newlist

"""
Make a tuple from a dictionary
"""
def get_tuple_values(mylist, details):

    newtuple=()
    for a in mylist:
        if a in details:
            newtuple= newtuple + (details[a] ,)

    return newtuple

"""
Print Messages to the screen and logfile
"""
def debug_msg(mystr, linefeed = True):

    mystr = str(mystr)
    if debug:
        sys.stdout.write(mystr)

        if linefeed:
           sys.stdout.write("\n")

        sys.stdout.flush()

    logging.debug(get_date()+" ::: "+mystr)
    print(mystr)


"""
Send Output to console as json, text, boolean, then exit
"""
def output_close(mystr, error = False):

    global output_index

    mystr = str(mystr)
    if error:
        scode = 'fail'
        skey = 'error'
    else:
        scode = 'success'
        skey = 'result'

    # print "output_index="+str(output_index)

    if output_index == 0:
        # if mystr is in format [ ... ] then its a json string. dont quote json array
        if '[' in mystr[0] and ']' in mystr[-1]:
            print('{"status":"'+scode+'","'+skey+'":'+mystr+'}')
        else:
            print('{"status":"'+scode+'","'+skey+'":"'+mystr+'"}')
    elif output_index == 1:
        print(scode)
    
    close()
    if not error:
        sys.exit(0)
    else:
        sys.exit(1)



"""
Print Messages to the screen and logfile
"""
def debug_msg_sql(sql, mylist):

    mysql = " - SQL: "+str(sql)
    myvals = " - Values: "+', '.join(map(str,mylist))

    if debug:
        sys.stdout.write(mysql+"\n")
        sys.stdout.write(myvals+"\n")
        sys.stdout.flush()

    logging.debug(mysql)
    logging.debug(myvals)


"""
Print Messages to a File
"""
def save_at_command(mystr):
    if mystr.find('AT+') > -1:
        with open(atfile, "a") as f:
            f.write(mystr+"\n")

"""
Print sent list to a File
"""
def save_send_details(mystr):
    format = "%a %b %d %H:%M:%S"
    d = datetime.datetime.today().strftime(format)
    with open(sendlist, "a") as f:
        f.write(d+" ::: "+mystr+"\n")


"""
Print Messages to a File
"""
def save_date(myfile):
    format = "%a %b %d %H:%M:%S"
    d = datetime.datetime.today().strftime(format)
    with open(myfile, "a") as f:
            f.write("------------------------------\n"+d+"\n------------------------------\n")


"""
Make date as filename
"""
def get_date_as_filename():
    fn = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return fn

""" ---------------------------------------------------------

    Serial Communications

--------------------------------------------------------- """

"""
Function to Initialize the Serial Port
"""
def init_serial():

    global ser          # Must be declared in Each Function

    ser = serial.Serial()

    ser.baudrate = args['baudrate']

    # enable hardware control
    ser.rtscts = False
    
    ser.port = args['port']

    #Specify the TimeOut in seconds, so that SerialPort
    #Doesn't hangs
    ser.timeout = .5

    # -----------------------------------
    # Check is the Serial Port is being used 
    # -----------------------------------
    cmd = "sudo lsof | grep "+ser.port

    while True:
        p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        output = p.communicate()[0]
        if output:
            msg = 'Serial Port ' + str(ser.port) + ' ' + str(ser.baudrate) + ' is being used by ...'
            debug_msg(msg)
            output = str(output)
            txt = output.split('\n')
            for line in txt:
                if line:
                    val = line.split()
                    msg = str(val[0]) + ' PID: ' + str(val[1])
                    debug_msg(msg)

            debug_msg("Trying again in 60 seconds...")
            time.sleep(60)  # Try again in 1 minute

            # msg = 'Serial Port ' + str(ser.port) + ' ' + str(ser.baudrate) + ' is being used, Aborting. Check ' + logfile
            # output_close(msg, True)
        else:
            msg = 'Serial Port ' + str(ser.port) + ' ' + str(ser.baudrate) + ' seems to be free to use'
            debug_msg(msg)
            ser.open()      #Opens SerialPort
            break

        # print port open or closed
    if ser.is_open:
        debug_msg('Openned: ' + str(ser.name) + ", baud: "+str(ser.baudrate))        # .name is the port connection

#Function Ends Here


"""
Read from the Serial Port
"""
def serial_read(search='OK', mytimeout=3, length=1000):
    
    ret = {}
    ret['search'] = search
    ret['read'] = ''
    curr_time = time.time()
    while True:
        holder = ser.read(length)
        print(holder)
        print(search)
        ret['read'] += str(holder)
        if search in ret['read']:
            ret['status']="Serial Read Search '"+search+"' Found."
            ret['success']=True
            return ret
        if time.time()-curr_time >= mytimeout:
            ret['status']="Serial Read Search Timed Out."
            ret['success']=False
            return ret


"""
 Read/Clear/Forward Recieved SMS Messages

 args [readall|clear|PHONE|Filter]

 # AT+CMGR=1
# +CMGR: "REC READ","9000",,"18/08/04,14:03:31+00"
# Rogers svc msg: Your payment on your 15 /month plan was received. Thank you.

# OK
# AT+CMGL="ALL"

"""
def sms_actions(lst):

    jsonstr = ''
    jsonclr = ''

    if 'readall' or 'forwardsms' in lst:

        debug_msg('sms_actions: ReadALL: Set SMS message format as text mode')
        # Set SMS message format as text mode
        at_command('AT+CMGF=1')

        debug_msg('sms_actions: ReadALL: Getting all messages in bulk')
        ret = at_command('AT+CMGL="ALL"', ok='OK', timeout=10, length=1000)

        jsonstr = parse_raw_sms(lst, ret['read'])

    if 'clear' in lst:

        debug_msg('sms_actions: clear: ** Deleting All Recieved Messages **')
        # Get a list of all the messages we are deleting
        ret = at_command('AT+CMGD=1,4', ok='OK', timeout=2, length=30)

        # Check for zereo messages
        ret = at_command('AT+CMGL="ALL"', ok='OK', timeout=5, length=300)
        if 'OK' in ret['read']:
            jsonclr = json.dumps(['SMS Messages Cleared'])
        else:
            jsonclr = json.dumps(['ERROR: '+ret['read']])

    if not jsonstr:
        return jsonclr
    elif 'ERROR' in jsonclr:
        return jsonclr
    else:
        return jsonstr
    

"""
 Parse raw sms messages recieved into nice array of messages

 arg list of SMSAction. ie 'readall|forwardsms|clear|searchsms'
 arg string Raw sms messages separated by line

 return json string
"""
def parse_raw_sms(lst, msgstring=''):

    debug_msg('parse_raw_sms: Parsing Raw SMS Message...')
    nextLineisMsg=False
    searchLineFound=True  # make very line Saveable unless 'searchsms'
    searchFromFound=True
    result=[]
    item={}
    mysearch="+CMGL:"
    txt = msgstring.split('\n')

    for line in txt:
        if len(line) > 0 and "+CMGL:" in line[:6]:
            parts = [x.strip() for x in line.split(",")]
            i = [y.strip() for y in parts[0].split(" ")]
            item["id"] = i[1].strip("\"")
            item["from"] = parts[2].strip("\"")
            
            if 'searchsms' in lst:
                debug_msg(" - Searching From: "+item["from"]+" for "+SMSSearch)
                ftr=re.search(SMSSearch, item["from"])
                if not ftr:
                    debug_msg("   - Not Found")
                    searchFromFound=False
                else:
                    debug_msg("   - Found")
            searchLineFound=True   # set search to True for next call

            # date is YY/MM/DD and Time is UTC 24:24:00+00
            dt = parts[4].strip("\"") + ' ' +parts[5].strip("\"").split('+')[0]
            debug_msg(" - Converting UTC date ["+dt+"] to EST")
            dateobj = datetime.datetime.strptime(dt, '%y/%m/%d %H:%M:%S')
            # Set Time zone from UTC to EST
            from_tz = tz.gettz('UTC')
            to_tz = tz.gettz('US/Eastern')
            dateobj = dateobj.replace(tzinfo=from_tz)
            dateobj = dateobj.astimezone(to_tz)
            debug_msg(" - New Local Datetime: "+str(dateobj))
            prettydate = dateobj.strftime('%b %d %Y %I:%M %p')
            debug_msg(" - Stored Date as: "+prettydate)
            item["datetime"] = prettydate
            nextLineisMsg=True

        elif len(line) > 0 and nextLineisMsg:
            if 'searchsms' in lst:
                debug_msg(" - Searching Line: "+re.sub('\r','',line)+" for "+SMSSearch)
                ftr=re.search(SMSSearch, line)
                if not ftr:
                    debug_msg("   - Not Found")
                    searchLineFound=False
                else:
                    debug_msg("   - Found")
            
            if searchLineFound or searchFromFound:
                # remove \r and multiple spaces in line
                tmpstr=re.sub('\r','',line)
                tmpstr=re.sub(' +',' ',tmpstr)
                item["msg"]=tmpstr
                result.append(item)

            item={}
            nextLineisMsg=False
            searchFromFound=True    # set search From to True for next call    

    debug_msg("parse_raw_sms: "+str(len(result))+" lines found")

    return json.dumps(result, indent=4) 

"""
 Edit the MMS Message
 Recipients -> AT+QMMSEDIT=<function>,<option>,<optstring> 
 command('AT+QMMSEDIT=1,1,<optstring>')

Integer type function.
0 - Delete all
1 - Operate “TO address”
2 - Operate “CC address”
3 - Operate “BCC address”
4 - Operate title
5 - Operate file as attachment
Integer type option
0 - Delete the specific setting
1 - Config the specific Setting
String optstring
string - if function is 1,2,3,4 then TO, CC, BCC, Title STRING Address
string - if function is 5 then filename of attachement
         ie. AT+QMMSEDIT=5,1,"RAM:test_pic.jpg"

Query the setting command('AT+QMMSEDIT=4')
"""
def create_message(recipient, message, image='', title='', altmsg=''):

    global textfile_holder
    global imagefile_holder
    details = {}

    if not recipient:
        debug_msg('create_message: Recipient cannot be empty')
        close()
    elif not message:
        debug_msg('create_message: Message cannot be empty')
        close()

    if not (10 <= len(recipient) <= 11):
        output_close("Phone number "+recipient+" is too long or short", True)

    # Clear all MMS Messages
    clear_entries()

    debug_msg("Creating MMS Message")

    # TO     
    at_command('AT+QMMSEDIT=1,1,"'+recipient+'"') # to phone no.
    debug_msg(' - Recipient: '+recipient)
    details['recipient']=recipient

    # Attach Title
    if title:
        at_command('AT+QMMSEDIT=4,1,"'+title+'"')
        debug_msg(' - Title: '+title)

    details['title']=title

    # Attach Image
    if image:
        debug_msg(' - Image: '+image)        
        imagefile_holder = upload_file(image, False, True)
        if not imagefile_holder:
            debug_msg(' - Image was not found')
            if altmsg:
                debug_msg(' - Substituting Message with Alternate Message: '+altmsg)
                message = altmsg

    details['image']=image

    # Attach Message
    # we keep the textfile path and name so we can delete later
    # debug_msg(' - Message before make_text_file: '+message)
    textfile = make_text_file(message)
    textfile_holder = upload_file(textfile, True)
    debug_msg(' - Message: '+message)
    details['message']=message

    return details

#Function Ends Here  


"""
Function that writes and reads from serial until timeout occurs.
msg == AT command to execute
timeout == is the time until end execution
ok == is the desired AT print
end == ending ascii character
"""
"""
THIS IS THE OLDER COMMAND THAT DELT WITH TWO TYPES OF MSG
VARS, 1-STRING & 2-LIST
THIS HAS BEEN DISABLED
def command(msg, timeout=2, ok='OK', end=13):

    # if list then break it down. See Array lists at the top os script
    if type(msg) is list:
        #t0 = time.time()
        while True:
            # send the query
            ret = command_str(msg[0], timeout, msg[1], end)

            # if the query response was not found, send set AT command
            if not ret['success']:
                debug_msg("Sending Command: "+msg[2])
                ret = command_str(msg[2], ok='OK')

            return ret

            #if time.time()-t0 >= timeout:
            #    debug_msg("Timeout while executing command: "+msg[0])
            #    return false

    ret = command_str(msg, timeout, ok, end)
    return ret
#Function Ends Here
"""

"""
Write a command to Serial Port
Wait for a response
Check the response
If response is expected return TRUE
If response is abnormal then write command to Serial and recheck it

arg list of dicts
    dicts must have keys, query, expected, correct
"""
def verify_settings(mylist):

    for k0 in mylist:
        for k1, v1 in list(mylist[k0].items()):
            if 'desc' in k1:
                desc = v1
            elif 'query' in k1:
                query = v1
            elif 'expected' in k1:
                expected = v1
            elif 'correct' in k1:
                correct = v1

        debug_msg("Checking: "+desc, False)
        # save_at_command(msg)
        ser.write((query+chr(13)).encode())
        ret = serial_read('OK')
        print(ret)
        if ret['success'] == False:
            debug_msg(" [ FAILED ]")
            debug_msg(" - Response: "+ret['status'])
            close()
        if expected not in ret['read']:
            debug_msg(" [ FAILED ]")
            debug_msg(" - Setting...")
            debug_msg(" - Setting: "+correct, False)
            ser.write((correct+chr(13)).encode())
            ret = serial_read('OK')
            if not ret['success']:
                debug_msg(" [ FAILED ]")
                debug_msg(" - Response: "+ret['status'])
                close()
            else:
                debug_msg(" [ OK ]")
        else:
            debug_msg(" [ OK ]")
# Function Ends Here
            


"""    
Same as function command but msg is string
"""
def at_command(msg, ok='OK', timeout=30, length=1000):

    if ser.is_open:
        save_at_command(msg)

        # t0 = time.time()
        #while True:
        ser.write((msg+chr(13)).encode())
        ret = serial_read(ok, timeout, length)

        if not ret['success']:
            debug_msg('AT Command Failed: '+msg)
            debug_msg(""+ret['status'])
            debug_msg("Error Code: "+error_code(ret['read']))
            debug_msg("Response: \n"+ret['read'])

        return ret


# Function Ends Here

"""
Download an image file from the web
"""
def download_image(url):
    
    global mtype

    debug_msg("Downloading: "+url)

    # make a new filename
    base = os.path.basename(urllib.parse.urlparse(url).path)
    
    if len(base) > 15:
        ext = os.path.splitext(base)[1]
        time_string = str(int(time.mktime(time.localtime())))
        base = (time_string+ext).lower()

    # if base is empty
    elif not base:
        base = get_date_as_filename()

    myfile = filepath+base

    debug_msg("Downloading Image: "+url)

    # Some files can't be downloaded without a User-agent Header. We have to make one
    # http://www.hanedanrpg.com/photos/hanedanrpg/14/65194.jpg
    hdr = urllib.request.Request(url, None, {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5'})

    try: 
        imgData = urllib.request.urlopen(hdr, timeout=2).read()

    except urllib.error.HTTPError as e:
        myerr = 'Downloading Image HTTPError = ' + str(e.code)
        output_close(myerr, True)

    except urllib.error.URLError as e:
        myerr = 'Downloading Image URLError = ' + str(e.reason)
        output_close(myerr, True)

    except httplib.HTTPException as e:
        myerr = 'Downloading Image HTTPException'
        output_close(myerr, True)

    except Exception:
        import traceback
        myerr = 'Downloading Image generic exception: ' + traceback.format_exc()
        output_close(myerr, True)

    debug_msg("Saving file as: "+myfile)
    output = open(myfile,'wb')
    output.write(imgData)
    output.close()

    # check if image downloaded
    img_types = ['image/gif', 'image/jpg', 'image/png', 'image/jpeg']
    mtype = magic.from_file(myfile, mime=True)
    debug_msg("Image File Type: "+ mtype)
    if not mtype in img_types:
        debug_msg("Image type: "+mtype+" is not a valid image type. Aborting.")
        return False

    # check the mime type with the file ext
    mimeext = mtype.split('/',1)[1]
    myfileext = os.path.splitext(myfile)[1]
    if mimeext != myfileext:
        if 'jpg' in myfileext:
            debug_msg("Mime type jpg is OK as jpeg")
        else:
            newfile = myfile+'.'+mimeext
            debug_msg("New Filename: "+newfile)
            os.rename(myfile, newfile)
            myfile = newfile

    size=500
    while True:
        s = getFilesize(myfile)
        if s > 90000:
            debug_msg(" - Size too large, resizing...")
            resize_image(myfile, size)
            size = size - 50
        else:
            break

    return myfile
# Function Ends Here


"""
Upload a File to RAM

arg - string filename (must be in filepath)
arg - boolean true for ASCII, null or false for binary (ie. jpg)

upload_file('AT+QFUPL="RAM:'+fl+'",'+s+',300,1', connect=fl)
"""
def upload_file(file, ascii=False, clear_attachments=False):
    
    if 'http' in file:
        myfile = download_image(file)
        if not myfile:
            debug_msg("File: "+file+" could not be downloaded.")
            debug_msg("Check url or check the file in "+filepath+", its a "+str(mtype)+" mime type!")
            close()
    else:
        myfile = file


    # strip all but filename
    debug_msg("Getting basename from: "+myfile)
    base = os.path.basename(myfile)

    # look for an extention. if none then glob search in image path
    extension = os.path.splitext(base)[1]
    if not extension:
        myfile = imagepath+base+"*"
        debug_msg("Searching for file: "+myfile+" ...")
        result = glob.glob(myfile)
        if result:
            debug_msg(" - Found: "+result[0])
            myfile = result[0]
            base = os.path.basename(myfile)
        else:
            debug_msg(" - Not found")
            return False
    else:
        debug_msg("Searching for filename: "+myfile+"...")
        if not os.path.isfile(myfile):
            debug_msg(" - "+myfile+" does not exist. Searching...")
            debug_msg("Searching for filename: "+base+" ...")
            myfile = filepath+base
            if not os.path.isfile(myfile):
                debug_msg(" - "+myfile+" does not exist. Searching...")
                myfile = imagepath+base
                if not os.path.isfile(myfile):
                    debug_msg(" - "+myfile+" does not exist. Searching...")
                    myfile = file
                    if not os.path.isfile(myfile):
                        debug_msg(" - "+myfile+" does not exist. Exiting")
                        return False
                        
        debug_msg("-  Found "+myfile)

    size = str(os.path.getsize(myfile))
  
    if ( size == os.path.getsize(myfile) ):
        print("File "+myfile+" size is zero. Exiting.")
        close()

    # attach the text file
    if ascii:
        verify_settings(char_ascii)

    """
    Read the Binary/Ascii File in to memory
    """
    with open(myfile, "rb") as binary_file:
        # Read the whole file at once
        data = binary_file.read()
        #print(data)


    """
    AT+QFUPL="RAM:test_mms.txt",100,300,1
        100 - the maximum size of file in bytes
        300 - indicates timeout value
        1 - indicates ACK mode.
    """
    count=1
    while True:
        upl='AT+QFUPL="RAM:'+base+'",'+size+',300,1'
        debug_msg("Uploading: "+base)
        ret = at_command(upl, ok='CONNECT')

        if not ret['success']:
            if '407' not in ret['read']:
                close()
            elif count > 2:
                debug_msg("Could not Upload after 2 tries")
                clear_ram()
                close()
            else:
                debug_msg("Deleting File and trying Again...")
                clear_ram()
                count+=1
        else:
            break

    # Send the Binary/Text data
    ser.write(data)
    ret = serial_read('OK')

    if size in ret['read']:
        #debug_msg(ret)
        debug_msg(" - Uploaded "+size+" bytes to RAM")

        # Clear all Attachments
        if clear_attachments:
            debug_msg(" - Clearing RAM Attachements")
            at_command('AT+QMMSEDIT=5,0')

        # Attach the File to query
        at_command('AT+QMMSEDIT=5,1,"RAM:'+base+'"')
        # Query the attachment
        result = at_command('AT+QMMSEDIT=5')
        if result['success']:
            mylist = [search_string(result['read'], '+QMMSEDIT: 5')]
            for ln in mylist:
                debug_msg(ln)
        else:
            debug_msg("Nothing was uploaded. Check Logs")

        return myfile
    else:
        debug_msg(ret['read'])
        return False
# Function ends here


"""
Get the size of a file
"""
def getFilesize( myfile='' ):

    if not os.path.isfile(myfile):
        debug_msg("File: "+myfile+" does not exist")
        close()

    size = os.path.getsize(myfile)
    sizestr = humanfriendly.format_size(size)
    debug_msg(" - Size: "+str(size)+" bytes or "+sizestr)
    
    return size
# Function Ends Here

"""
Clear Ram and Querys
"""
def clear_all():

    clear_ram()
    clear_entries()
# End Function Here

"""
Clear RAM
"""
def clear_ram(check=False):

    if check:
        tries = 0
        while True:
            l = at_command('AT+QFLST="RAM:*"', 'OK', 5)
            nlines = l['read'].count('\n')
            debug_msg("RAM files found in memory: "+str(nlines))
            if nlines > 2:
                if ( tries > 2 ):
                    debug_msg(" - Cannot Delete RAM.")
                    debug_msg(" - Powering down Cellular Modem normally")
                    at_command('AT+QPOWD=1', 'OK', 10)
                    debug_msg(" - Reboot RPi3 in 1 minute")
                    rc = subprocess.call("shutdown -r +1", shell=True)
                    ser.close()
                    sys.exit()

                debug_msg(" - Deleting RAM one-by-one")
                filescount = 0
                tries += 1
                ll = l['read'].splitlines()
                for aline in ll[:]:
                    if '+QFLST:' in aline:
                        filen = re.findall(r'"RAM:(.+?)"',aline)
                        debug_msg("  "+str(filescount+1)+" DEL: "+str(filen[0]))
                        at_command('AT+QFDEL="RAM:'+str(filen[0])+'"', 'OK', 10)
                        filescount += 1

            else:
                break

    else:     
        # Clear the RAM
        at_command('AT+QFDEL="RAM:*"', 'OK', 5)

# End Function Here

"""
Clear Entrys
"""
def clear_entries():
    
    # Clear all querys
    at_command('AT+QMMSEDIT=0')
# End Function Here


"""
Look up an error code in a file list and display description
"""
def error_code(mystr):

    global errorcodes

    if not errorcodes: 
        if not os.path.isfile(errorCodesFile):
            debug_msg(" - File: "+errorCodesFile+" does not exist")
            close()

        with open(errorCodesFile, 'r') as f:
            errorcodes = ast.literal_eval(f.read())

    txt = mystr.split('\n')
    for line in txt:
        if 'ERROR' and re.findall('\d+',line):
            #debug_msg("Error Found: "+line)
            err=re.findall('\d+',line)
            for key,value in errorcodes: 
                if key in err:
                    return value
                    break
    return "(unknown)"
#Function Ends Here


"""
Look for Lines in string and print them
"""
def search_string(mystring, mysearch):

    results=[]
    txt = mystring.split('\n')
    for line in txt:
        if mysearch in line:
            results.append(line)

    if not len(results):
        return False

    return results


"""
Make a text file from a string
"""
def make_text_file(mystr):

    time_string = str(int(time.mktime(time.localtime())))
    fn = filepath+time_string+'.txt'
    f = open(fn, 'w+')
    #debug_msg("make_text_file: Making Message text File: "+mystr)
    f.write(str(mystr.replace('\\n', '\n')))
    f.close

    if not os.path.isfile(fn):
        debug_msg("Error: "+fn+" could not be created")
        close()

    debug_msg("Created: "+fn)

    return fn
#Function Ends Here

"""
Delete a File

 - Only delete files in the filepath. Images from another location
    should not be deleted
"""
def delete_file(myfile):

    # strip all but filename
    base = os.path.basename(myfile)
    myfile = filepath+base
    #if file exists, delete it
    if os.path.isfile(myfile):
        ## try to delete file ##
        try:
            os.remove(myfile)
        except OSError as e:  ## if failed, report it back to the user ##
            debug_msg("Error: %s - %s." % (e.filename,e.strerror))
            return False

        debug_msg("Deleted: "+myfile)
        return True
#Function Ends Here

"""
Send Message
"""
def send_message(details):
 

    recid = table('delete', {'days':30})
    recid = table('insert', details)
    details['id'] = recid
    details['sent']=0
    details['tries']=0

    count=1

    while True:
        debug_msg("Trying to Send MMS (attempts: "+str(count)+")")
        result = at_command('AT+QMMSEND=20', '+QMMSEND: 0,200')

        if not result['success']:
            debug_msg(" - Send Message FAILED")

            if count > 3:
                debug_msg(" - Attempted 3 times... Aborting.")
                return False
            else:
                count += 1
                details['tries'] = count
                table('update', details)
        else:
            debug_msg(" - Success")
            details['sent'] = 1
            table('update', details)
            return True

# Function Ends Here


"""
Close and end program
"""
def close():
    
    global textfile_holder
    global imagefile_holder

    close_db_connection()

    debug_msg('Clearing RAM & Entries...')
    clear_all()

    debug_msg('Closing Connection...')
    if ser.is_open:  
        ser.close()   # close serial port
        if ser.is_open:
            debug_msg(' - Failed')
    else:
        debug_msg(' - Not open, therefore close not neccessary')


    #debug_msg("Deleting Text File...")
    delete_file(textfile_holder)

    if imagefile_holder:
        #debug_msg("Deleting Image File...")
        delete_file(imagefile_holder)

    debug_msg('Done.')

    #sys.exit()    # exit program is done in output_close()
#Function Ends Here



"""
----------------------------------------------------------

    MEAT AND POTATOES

----------------------------------------------------------
"""

"""
Usage
"""
s="""
Files
-----
        Log File:       {log}
        Quectel E25 Chipset Error Codes:
                        {error}
Note
----
        If Title(-t) and File(-i) are not supplied
        then SMS Message will be used to send
Author
------
        Michael Connors
        daddyfix@outlook.com
                
""".format( log=logfile,
            error=errorCodesFile
)
parser = argparse.ArgumentParser(
                description='Script to send MMS/SMS Messages to one or more recipients',
                formatter_class=argparse.RawTextHelpFormatter,
                epilog=(s)
)

#----------------------------------------------------------
# Group args as optional but One must be selected

#-----------------------------------------------------------

#-----------------------------------------------------------
# Regular Args
#-----------------------------------------------------------
parser.add_argument('-r','--recipient', help="""** Required **
Recipient Phone Number (ie. 1705-999-1111).
This can be repeated multiple times
""", required=False)
parser.add_argument('-m','--message', help="""** Required **
Attach text to MMS message
Message can have line feed with \\n""", required=False)
parser.add_argument('-t','--title', help='Attach a title to the MMS Message', required=False)
parser.add_argument('-i','--image', help='Attach a File (ie .jpg .png .gif) or Url to Image file', required=False)
parser.add_argument('-a','--altmsg', help='Alterntive message if image name was given and can not be found', required=False)
mystr="""
Default File Path: {files}
Image File Path: {images}
Files must be in either of the above directories
unless otherwise specified.
""".format(files=filepath,
           images=imagepath
)
#parser.add_argument('-S','--readsms', action='store_true', help="Read all the SMS messages recieved", required=False)
parser.add_argument('-p','--path', help=mystr, required=False)
parser.add_argument('-b','--baudrate', help='Default: '+default_baudrate, required=False)
parser.add_argument('-o','--port', help='Default: '+default_port, required=False)
parser.add_argument('-d','--debug', action='store_true', help='Default: '+str(debug), required=False)
parser.add_argument('--output', help=(', '.join(output_types))+' Default: '+str(output_types[default_type]), required=False)
#-----------------------------------------------------------
# Read SMS Recieved
# ----------------------------------------------------------
parser.add_argument('-R','--readsms', action='store_true', help="Read all the SMS messages recieved", required=False)
parser.add_argument('-C','--deletesms', action='store_true', help="Delete all the SMS messages recieved", required=False)
parser.add_argument('-F','--forwardsms', help="Forward all the SMS messages recieved to recipient", required=False)
parser.add_argument('-S','--searchsms', help="Search by Regex all SMS Messages recieved.\nFYI: '(?i)' in regex expression will turn off case sensitive", required=False)
#parser.add_argument('-R','--readlast', help="", required=False)



# Add all the Command Line args to array(list)
args = vars(parser.parse_args())

if args['readsms']:
    SMSAction.append('readall')
    #print "Read all SMS"
if args['deletesms']:
    SMSAction.append('clear')
    #print "Clear all SMS"
if args['forwardsms']:
    SMSAction.append('forwardsms')
    SMSForward = args['forwardsms']
    #print "Good: "+args['forwardsms']
if args['searchsms']:
    if not 'readall' in SMSAction and not 'forwardsms' in SMSAction:
        print("If using Search (--searchsms)...\nMust have (-F 7059992222) or Read All (-R)")
        sys.exit()
    SMSAction.append('searchsms')
    SMSSearch = args['searchsms']
if args['recipient'] is None or args['message'] is None:
    if not SMSAction:
        print("Must have a Recipient (-r) and Message (-m) OR --help")
        sys.exit()


# set the defaults
if not args['baudrate']:
    args['baudrate'] = default_baudrate
if not args['port']:
    args['port'] = default_port
if not args['output']:
    output_index = default_type
else:
    if args['output'] in output_types:
        output_index = output_types.index(args['output'])
    else:
        print("The output type: "+args['output']+' is not one of '+(', '.join(output_types)))
        sys.exit()
if args['debug']:
    debug = True


#print "Output: "+str(output_index)+": "+output_types[output_index]
#sys.exit()

"""
Save Date to Files
"""
save_date(logfile)
save_date(atfile)

# ---------------------------- START ----------------------------

#create_connection()
#close_db_connection()
#sys.exit()

"""

Call the Serial Initilization

"""
init_serial()

"""

Check Connection Params

"""
verify_settings(modem)
verify_settings(char_ascii)
clear_ram(True)

debug_msg( "Args Given: "+str(args)[1:-1] )

if 'readall' in SMSAction:
    jsonstr = sms_actions(SMSAction)
    if 'Error' in jsonstr:
        output_close(jsonstr, True)
        #print '{"status":"fail","error":"'+jsonstr+'","result":"'+jsonstr+'"}'
    else:
        if ( len(jsonstr) == 2 ):
            jsonstr = "There are no new messages"
        #print '{"status":"success","result":"'+jsonstr+'"}'
        output_close(jsonstr)

elif 'forwardsms' in SMSAction:
    jsonstr = sms_actions(SMSAction)
    jdata = json.loads(jsonstr)

    msgstr = ''
    output = ''
    err = False
    counter = 0
    limit = 2
    totalsms=0

    for a in jdata:

        totalsms += 1
        # convert cell number to only digits
        recipient = re.findall(r'\d+', a['from'])[0]

        msgstr += "From: "+recipient+"\n"+a['datetime']+"\n"+a['msg']

        if ( counter == limit ):
            counter = 0
            details_dict = create_message( str(SMSForward), str(msgstr) )
            status = send_message(details_dict)
            if not status:
                s = ( a['id'] - limit )
                output = "*** Error Sending Messages Ids "+str(s)+" thru "+str(a['id'])+": "+status+" ***"
                debug_msg(str(output))
                err = True
            else:
                output = "Sent Ids "+str(s)+" thru "+str(a['id'])+" OK"
                debug_msg(str(output))
            msgstr = ''
        else:
            counter += 1
            msgstr +="\n"

    if msgstr:
        details_dict = create_message( str(SMSForward), str(msgstr) )
        status = send_message(details_dict)
        numlines = len(msgstr.split('\n'))
        if not status:
            output = "*** Error Sending Last "+str(numlines)+" Messages: "+status+" ***"
            debug_msg(str(output))
            err = True
        else:
            output = "Sent Last "+str(numlines)+" Messages OK"
            debug_msg(str(output))

    if err:
        output_close('There were errors sending the SMS messages to '+str(SMSForward)+'. Check '+logfile, True)
        #print '{"status":"fail","result":"There were errors sending the SMS messages to '+str(SMSForward)+'. Check '+logfile+'"}'
    else:
        output_close(str(totalsms)+' SMS Messages Forwarded to '+str(SMSForward))
        #print '{"status":"success","result":"'+str(len(jsonstr))+' SMS Messages Sent"}'

elif 'clear' in SMSAction:
    jsonstr = sms_actions(SMSAction)
    if 'Error' in jsonstr:
        output_close(jsonstr, True)
        #print '{"status":"fail","error":"'+jsonstr+'","result":"'+jsonstr+'"}'
    else:
        output_close(jsonstr)
        #print '{"status":"success","result":"'+jsonstr+'"}'


"""

Create a Message and Send

"""
details_dict = create_message(args['recipient'], args['message'], args['image'], args['title'], args['altmsg'])

status = send_message(details_dict)

if not status:
    msg = "*** Error Sending Message: "+status+" ***"
    debug_msg(str(msg))
    output_close(str(msg), True)
    
else:
    msg = "Sent OK"
    debug_msg(str(msg))

    # Add an entry to the sent messages list file
    message = args['message']
    if args['image']:
        if args['altmsg']:
            message = args['altmsg']

    senddetails = args['recipient']+" -> "+message
    save_send_details(senddetails)
    output_close(str(msg))
