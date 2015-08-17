from lxml import etree as ET
import sys
	
def update_log(logPath, changeId, elementName, messageElement):
	parser = ET.XMLParser(remove_blank_text=True)
	logXML = ET.parse(logPath, parser)
	log = logXML.getroot()
	for change in log:
		if change.attrib['id'] == changeId:
			if change.find(messageElement.tag) is None:
				#for adding elements
				change.find(elementName).append(messageElement)
			else:
				#for replacing elements
				tagIndex = change.index(change.find(messageElement.tag))
				change.remove(change.find(messageElement.tag))
				change.insert(tagIndex, messageElement)
	logString = ET.tostring(log, pretty_print=True, xml_declaration=True, encoding="utf-8")
	updateLog = open(logPath, "w")
	updateLog.write(logString)
	updateLog.close()
	
def error(message, dateStart, logPath, changeId, fileName, exceptMsg):
	if len(logPath) > 0:
		status_element = ET.Element('status')
		status_element.text = "error"
		update_log(logPath, changeId, "status", status_element)
	print "ERROR: " + message + "; " + "TIME: " + str(dateStart) + "; " + "ID: " + changeId + "; "+ "FILE: " + fileName + "; " + "MSG: " + str(exceptMsg)
	sys.exit()
	
def file_size(bytes):
	suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
	if bytes == 0: return '0 B'
	i = 0
	while bytes >= 1024 and i < len(suffixes)-1:
		bytes /= 1024.
		i += 1
	f = ('%.2f' % bytes).rstrip('0').rstrip('.')
	return '%s %s' % (f, suffixes[i])
	
def normalize_date(dateString):
	calendar = {'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06', 'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12', 'Spring': '04', 'Summer': '07', 'Fall': '10', 'Autumn': '10', 'Winter': '12'};
	if "-" in dateString:
		if " " in dateString:
			dateStart = dateString.split('-')[0]
			dateEnd = dateString.split('-')[1]
			
		else:
			normalDate = dateString.replace('-', '/')
	else:
		if " " in dateString:
			pass
		else:
			normalDate = dateString
	return normalDate