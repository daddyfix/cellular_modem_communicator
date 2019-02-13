Send MMS/SMS and Recieve SMS from Cellular LTE Modem
----------------------------------------------------

Script sends/receives MMS/SMS Messages to one or more recipients.

Makes a serial connection to a Quectel EC25 LTE modem chipset...

  https://www.quectel.com/product/ec25.htm
  
via Raspberry Pi Hat from SixFab.com..
  
  https://sixfab.com/product/raspberry-pi-3g-4glte-base-shield-v2/
  
and Sixfab.com PCIe module...

  https://sixfab.com/product/quectel-ec25-mini-pcle-4glte-module/
  
Cellular Info
-------------

Country: Canada (Sudbury Ontario)
Micro SIM Service Provider: Rogers.com
Band: North America
APN: ltemobile.apn
Rogers: mms.gprs.rogers.com
Port: /dev/ttyUSB3
  
  
USAGE
-----

optional arguments:

  -h, --help            show this help message and exit

Send Messages
-------------
  
  -r RECIPIENT, --recipient RECIPIENT
  
                        ** Required **
                        
                        Recipient Phone Number (ie. 1705-999-1111).
                        
                        This can be repeated multiple times
                        
  -m MESSAGE, --message MESSAGE
  
                        ** Required **
                        
                        Attach text to MMS message
                        
                        Message can have line feed with \n
                        
  -t TITLE, --title TITLE
  
                        Attach a title to the MMS Message
                        
  -i IMAGE, --image IMAGE
                        Attach a File (ie .jpg .png .gif) or Url to Image file
                        
  -a ALTMSG, --altmsg ALTMSG
                        Alterntive message if image name was given and can not be found
                        
  -p PATH, --path PATH  
                        Default File Path: mms_files/
                        
                        Image File Path: movie_posters/
                        
                        Files must be in either of the above directories
                        
                        unless otherwise specified.
                        
  -b BAUDRATE, --baudrate BAUDRATE
                        Default: 115200
                        
  -o PORT, --port PORT  
                        Default: /dev/ttyUSB3
  
  -d, --debug           
                        Default: False
  --output OUTPUT      
                        json, text, boolean Default: json
  
  Receive SMS Messages
  --------------------
  
  -R, --readsms         Read all the SMS messages recieved
  
  -C, --deletesms       Delete all the SMS messages recieved
 
  -F FORWARDSMS, --forwardsms FORWARDSMS
  
                        Forward all the SMS messages recieved to recipient
                        
  -S SEARCHSMS, --searchsms SEARCHSMS
  
                        Search by Regex all SMS Messages recieved.
                        
                        FYI: '(?i)' in regex expression will turn off case sensitive

Files
-----
        Log File:       logs/cellular_communicator.py.log
        Quectel E25 Chipset Error Codes:
                        errorcodes.py
Note
----
        If Title(-t) and File(-i) are not supplied
        then SMS Message will be used to send
  
