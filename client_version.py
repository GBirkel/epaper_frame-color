#!/usr/bin/python

import os, xml.dom.minidom

versionFilePath = os.path.join(os.path.dirname(__file__), 'client_version.xml')
parsedVersionFile = xml.dom.minidom.parse(versionFilePath)
client_version = int(parsedVersionFile.getElementsByTagName('ClientVersion')[0].firstChild.wholeText)

if __name__ == '__main__':
	print(client_version)