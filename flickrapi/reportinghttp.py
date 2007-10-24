# -*- encoding: utf-8 -*-

'''HTTPHandler that supports a callback method for progress reports.
'''

import urllib2
import httplib
import logging

__all__ = ['urlopen']

logging.basicConfig()
LOG = logging.getLogger(__name__)

progress_callback = None

class ReportingSocket(object):
    '''Wrapper around a socket. Gives progress report
    through a callback function.
    '''
    
    min_chunksize = 10240
    
    def __init__(self, socket):
        self.socket = socket

    def sendall(self, bits):
        LOG.debug("SENDING: %s..." % bits[0:30])
        total = len(bits)
        sent = 0
        chunksize = max(self.min_chunksize, total / 100)
        
        while len(bits) > 0:
            send = bits[0:chunksize]
            self.socket.sendall(send)
            sent += len(send)
            if progress_callback:
                progress = float(sent) / total * 100
                progress_callback(progress, sent == total)
            
            bits = bits[chunksize:]
    
    def makefile(self, mode, bufsize):
        return self.socket.makefile(mode, bufsize)
    
    def close(self):
        return self.socket.close()
    
class ProgressHTTPConnection(httplib.HTTPConnection):

    def connect(self):
        httplib.HTTPConnection.connect(self)
        self.sock = ReportingSocket(self.sock)
        
class ProgressHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        return self.do_open(ProgressHTTPConnection, req)

def set_callback(method):
    global progress_callback # IGNORE:W0603

    if not callable(method):
        raise ValueError('Callback method must be callable')
    
    progress_callback = method

def urlopen(url_or_request, callback, body=None):
    set_callback(callback)
    opener = urllib2.build_opener(ProgressHTTPHandler)
    return opener.open(url_or_request, body)

if __name__ == '__main__':
    def upload(progress, finished):
        LOG.info("%3.0f - %s" % (progress, finished))
    
    conn = urlopen("http://www.flickr.com/", 'x' * 10245, upload)
    data = conn.read()
    LOG.info("Read data")
    print data[:100].split('\n')[0]
    