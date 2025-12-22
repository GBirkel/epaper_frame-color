import os, re, sys, logging, traceback, shutil, urllib.request
import xml.dom.minidom
from datetime import tzinfo, timedelta
import client_version


logger = logging.getLogger("epaper_frame")


# Read in the standard configuration file and return its parsed contents
def read_config():
	config = {}
	if os.access("config.xml", os.F_OK):
		config_xml = xml.dom.minidom.parse("config.xml")
		for item in config_xml.documentElement.childNodes:
			if item.nodeType == item.ELEMENT_NODE:
				config[item.tagName] = item.firstChild.data
		return config
	else:
		return None


def set_up_logger():
    logger = logging.getLogger("epaper_frame")
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel("DEBUG")
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)
    return logger


# Subclass of tzinfo swiped mostly from dateutil
class fancytzoffset(tzinfo):
    def __init__(self, name, offset):
        self._name = name
        self._offset = timedelta(seconds=offset)
    def utcoffset(self, dt):
        return self._offset
    def dst(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return self._name
    def __eq__(self, other):
        return (isinstance(other, fancytzoffset) and self._offset == other._offset)
    def __ne__(self, other):
        return not self.__eq__(other)
    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               repr(self._name),
                               self._offset.days*86400+self._offset.seconds)
    __reduce__ = object.__reduce__


# Variant tzinfo subclass for UTC pulled from GPX logs
class fancytzutc(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "UTC"
    def __eq__(self, other):
        return (isinstance(other, fancytzutc) or
                (isinstance(other, fancytzoffset) and other._offset == timedelta(0)))
    def __ne__(self, other):
        return not self.__eq__(other)
    def __repr__(self):
        return "%s()" % self.__class__.__name__
    __reduce__ = object.__reduce__


# Support function to pretty-print dates that datetime can't handle
def pretty_datetime(t):
	# Code loosely adapted from Perl's HTTP-Date
	MoY = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
	mon = t.month - 1
	date_str = '%04d-%s-%02d' % (t.year, MoY[mon], t.day)
	hour = t.hour
	half_day = 'am'
	if hour > 11:
		half_day = 'pm'
	if hour > 12:
		hour = hour - 12
	elif hour == 0:
		hour = 12
	u = t.tzname()
	u_str = ''
	if u is not None:
		u_str = ' ' + u
	time_str = '%02d:%02d%s' % (hour, t.minute, half_day)

	return date_str + ' ' + time_str + u_str


def update_check(pythonPath):
    try:
        logger.info("Current client version: %s" % (client_version.client_version))
        output = Popen(["curl", "-s", "https://garote.bdmonkeys.net/epaper_client/client_version.xml"], stdout=PIPE, stderr=STDOUT).communicate()[0]
        output_text = output.decode('utf-8')
        version_match = re.search(r'<ClientVersion>(\d+)</ClientVersion>', output_text)
        if not version_match:
            logger.error("Could not determine server client version.")
            return
        server_client_version = int(version_match.group(1))
        logger.info("Server client version: %s" % (server_client_version))
        if (server_client_version <= client_version.client_version):
            return
        logger.info('Updating Client from v%s to v%s' % (client_version.client_version, server_client_version))
        zipped_client = urllib.request.urlopen("https://garote.bdmonkeys.net/epaper_client/client.zip")
        zipped_client_file = open(os.path.join(os.path.dirname(__file__), 'client.zip'), "wb")
        shutil.copyfileobj(zipped_client, zipped_client_file)
        zipped_client.close()
        zipped_client_file.close()
        result = call(["unzip", "-o", "-d", ".", "client.zip"])
        #call(["xattr", "-d", "com.apple.quarantine" ,"./client.command"])
        logger.info('Updated to new client version.  Restarting %s' % (' '.join([pythonPath] + sys.argv)))
        os.execv(pythonPath, [pythonPath] + sys.argv)
    except urllib.error.HTTPError as e:
        logger.error("HTTP Error during update check: %s" % (str(e)))
    except urllib.error.URLError as e:
        logger.error("URL Error during update check: %s" % (str(e)))
    except Exception as e:
        s = traceback.format_exception(e)
        logger.error(''.join(s))


if __name__ == "__main__":
   sys.exit()
