# -*- coding: utf-8 -*-
from lxml import etree as ET
import os
import sys
import datetime
import hashlib
import shutil
import bagit
from func import file_size
from func import error
from func import update_log
from func import date_from_normal
from validate import validate
import smtplib
from smtplib import SMTP

def AutoUpload(inputDir):

	#inputDir = '//romeo/Collect/AutoUpload'
	faDir = '//romeo/wwwroot/eresources/metadata_testing'
	workingDir = '//romeo/SPE/workflow/AutoUpload_admin/working'
	errorDir = '//romeo/SPE/workflow/AutoUpload_admin/errors'
	adminDir = '//romeo/SPE/workflow/AutoUpload_admin'
	accessDir = '//romeo/wwwroot/eresources/digital_objects'
	presDir = '//romeo/SPE/workflow/AutoUpload_storage'

	parser = ET.XMLParser(remove_comments=True, remove_blank_text=True)
	rep_id = "nam_"


	for inputFile in os.listdir(inputDir):
		if not inputFile.startswith('Thumbs'):
			pass
		else:
			continue
		
		#start date and time
		dateStart = datetime.datetime.now()
		
		#get most recent changeId
		try:
			recentChangeId = 0
			for logYears in os.listdir(adminDir + "/logs"):
				for logMonths in os.listdir(adminDir + "/logs/" + logYears):
					monthXML = ET.parse(adminDir + "/logs/" + logYears + "/" + logMonths, parser)
					month = monthXML.getroot()
					for change in month:
						if int(change.attrib['id']) > int(recentChangeId):
							recentChangeId = change.attrib['id']
			changeId = str(int(recentChangeId) + 1)
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Could not create change ID", dateStart, "", "unable to create changeId", os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)
		
		#create log
		try:
			newYear = str(dateStart).split('-')[0]
			newMonth = str(dateStart).split('-')[0] + "-" + str(dateStart).split('-')[1]
			if not os.path.exists(adminDir + "/logs/" + newYear):
				os.makedirs(adminDir + "/logs/" + newYear)
			if not os.path.isfile(adminDir + "/logs/" + newYear + "/" + newMonth + ".xml"):
				logPath_element = ET.Element('log')
				logPath_element.set('date', newMonth)
				logPathString = ET.tostring(logPath_element, pretty_print=True, xml_declaration=True, encoding="utf-8")
				logPathFile = open(adminDir + "/logs/" + newYear + "/" + newMonth + ".xml", "w")
				logPathFile.write(logPathString)
				logPathFile.close()
			logPath = adminDir + "/logs/" + newYear + "/" + newMonth + ".xml"
			logXML = ET.parse(logPath, parser)
			logRoot = logXML.getroot()
			change_element = ET.SubElement(logRoot, "change")
			change_element.set('id', changeId)
			dateStart_element = ET.SubElement(change_element, "dateStart")
			dateStart_element.text = str(dateStart)
			recordid_element = ET.SubElement(change_element, "recordId")
			status_element = ET.SubElement(change_element, "status")
			status_element.text = "open"
			message_element = ET.SubElement(change_element, "message")
			dateComplete_element = ET.SubElement(change_element, "dateComplete")
			originalRecord_element = ET.SubElement(change_element, "originalRecord")
			changedRecord_element = ET.SubElement(change_element, "changedRecord")
			logString = ET.tostring(logRoot, pretty_print=True, xml_declaration=True, encoding="utf-8")
			createLog = open(logPath, "w")
			createLog.write(logString)
			createLog.close()
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Could not find or create new log entry", dateStart, "", changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)
		
		#get data from upload file's filename
		try:
			uploadFile = os.path.basename(inputFile)
			fileName = os.path.splitext(uploadFile)[0]
			if not fileName.startswith('nam_'):
				raise ValueError("Invalid upload filename, does not begin with 'nam_'.")
			if "---" in fileName:
				recordId = fileName.split('---')[0]
				newMetadata = fileName.split('---')[1]
				uCount = newMetadata.count('_')
				if uCount > 0:
					if uCount == 1:
						newDescription = newMetadata.split('_')[0]
						newDate = newMetadata.split('_')[1]
					elif uCount == 2:
						newDescription = newMetadata.split('_')[0]
						newDate = newMetadata.split('_')[1] + "/" + newMetadata.split('_')[2]
					else:
						raise ValueError("Invalid upload filename, incorrect underscores (_) in date.")
				else:
					newDescription = newMetadata
					newDate = ""
				originalFilename_element = ET.Element('originalFilename')
				originalFilename_element.text = uploadFile
				update_log(logPath, changeId, "message", originalFilename_element)
				if "---" in uploadFile:
					fileExtension = uploadFile.split('.')[-1]
					os.rename(inputDir + "/" + uploadFile, inputDir + "/" + uploadFile.split('---')[0] + "." + fileExtension)
					uploadFile = uploadFile.split('---')[0] + "." + fileExtension
			else:
				recordId = fileName
				newDescription = ""
				newDate = ""
			recordId_element = ET.Element('recordId')
			recordId_element.text = recordId
			update_log(logPath, changeId, "recordId", recordId_element)
			collectionId = recordId.split('-')[0][len('nam_'):]
			fileSize = file_size(os.stat(inputDir + "/" + uploadFile).st_size)
			data_element = ET.Element('data')
			data_element.text = "data read from filename"
			update_log(logPath, changeId, "message", data_element)
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Invalid filename, failed to get data from upload file's filename", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)	
		
		#copy and log original finding aid
		try:
			matchingFindingAid = faDir + "/" + collectionId + ".xml"
			originalHash = hashlib.md5(open(matchingFindingAid, 'rb').read()).hexdigest()
			newYear = str(dateStart).split('-')[0]
			newMonth = str(dateStart).split('-')[0] + "-" + str(dateStart).split('-')[1]
			if not os.path.exists(adminDir + "/findingaids/" + newYear):
				os.makedirs(adminDir + "/findingaids/" + newYear)
			if not os.path.exists(adminDir + "/findingaids/" + newYear + "/" + newMonth):
				os.makedirs(adminDir + "/findingaids/" + newYear + "/" + newMonth)
			FAlogLocation = adminDir + "/findingaids/" + newYear + "/" + newMonth
			shutil.copy2(matchingFindingAid, FAlogLocation)
			FAlogHash = hashlib.md5(open(FAlogLocation + "/" + collectionId + ".xml", 'rb').read()).hexdigest()
			if not FAlogHash == originalHash:
				raise ValueError("Checksum error, log finding aid does not match original finding aid.")
			os.rename(FAlogLocation + "/" + collectionId + ".xml", FAlogLocation + "/" + changeId + "_" + collectionId + ".xml")
			logged_element = ET.Element('logged')
			logged_element.text = "finding aid logged"
			update_log(logPath, changeId, "message", logged_element)
			shutil.copy2(matchingFindingAid, workingDir)
			workingHash = hashlib.md5(open(workingDir + "/" + collectionId + ".xml", 'rb').read()).hexdigest()
			if not workingHash == originalHash:
				raise ValueError("Checksum error, working finding aid does not match original finding aid.")
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Failed to copy and log original finding aid", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)	
		
		
		#create preservation copy
		try:
			uploadHash = hashlib.md5(open(inputDir + "/" + uploadFile, 'rb').read()).hexdigest()
			shutil.copy2(inputDir + "/" + uploadFile, presDir + "/data")
			presHash = hashlib.md5(open(presDir + "/data/" + uploadFile, 'rb').read()).hexdigest()
			if not presHash == uploadHash:
				raise ValueError("Checksum error, file in preservation directory does not match original file.")
			bag = bagit.Bag(presDir)
			bag.info['Last-Updated'] = str(dateStart).split(' ')[0]
			updateManifest = open(presDir + "/manifest-md5.txt", "a")
			updateManifest.write(presHash + "  " + "data/" + uploadFile + "\n")
			updateManifest.close()
			#bag.save(manifests=True)
			preservation_element = ET.Element('preservation')
			preservation_element.text = "preservation file created"
			update_log(logPath, changeId, "message", preservation_element)
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Failed to create preservation copy", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)	
		
		#create access copy
		try:
			if not os.path.exists(accessDir + "/" + collectionId):
				os.makedirs(accessDir + "/" + collectionId)
			shutil.copy2(inputDir + "/" + uploadFile, accessDir + "/" + collectionId)
			access_element = ET.Element('access')
			access_element.text = "access file created"
			update_log(logPath, changeId, "message", access_element)
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Failed to create access copy", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)
		
		
		#update matching record in finding aid
		try:
			updateFindingAid = workingDir + "/" + collectionId + ".xml"
			findingAidXML = ET.parse(updateFindingAid, parser)
			FA = findingAidXML.getroot()
			pi = FA.getprevious()
			repId = "nam_"
			if not FA.attrib['id'] == repId + collectionId:
				raise ValueError("Error matching to Finding Aid, <ead> @id does not match.")
			matchCount = 0
			if "_" in recordId[4:]:
				cmpntId = recordId.split('-')[1].split('_')[0]
				fileId = recordId.split('-')[1].split('_')[1]
				if "." in fileId:
					itemId = fileId.split('.')[1]
				else:
					itemId = ""
			else:
				fileId = ""
				cmpntId = recordId.split('-')[1].split('_')[0]
				if "." in cmpntId:
					itemId = cmpntId.split('.')[1]
				else:
					itemId = ""
			for cmpnt in FA.iter():
				if matchCount > 1:
					raise ValueError("Error matching to Finding Aid, more than one match found.")
				if cmpnt.tag.startswith('c0'):
					if cmpnt.attrib['id'] == recordId:
						if cmpnt.find('did/dao') is None:
							#exact match
							cmpntParent = cmpnt.getparent()
							cmpntIndex = cmpntParent.index(cmpnt)
							match_element = ET.Element('match')
							match_element.text = "exact match found"
							update_log(logPath, changeId, "message", match_element)
							matchCount = matchCount + 1
							update_log(logPath, changeId, "originalRecord", cmpnt)
							physdesc_element = ET.SubElement(cmpnt.find('did'), "physdesc")
							physdesc_element.text = fileSize
							dao_element = ET.Element('dao')
							cmpnt.find('did').append(dao_element)
							dao_element.set('actuate', 'onrequest')
							linkDir = accessDir.replace('//romeo/wwwroot/eresources/', 'http://library.albany.edu/speccoll/findaids/eresources/')
							dao_element.set('href', linkDir + "/" + collectionId + "/" +uploadFile)
							dao_element.set('linktype', 'simple')
							dao_element.set('show', 'new')
							update_log(logPath, changeId, "changedRecord", cmpnt)
							cmpntParent.insert(cmpntIndex, cmpnt)
							break
						else:
							raise ValueError("Error matching to Finding Aid, digital object already found.")
					else:
						#detects last special character to only enable parent matches to be made at item level rather than '.' in series level
						specialCount = 0
						for char in reversed(recordId):
							if char == "_":
								specialCount = 1
								break
							elif char == ".":
								specialCount = 2
								break
						if "." in recordId and specialCount == 2:
							if cmpnt.attrib['id'] == '.'.join(recordId.split('.')[:-1]):
								if cmpnt.find('did/dao') is None:
									#parent match
									cmpntParent = cmpnt.getparent()
									cmpntIndex = cmpntParent.index(cmpnt)
									match_element = ET.Element('match')
									match_element.text = "parent match found"
									update_log(logPath, changeId, "message", match_element)
									matchCount = matchCount + 1
									update_log(logPath, changeId, "originalRecord", cmpnt)
									childElementNumber = int(cmpnt.tag[1:]) + 1
									childElement = ET.Element("c0" + str(childElementNumber))
									cmpnt.append(childElement)
									childElement.set('id', recordId)
									did_element = ET.SubElement(childElement, "did")
									if len(newDescription) > 0:
										unittitle_element = ET.SubElement(did_element, "unittitle")
										unittitle_element.text = newDescription
									else:
										unittitle_element = ET.SubElement(did_element, "unittitle")
										unittitle_element.text = "Item"
									if len(newDate) > 0:
										unitdate_element = ET.SubElement(did_element, "unitdate")
										unitdate_element.text = date_from_normal(newDate.strip())
										unitdate_element.set('normal', newDate)
									dao_element = ET.Element('dao')
									did_element.append(dao_element)
									physdesc_element = ET.SubElement(did_element, "physdesc")
									physdesc_element.text = fileSize
									dao_element.set('actuate', 'onrequest')
									linkDir = accessDir.replace('//romeo/wwwroot/eresources/', 'http://library.albany.edu/speccoll/findaids/eresources/')
									dao_element.set('href', linkDir + "/" + collectionId + "/" +uploadFile)
									dao_element.set('linktype', 'simple')
									dao_element.set('show', 'new')
									update_log(logPath, changeId, "changedRecord", cmpnt)
									cmpntParent.insert(cmpntIndex, cmpnt)
									break
								else:
									raise ValueError("Error matching to Finding Aid, digital object already found.")
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			print exceptMsg
			error("Failed to update record.", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)
		
		#write finding aid to working directory
		try:
			if matchCount == 1:
				FAString = ET.tostring(FA, pretty_print=True, xml_declaration=True, encoding="utf-8", doctype="<!DOCTYPE ead SYSTEM 'ead.dtd'>")
				#insert stylesheet processing instruction
				if isinstance(pi, ET._XSLTProcessingInstruction):
					if "no_series" in str(pi):
						FAoutput = FAString[:38] + "\n<?xml-stylesheet type='text/xsl' href='collection-level_no_series.xsl'?> " + FAString[38:]
					else:
						FAoutput = FAString[:38] + "\n<?xml-stylesheet type='text/xsl' href='collection-level.xsl'?> " + FAString[38:]
				writeFA = open(updateFindingAid, "w")
				writeFA.write(FAoutput)
				writeFA.close()
				write_element = ET.Element('write')
				write_element.text = "finding aid written to working directory"
				update_log(logPath, changeId, "message", write_element)
			elif matchCount == 0:
				raise ValueError("Error matching to Finding Aid, could not find match.")
			else:
				raise ValueError("Error matching to Finding Aid.")
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Error matching to Finding Aid, matchCount variable issue.", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)
		
		#Validate and copy finding aid
		try:
			workingFindingAid = workingDir + "/" + collectionId + ".xml"
			issueCount, issueTriplet = validate(workingFindingAid)
			if issueCount != 0:
				raise ValueError("Updated finding aid did not validate.")
			validate_element = ET.Element('validate')
			validate_element.text = "finding aid validated"
			update_log(logPath, changeId, "message", validate_element)
			shutil.copy2(workingFindingAid, faDir)
			update_element = ET.Element('update')
			update_element.text = "finding aid directory updated"
			update_log(logPath, changeId, "message", update_element)
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Error validating Finding Aid.", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)
		
		#transform finding aid to HTML
		try:
			cmd = "java -cp c:\saxon\saxon9he.jar net.sf.saxon.Transform -t "
			if isinstance(pi, ET._XSLTProcessingInstruction):
				if "no_series" in str(pi):
					cmd = cmd + "-s:" + workingDir + "/" + collectionId + ".xml" + " -xsl:" +  faDir + "/collection-level_no_series.xsl" + " -o:" + workingDir + "/" + collectionId + ".html"
				else:
					cmd = cmd + "-s:" + workingDir + "/" + collectionId + ".xml" + " -xsl:" +  faDir + "/collection-level.xsl" + " -o:" + workingDir + "/" + collectionId + ".html"
				os.system(cmd)
				shutil.copy2(workingDir + "/" + collectionId + ".html", faDir)
				transform_element = ET.Element('transform')
				transform_element.text = "finding aid transformed to HTML"
				update_log(logPath, changeId, "message", transform_element)
			else:
				raise ValueError("Error transforming finding aid, processing instruction error.")
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Error transforming Finding Aid.", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)
		
		#remove files in upload directory and working directory
		try:
			os.remove(inputDir + "/" + uploadFile)
			os.remove(workingDir + "/" + collectionId + ".xml")
			os.remove(workingDir + "/" + collectionId + ".html")
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Error removing upload or working files.", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)
		
		#change status and finalize log
		try:
			status_element = ET.Element('status')
			status_element.text = "complete"
			update_log(logPath, changeId, "status", status_element)
			dateComplete_element = ET.Element('dateComplete')
			dateFinish = datetime.datetime.now()
			dateComplete_element.text = str(dateFinish)
			update_log(logPath, changeId, "dateComplete", dateComplete_element)
		except Exception as exceptMsg:
			exceptLine = sys.exc_traceback.tb_lineno
			error("Failed to finalize log", dateStart, logPath, changeId, os.path.basename(inputFile), exceptMsg, exceptLine, errorDir, inputDir + '/' + uploadFile)