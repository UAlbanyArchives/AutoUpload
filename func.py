from lxml import etree as ET
import os
import sys
import shutil
import datetime
import smtplib
from smtplib import SMTP
	
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
	
def error(message, dateStart, logPath, changeId, fileName, exceptMsg, exceptLine, errorDir, originalFile):
	errorTime = datetime.datetime.now()
	if len(logPath) > 0:
		status_element = ET.Element('status')
		status_element.text = "error"
		update_log(logPath, changeId, "status", status_element)
		error_element = ET.Element('error')
		issue_element = ET.SubElement(error_element, "issue")
		issue_element.text = message
		line_element = ET.SubElement(error_element, "line")
		line_element.text = str(exceptLine)
		exception_element = ET.SubElement(error_element, "exception")
		exception_element.text = str(exceptMsg)
		id_element = ET.SubElement(error_element, "id")
		id_element.text = changeId
		filename_element = ET.SubElement(error_element, "filename")
		filename_element.text = fileName
		time_element = ET.SubElement(error_element, "time")
		time_element.text = str(errorTime)
		update_log(logPath, changeId, "message", error_element)
		shutil.copy2(originalFile, errorDir)
		os.remove(originalFile)
	print "ERROR: " + message + "\n" + "LINE: " + str(exceptLine) + "\n" + "TIME: " + str(errorTime) + "\n" + "CHANGEID: " + changeId + "\n" + "FILE: " + fileName + "\n" + "MSG: " + str(exceptMsg)
	#send error email
	try:
		sender = 'AutoUploadError@gmail.com'
		receivers = ['gwiedeman@albany.edu']
		subject = "AutoUpload Error"
		parser = ET.XMLParser(remove_blank_text=True)
		logXML = ET.parse(logPath, parser)
		log = logXML.getroot()
		for change in log:
			if change.attrib['id'] == changeId:
				bodyText = ET.tostring(change, pretty_print=True)
		if len(bodyText) > 0:
			body = bodyText
		else:
			body = "ERROR: " + message + "\n" + "LINE: " + str(exceptLine) + "\n" + "TIME: " + str(errorTime) + "\n" + "CHANGEID: " + changeId + "\n" + "FILE: " + fileName + "\n" + "MSG: " + str(exceptMsg)
		message = 'Subject: %s\n\n%s' % (subject, body)
		smtpObj = smtplib.SMTP(host='smtp.gmail.com', port=587)
		smtpObj.ehlo()
		smtpObj.starttls()
		smtpObj.ehlo()
		smtpObj.login('AutoUploadError','XXXXXXXXXXXX')
		smtpObj.sendmail(sender, receivers, message)
		smtpObj.quit()
		email_element = ET.Element('emailSuccess')
		email_element.text = "sent error email"
		update_log(logPath, changeId, "message", email_element)
	except smtplib.SMTPException,error:
		print str(error)
		email_element = ET.Element('emailFailed')
		email_element.text = "failed to send error email"
		update_log(logPath, changeId, "message", email_element)
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
	
def date_from_normal(normalDate):
	calendar = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June', '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November', '12': 'December'};
	if "/" in normalDate:
		#date range		
		startDate = normalDate.split('/')[0]
		endDate = normalDate.split('/')[1]
		hyphenCount1 = startDate.count('-')
		if hyphenCount1 == 0:
			displayStart = startDate
		elif hyphenCount1 == 1:
			year = startDate.split('-')[0]
			month = calendar[startDate.split('-')[1]]
			displayStart = year + " " + Month
		elif hyphenCount1 == 2:
			year = startDate.split('-')[0]
			month = calendar[startDate.split('-')[1]]
			dayNormal = startDate.split('-')[2]
			if dayNormal.startswith('0'):
				day = dayNormal[1:]
			else:
				day = dayNormal
			displayStart = year + " " + month + " " + day
		else:
			displayStart = "DateError"
		hyphenCount2 = endDate.count('-')
		if hyphenCount2 == 0:
			displayEnd = endDate
		elif hyphenCount2 == 1:
			year = endDate.split('-')[0]
			month = calendar[endDate.split('-')[1]]
			displayEnd = year + " " + month
		elif hyphenCount2 == 2:
			year = endDate.split('-')[0]
			month = calendar[endDate.split('-')[1]]
			dayNormal = endDate.split('-')[2]
			if dayNormal.startswith('0'):
				day = dayNormal[1:]
			else:
				day = dayNormal
			displayEnd = year + " " + month + " " + day
		else:
			displayEnd = "DateError"
		displayDate = displayStart + "-" + displayEnd
	else:
		#single date
		hyphenCount = normalDate.count('-')
		if hyphenCount == 0:
			if normalDate.lower() == "undated":
				displayDate = "Undated"
			else:
				displayDate = normalDate
		elif hyphenCount == 1:
			year = normalDate.split('-')[0]
			month = calendar[normalDate.split('-')[1]]
			displayDate = year + " " + month
		elif hyphenCount == 2:
			year = normalDate.split('-')[0]
			month = calendar[normalDate.split('-')[1]]
			dayNormal = normalDate.split('-')[2]
			if dayNormal.startswith('0'):
				day = dayNormal[1:]
			else:
				day = dayNormal
			displayDate = year + " " + month + " " + day
		else:
			displayDate = "DateError"
	return displayDate