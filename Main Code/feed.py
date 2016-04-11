"""Module to create objects for the elements Classes based in a specific plain
text format. More information in utils/docx_format.txt"""

import re
import json
from papofeed import elements, extractor

QUESTION_ID_PREFIX = 'q.'
TYPE_ATTR_JSON = 'json'
#[MEMO] or [TEXTBOX] or [NUMERICAL] or [INSERT] or [|(.*|)+] or [:(.*:)+]
PLAIN_TEXT_TAGS_REGEX = '((\[MEMO\]|\[TEXTBOX\]|\[NUMERICAL\]|\[\|(.*\|)+\]|\[:(.*:)+\]|\[INSERT\])(?:\{([^}]*)\})?)'

#line = current line
#id attribute
def replace_with_json(line, id_attr=''):
  """For each line of the plain text string, replaces the SPECIAL FIELDS with
  JSON code described in utils/questionnaire_tag_description.docx"""

  embedded_json_letter = 'a'
  match = re.search(PLAIN_TEXT_TAGS_REGEX, line) #A match object
  def json_validation():
    #TODO: We need to extract 'default' from here and up to cloze
    validation = {} #a dictionary
    if(match.group(5)):
      validation_pairs = match.group(5).split(";;") #delinieated using ;
      for validation_pair in validation_pairs:
        validation_pair = validation_pair.split("::") #delinieated using :
        #TODO: should I really remove these spaces?
        validation[re.sub('^( )+|( )+$', '', validation_pair[0])] = re.sub('^( )+|( )+$', '', validation_pair[1])
    return validation

  while(match):#while the match object is found
    embedded_json = {}
    cloze = {}
    cloze['id'] = id_attr + '.' + embedded_json_letter
    embedded_json['cloze'] = cloze
    if(match.group(2) == '[MEMO]'):
      validation = json_validation()
      cloze['type'] = 'memo'
      if(validation):
        if(validation.has_key('default')):
          cloze['default'] = validation.pop('default')

        if(validation):
          cloze['validation'] = validation

      line = re.sub('\[MEMO\](\{([^}]*)\})?', json.dumps(embedded_json), line, 1)

    if(match.group(2) == '[TEXTBOX]'):
      validation = json_validation()
      cloze['type'] = 'textbox'
      if(validation):
        if(validation.has_key('default')):
          cloze['default'] = validation.pop('default')

        if(validation):
          cloze['validation'] = validation

      line = re.sub('\[TEXTBOX\](\{([^}]*)\})?', json.dumps(embedded_json), line, 1)

    if(match.group(2) == '[NUMERICAL]'):
      validation = json_validation()

      cloze['type'] = 'numerical'
      if(validation):
        if(validation.has_key('default')):
          cloze['default'] = validation.pop('default')

        if(validation):
          cloze['validation'] = validation

      line = re.sub('\[NUMERICAL\](\{([^}]*)\})?', json.dumps(embedded_json), line, 1)

    if(re.search('\[\|(.*\|)+\]', match.group(1))):
      validation = json_validation()
      cloze['type'] = 'select one'
      options = match.group(3).split('|')
      options.pop() #removes last '|'
      cloze['options'] = options
      if(validation):
        if(validation.has_key('default')):
          cloze['default'] = validation.pop('default')

        if(validation):
          cloze['validation'] = validation

      line = re.sub('\[\|(.*\|)+\](\{([^}]*)\})?', json.dumps(embedded_json), line, 1)

    if(re.search('\[:(.*:)+\]', match.group(1))):
      validation = json_validation()
      cloze['type'] = 'select multi'
      options = match.group(4).split(':')
      options.pop() #removes last ':'
      cloze['options'] = options
      if(validation):
        if(validation.has_key('default')):
          cloze['default'] = validation.pop('default')

        if(validation):
          cloze['validation'] = validation

      line = re.sub('\[:(.*:)+\](\{([^}]*)\})?', json.dumps(embedded_json), line, 1)

    if(match.group(2) == '[INSERT]'):
      embedded_json = {}
      insert = {}
      mod = {}
      insert_attributes = ['cref','qref','math','count','separator']
      validation = json_validation() #stores the qref
      if(validation): #if the qref exists
        for key in validation.iterkeys():
          if(key in insert_attributes):
			if(key == 'separator'):
			  newKey = validation[key]
			  newKey = newKey[1:-1]
			  validation[key] = newKey
			  insert[key] = validation[key]
			else:
			  insert[key] = validation[key]
          else:
            mod[key] = validation[key]
        if(mod):
          insert['mod'] = mod
      else:
        #TODO
        raise Exception
      embedded_json['insert'] = insert
      line = re.sub('\[INSERT\](\{([^}]*)\})?', json.dumps(embedded_json), line, 1)

    embedded_json_letter = chr(ord(embedded_json_letter) + 1)
    match = re.search(PLAIN_TEXT_TAGS_REGEX, line)

  return line

def parse(plain_text):
  
  """find_nth(haystack, needle, n)
  Input: haystack(the string), needle(item to look for), (the occurance # to look for)
  Output: Integer position
  Functionality: returns the index(start) of the nth occurrence of character needle in string haystack """
  def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start
  
  """
  replaceRegCatDelinForMod
  Convert :: delins in regular Category Mod statements to : delineators
  """
  def replaceRegCatDelinForMod(convertedRegularCategoryArray):
	
	#loop through list
	index = 0
	for regCatSyntax in convertedRegularCategoryArray: #insertSyntax is a Str
		#convert to list, replace :: with :, then convert back to string
		regCatString = regCatSyntax.replace("::", ":")
		convertedRegularCategoryArray[index] = regCatString
		index = index + 1
	return convertedRegularCategoryArray
  
  """convertRegCatToXML
  Input: Array of stripped raw categories
  Output: Array of regular categories with the values in the input array held in double quotes
  Functionality: Converts each item in the input array into a list, inserts double quotes at the end and beginning of the qref value,
  turns it back into a string, and adds it to an array of converted regular category that it then returns.
  """
  def convertRegCatToXML(convertedRegularCategoryArray):
	counter = 0
	convertedRegularCategoryArray = replaceRegCatDelinForMod(convertedRegularCategoryArray)
	while(counter < len(convertedRegularCategoryArray)):
	  rawText = list(convertedRegularCategoryArray[counter])
	  rawText.insert(0,'"')
	  rawText.insert(rawText.index(':'), '"')
	  convertedCategoryText = ''.join(rawText)

	  if(convertedCategoryText[len(convertedCategoryText)-1:] == "}"):
		convertedRegularCategoryArray[counter] = convertedCategoryText + "}}"
	  else:
	    convertedRegularCategoryArray[counter] = convertedCategoryText
	  counter += 1
	return convertedRegularCategoryArray

  """
  replaceDelineatorsForMod
  Convert :: delins in mod statements to : delineators
  """
  def replaceInsertDelinForMod(convertedInsertArray):
	
	#loop through list
	index = 0
	for insertSyntax in convertedInsertArray: #insertSyntax is a Str
		#convert to list, replace :: with :, then convert back to string
		insertString = insertSyntax.replace("::", ":")
		insertString = insertString.replace(";;", ",")
		convertedInsertArray[index] = insertString
		index = index + 1
	return convertedInsertArray
  
  def convertInsertArrayToXML(convertedInsertArray):
	#must check if the word endModType is present at the end of the string. If so, then the quotes are singles and add a " after the ending }}
    #if begModType is at the end, no ending }}
	#remove begModType and endModType Text, add quotes
	counter = 0
	convertedInsertArray = replaceInsertDelinForMod(convertedInsertArray)
	while (counter < len(convertedInsertArray)):
	  convertedInsertArray[counter] = convertedInsertArray[counter].replace(" ", "")
	  rawText = convertedInsertArray[counter]
	  if(rawText.startswith("StartIns")):
	    #StartIns[INSERT]{qref:q.4.6.4}
		#To: {"insert": {"qref":"q.4.6.4",
		#    {"insert": {"qref":"q.4.6.4",
		rawText = rawText.replace("StartIns[INSERT]{","{\"insert\": {")
		
		listText = rawText[rawText.find("qref"):-1]
		listPairs = listText.split(",")
		moddedListPairs = []
		numPairs = len(listPairs)
		rawText = rawText[:-1] + ","
		a = 0
		while(a < numPairs):
		  moddedListPairs.append("\"" + listPairs[a][:listPairs[a].find(":")] + "\"" + listPairs[a][listPairs[a].find(":"):listPairs[a].find(":")+1] + "\"" + listPairs[a][listPairs[a].find(":")+1:] + "\"")
		  rawText = rawText.replace(listPairs[a], moddedListPairs[a])
		  a = a + 1
		convertedInsertArray[counter] = rawText
	  elif(rawText.startswith("middleMod")):
		rawText = rawText[rawText.find("[INSERT]"):]
		rawText = rawText.replace("[INSERT]", "{'insert':") #insert changes
		rawText = rawText + "}" #ending brace
		listText = rawText[rawText.find("qref"):-2]
		listPairs = listText.split(",")
		moddedListPairs = []
		numPairs = len(listPairs)
		a = 0
		while(a < numPairs):
		  moddedListPairs.append("'" + listPairs[a][:listPairs[a].find(":")] + "'" + listPairs[a][listPairs[a].find(":"):listPairs[a].find(":")+1] + "'" + listPairs[a][listPairs[a].find(":")+1:] + "'")
		  rawText = rawText.replace(listPairs[a], moddedListPairs[a])
		  a = a + 1
		convertedInsertArray[counter] = rawText + "\""
	  elif(rawText.startswith("Reg")):
		rawText = rawText[rawText.find("[INSERT]"):]
		#numFields = rawText.count(",") + 1
		rawText = rawText.replace("[INSERT]", "{\"insert\":") #insert changes
		rawText = rawText + "}" #ending brace
		
		listText = rawText[rawText.find("qref"):-2]
		listPairs = listText.split(",")
		moddedListPairs = []
		numPairs = len(listPairs)
		
		a = 0
		while(a < numPairs):
		  moddedListPairs.append("\"" + listPairs[a][:listPairs[a].find(":")] + "\"" + listPairs[a][listPairs[a].find(":"):listPairs[a].find(":")+1] + "\"" + listPairs[a][listPairs[a].find(":")+1:] + "\"")
		  rawText = rawText.replace(listPairs[a], moddedListPairs[a])
		  a = a + 1
		convertedInsertArray[counter] = rawText
	  else:
	    raise Exception("Uh oh, there's something wrong with the insert formatting. Check convertedInsertArray")
	  counter = counter + 1

	return convertedInsertArray
	
  def replaceArrayWithXML(fullStatement, originalStrings, convertedStrings):
    counter = 0
    arrayPos = 0
	#CURRENT PROBLEM:REPLACES ALL IF SOME ARE THE SAME. SOLUTION: EACH TIME, MAKE SURE TO ONLY RELPACE THE FIRST INSTANCE
    while(counter < len(fullStatement) and arrayPos < len(originalStrings)):#loop through the line
	  originalString = originalStrings[arrayPos]
	  convertedString = convertedStrings[arrayPos]
	  if(originalString in fullStatement):#check to see if the reg category is in the original line. Replace the first instance
		fullStatement = fullStatement.replace(originalString, convertedString, 1)
		arrayPos += 1
	  counter += 1  

    return fullStatement
  
  """cleanupFinalStatement(String fullStatement)
  Input: the converted line with a few errors still remaining
  Output: the final string, ready for writing"""
  def cleanupFinalStatement(fullStatement): #Gets rid of [ in mods and adds a ' {' to ending mod inserts.
	#raise Exception(fullStatement)
	#add 2 ending brackets to a mod - find the index of a mod, then the index of the 3rd ending bracket.
	#find index of mod - make string from mod start to end.
	fullStatement = re.sub("\[MOD\]", "\"mod\":", fullStatement)
	modInsertPos = []
	
	#find all mod inserts
	for modIndex in list(re.finditer("{'insert'", fullStatement)):
	  modInsertPos.append(modIndex.start())

	#now get delete everything up to and including the nearest "
	counter = 0
	while(counter < len(modInsertPos)):
	  tempString = fullStatement[:modInsertPos[counter]]
	  if(tempString[len(tempString)-1:len(tempString)] == "{"):
	    raise Exception("There is an error with your MOD statement. MOD statements cannot have an INSERT statement as the first thing in their contents. This creates a parsing error with JINJA2. Currently, MOD statements must start with a qrefContents::Text pair. ")
	  deleteTo = tempString.rfind("\"")
	  deleteToContentsLen = modInsertPos[counter] - deleteTo
	  
	  fullStatement = fullStatement[:deleteTo] + fullStatement[deleteTo+deleteToContentsLen:]
	  
	  #counteracts modInsertPos value being wrong after changing fullStatement
	  if(counter+1 < len(modInsertPos)): 
	    modInsertPos[counter+1] = modInsertPos[counter+1] - deleteToContentsLen
	  counter += 1
	
	#fullStatement = fullStatement + "}}"
	return fullStatement

  """linePreProcessing(string line)
  need to get rid of whitespace after :: sequences in the mod statement line
  """
  def linePreProcessing(line):
	#find all of the matches
	pairMatches = re.findall("\w*::\s*\"", line)
	numMatches = len(pairMatches) #finds # of MOD qref/label pairs.
	changedMatches = []
	
	#iterate through matches
	for match in pairMatches:
	  changedMatches.append(re.sub(" ","", match))
	
	#then loop through all matches again, and sub in the changed ones using re.sub
	counter = 0
	while counter < numMatches:
	  line = re.sub(pairMatches[counter], changedMatches[counter], line)
	  counter = counter + 1
	
	return line
  
  """removeInsertWS
  need to get rid of white-space between the end of an insert and non-white-space character. 
  """
  def removeInsertWS(line):
	#Find all the inserts + 3 characters afterwards.
	#If any are spaces or tabs, sub with ""
	linePosition = 0
	lineLength = len(line)
	originalInsertList = []
	while (linePosition < lineLength):
	  if (linePosition + 2 < lineLength):
	    firstChar = line[linePosition]
	    secondChar = line[linePosition+1]
	    thirdChar = line[linePosition+2]
	    checkInsertSequence = firstChar + secondChar + thirdChar
	    if(checkInsertSequence == '[IN'): #Once we find an insert 	 
		  placeholderString = line[linePosition:] #placeholder string holds the start of an index to the end of the array
		  startOfInsertString = placeholderString[:placeholderString.index('}')+3]#The entire insert
		  originalInsertList.append(startOfInsertString)
	  linePosition += 1
	
	counter = 0
	modifiedInsertList = []
	while(counter < len(originalInsertList)):
	  modifiedInsertList.append(re.sub(" ", "", originalInsertList[counter]))
	  line = line.replace(originalInsertList[counter], modifiedInsertList[counter])
	  counter +=1
	
	return line
  
  def convertToXML(line, mod):
	line = linePreProcessing(line)
	lineLength = len(line)
	fullStatement = line
	
	insertArray = []
	convertedInsertArray = []
	modArray = []
	convertedModArray = []
	regularCategoryArray = []
	convertedRegularCategoryArray = []
	modStringForSkipping = ""
	
	linePosition = 0

	"""Mod stuff, including the inserts in Mod"""
	#Look for MOD or REGULAR CATEGORY. First step: search the line for the mod segment location
	while (linePosition < lineLength):
	  if (linePosition + 2 < lineLength):
	    colonChar = line[linePosition]
	    spaceChar = line[linePosition+1]
	    dQuoteChar = line[linePosition+2] #these hold three characters as the loop goes through the string
	    checkModSequence = colonChar + spaceChar + dQuoteChar
	    if(checkModSequence == '::"'): #once it finds the specific 3 character sequence
		  tempSubString = line[:linePosition]
		  lastQIndex = tempSubString.rfind('q.')
		  modOrRegularString = line[lastQIndex-1:] #so now  we have the mod string to the end, starting at the first {
		  
		  #handle whitespace issues for mod endings
		  #replace \ } and } } with nonwhitespace versions
		  modOrRegularString = re.sub("\"\s}","\"}", modOrRegularString)
		  modOrRegularString = re.sub("}\s}","}}", modOrRegularString)
		  
		  #so for the ending of the mod statement, we need to find the position of the end of the mod string
		  dqB = modOrRegularString.find("\"}") #Either find the closest one - means you can't have "} or }}
		  bB = modOrRegularString.find("}}")
		  if(dqB > -1 and bB > -1):
			posList = [dqB, bB]
			endModIndex = min(posList)
		  elif(dqB == -1 and bB == -1):
		    raise Exception("Mod Syntax is incorrect")
		  else: 
		    if(dqB > bB):
			  endModIndex = dqB
		    elif(bB > dqB):
			  endModIndex = bB
		    else:
			  raise Exception("Uh oh, bug in the code.")
		  	  
		  modOrRegularString = modOrRegularString[:endModIndex+2]#the full mod statement!
		  #raise Exception(modOrRegularString)
		  modStringForSkipping = modOrRegularString #we use this later to skip over the rest of the mod statement within the text parsing loop.
		  
		  #get rid of inserts so that we can detect the ends of the regular categories using ", and endModIndex value for the last one
		  numInserts = modOrRegularString.count("[INSERT]")
		  while(numInserts):
		  
			insertIndex = modOrRegularString.find("[INSERT]")
			tempString = modOrRegularString[insertIndex:]
			endInsertIndex = tempString.find("}")
			insertString = modOrRegularString[insertIndex:insertIndex+endInsertIndex+1] #the entire insert chunk
			
			#now do the modifying and saving business.
			insertArray.append(insertString)
			markedInsertString = "middleMod" + insertString
			convertedInsertArray.append(markedInsertString)
			
			#also remove it from the line
			#find position of index in mod string
			insertIndexInMod = modOrRegularString.find(insertString)
			modIndexInLine = line.find(modOrRegularString)
			#find position of modstring in line
			#remove insert by substringing line[:modstart+insertstart] + line[modstart+insertstart+insertlength:]
			line = line[:modIndexInLine+insertIndexInMod] + line[modIndexInLine+insertIndexInMod+len(insertString):]
			lineLength = len(line)

			#then remove it from modOrRegularString
			modOrRegularString = modOrRegularString[:insertIndexInMod] + modOrRegularString[insertIndexInMod + len(insertString):]
	
			numInserts = numInserts - 1

		  modOrRegularString = re.sub("\"\s,", "\",", modOrRegularString) #to make sure ", exist. May be " , otherwise.
		  
		  #{q.4.6.4.D::"Special Characters: ", q.4.6.4.E::"Numbers", q.4.6.4.B::"Lowercase Letters", q.4.6.4.C::"Letters", q.4.6.4.A::"Uppercase letters"}
		  regCatCount = modOrRegularString.count("::\"")
		  count = 0
		  while(count < regCatCount):
		    regCatIndex = find_nth(modOrRegularString, "q.", count+1)
		    if(count <= regCatCount-2):
			  regCatString = modOrRegularString[regCatIndex:]
			  regCatString = regCatString[:regCatString.find("\",")+1]
			  regularCategoryArray.append(regCatString)
			  convertedRegularCategoryArray.append(regCatString)
		    elif(count == regCatCount -1):
			  regCatString = modOrRegularString[regCatIndex:]
			  regCatString = regCatString[:regCatString.find("\"}")+2]
			  regularCategoryArray.append(regCatString)
			  convertedRegularCategoryArray.append(regCatString)
		    count = count + 1
		
		  modLength = len(modStringForSkipping)
		  linePosition = linePosition + modLength #So we don't repeat above for all ::" sequences in the mod statement
	  linePosition += 1  
	
	"""
	Insert stuff, not including inserts in mods
	"""

	#Look for INSERT
	#need to mark mod inserts as so because we need to put those in single quotes, not double like the rest
	linePosition = 0
	lineLength = len(line) #need to redo because we just got a line back from removeInsertWS
	while (linePosition < lineLength):
	  if (linePosition + 2 < lineLength):
	    firstChar = line[linePosition]
	    secondChar = line[linePosition+1]
	    thirdChar = line[linePosition+2]
	    checkInsertSequence = firstChar + secondChar + thirdChar
	    if(checkInsertSequence == '[IN'): #Once we find an insert 	 
		  placeholderString = line[linePosition:] #placeholder string holds the start of an index to the end of the array
		  startOfInsertString = placeholderString[:placeholderString.index('}')+1]#The entire insert
		  textAfterInsert = placeholderString[len(startOfInsertString):]
		  if(textAfterInsert[:2] == "[M"):
			insertArray.append(startOfInsertString)
		  else:
			insertArray.append(startOfInsertString)
	  linePosition += 1
	
	line = removeInsertWS(line)#Get rid of white-space immediately after insert statements to prepare line for insert conversion

	#Look for INSERT
	#need to mark mod inserts as so because we need to put those in single quotes, not double like the rest
	linePosition = 0
	lineLength = len(line) #need to redo because we just got a line back from removeInsertWS
	while (linePosition < lineLength):
	  if (linePosition + 2 < lineLength):
	    firstChar = line[linePosition]
	    secondChar = line[linePosition+1]
	    thirdChar = line[linePosition+2]
	    checkInsertSequence = firstChar + secondChar + thirdChar
	    if(checkInsertSequence == '[IN'): #Once we find an insert 	 
		  placeholderString = line[linePosition:] #placeholder string holds the start of an index to the end of the array
		  startOfInsertString = placeholderString[:placeholderString.index('}')+1]#The entire insert
		  textAfterInsert = placeholderString[len(startOfInsertString):]
		  if(textAfterInsert[:2] == "[M"):
			startOfInsertString = "StartIns" + startOfInsertString
			convertedInsertArray.append(startOfInsertString)
		  else:
			startOfInsertString = "Reg" + startOfInsertString
			convertedInsertArray.append(startOfInsertString)
	  linePosition += 1
	
	
	#Loop through regularCategoryArray, look for matches in fullStatement(the line), delete it, and replace each match with the corresponding counter in convertedRegularCategoryArray
	convertedRegularCategoryArray = convertRegCatToXML(convertedRegularCategoryArray)
	fullStatement = replaceArrayWithXML(fullStatement, regularCategoryArray, convertedRegularCategoryArray)

	#convert insert statements in convertedInsertArray into XML, then replace it in the array
	convertedInsertArray = convertInsertArrayToXML(convertedInsertArray)
	fullStatement = replaceArrayWithXML(fullStatement, insertArray, convertedInsertArray)
	
	fullStatement = cleanupFinalStatement(fullStatement) #currently just replaces [MOD]
	#need stuff here that takes each mod segment and adds }} to the end of it.

	return fullStatement
  
  
  """deleteCDATAContructs(String fullStatement)"""
  def deleteCDATAContructs(fullStatement):
    #delete '<![CDATA[ ' and ' ]]>' 
	CDATAList = list(fullStatement)
	startCDATA = '<![CDATA[ '
	startCDATALength = 10
	endCDATA = ' ]]>'
	endCDATALength = 4
	counter = 0
	
	while(counter < len(CDATAList)-11):
	  startCDATACheck = ''.join(CDATAList[counter:counter+startCDATALength])
	  if(startCDATACheck == '<![CDATA[ '): # if beginning is found, remove it from the list
	    currPos1 = startCDATALength
	    while(currPos1 > 0):
		  CDATAList.pop(counter)
		  currPos1 = currPos1 - 1  
	  
	  counter += 1
    
	counter = 0
	while(counter < len(CDATAList)-5):
	  endCDATACheck = ''.join(CDATAList[counter:counter+endCDATALength])
	  if(endCDATACheck == '</p>'):
	    currPos2 = endCDATALength 
	    while(currPos2 > 0):
		  CDATAList.pop(counter+4)
		  currPos2 = currPos2 - 1
	  counter = counter + 1    
	fullStatement = ''.join(CDATAList)
	return fullStatement  
	
  """receives a string and populates the elements module lists"""
  lines = plain_text.split('\n') #creates an array with each box containing one line of the plain text
  current_question = None
  current_response = None
  current_option = None
  current_option_letter = None
  current_group = None
  groups_tree = []
  current_page = None
  line_index = 0
  bnf_id = 1
  comment_id = 1
  #debug info
  line_dbg = 0
  for line in lines: #goes through the array of lines
	#debug info
    line_dbg += 1 #adds line to the counter (for use in the print console)
    print 'parsing line {0}'.format(line_dbg) #prints the line currently parsing to the console
    # end debug info
    group_match = re.search('^\[GROUP\]\{(\d+)\}: *(.*)', line) #does a regex search for each type of element
    page_match = re.search('^\[PAGE\]: *(.*)', line)
    additional_comments = re.search("^COMMENT: *(.*)", line)
    question_match = re.search('^ID: *((\d+\.)*\d+)', line)
    question_title = re.search('^TITLE: *(.*)', line)
    CDATA_match = re.search('<!\[CDATA\[.*?\]\]>', line) #check for CDATA
    if(CDATA_match):CDATA_match_position = CDATA_match.start() #gets the index CDATA start
    if(CDATA_match):CDATA_match_position_end = 	CDATA_match.end() #gets index of CDATA end
    text_tag = re.search('^TEXT: *(.*)', line)
    response_text_tag = re.search('^RESPONSE_TEXT: *(.*)', line)
    note_tag = re.search('^NOTE: *(.*)', line)
    CDATA_note_tag = re.search('^NOTE: <!\[CDATA\[.*?\]\]>', line)
    instructions_tag = re.search('^INSTRUCTIONS: *(.*)', line)
    response_note_tag = re.search('^RESPONSE_NOTE: *(.*)', line)
    validation_tag = re.search('^VALIDATION: *(?:\{([^}]*)\})?', line)
    response_validation_tag = re.search('^RESPONSE_VALIDATION: *(?:\{([^}]*)\})?', line)
    question_indent = re.search('INDENT: *(.*)', line)
    question_when = re.search('^DISPLAY_WHEN: *(.*)', line)
    question_where = re.search('^DISPLAY_WHERE: *(.*)', line)
    radio_option = re.search('^ *\(\) *(.*)', line)
    select_box_option = re.search('^ *\[\] *(.*)', line)
    option_clone = re.search('^CLONE: *(.*)', line)
    #validations are not included in this regex	
    textbox_response = re.search('^\[TEXTBOX\]$', line)
    memo_response = re.search('^\[MEMO\]$', line)
    cloze_response = re.search('.*(\[MEMO\]|\[TEXTBOX\]|\[NUMERICAL\]|\[\|(.*\|)+\]|\[:(.*:)+\]).*', line)
    insert_response = re.search('.*(\[INSERT\]).*', line)
    bnf_mapping = re.search('^BNF(?: ?\{(.*)\})?: *(.*)', line)
    response_bnf_mapping = re.search('^RESPONSE_BNF(?: ?\{(.*)\})?: *(.*)', line)
    blank_line = re.search('^ *$', line)
    mod = re.search('MOD', line)
    comment_not_to_parse = re.search('^ *#.*', line)

    if(comment_not_to_parse):
      pass
    
    elif(insert_response and mod): 
	  if(note_tag):
	    fullStatement = convertToXML(line, mod)
	    fullStatement = fullStatement[5:]
	    if(CDATA_match):
		  fullStatement = deleteCDATAContructs(fullStatement)
	    if(current_option):
		  current_option.note_elements.append(elements.Note(fullStatement,TYPE_ATTR_JSON))
	    elif(current_response):
		  current_response.note_elements.append(elements.Note(fullStatement,TYPE_ATTR_JSON))
	    else:
		  current_question.note_elements.append(elements.Note(fullStatement,TYPE_ATTR_JSON))
	  
	  elif(text_tag):
	    fullStatement = convertToXML(line, mod)
	    fullStatement = fullStatement[5:]
	    if(CDATA_match):
		  fullStatement = deleteCDATAContructs(fullStatement)
	    else:
		  if(current_question):
		    current_question.text_elements.append(elements.Text(replace_with_json(fullStatement)))
		  elif(current_page):
		    current_page.text_elements.append(elements.Text(replace_with_json(fullStatement)))
		  else:
		    current_group.text_elements.append(elements.Text(replace_with_json(fullStatement)))
	  
	  elif(instructions_tag):
		fullStatement = convertToXML(line, mod)
		fullStatement = fullStatement[13:]
		if(CDATA_match):
		  fullStatement = deleteCDATAContructs(fullStatement)
		if(current_question):
		  set_instructions(current_question, fullStatement, insert_response)
		elif(current_page):
		  set_instructions(current_page, fullStatement, insert_response)	
		elif(current_group):
		  set_instructions(current_group, fullStatement, insert_response)
	  
	  elif(response_bnf_mapping):
	    fullStatement = convertToXML(line, mod)
	    fullStatement = fullStatement[14:]
	    if(CDATA_match):
		  fullStatement = deleteCDATAContructs(fullStatement)
	    bnf_mapping_object = elements.BnfMapping('b.' + str(bnf_id),fullStatement)
	    if(insert_response):
	      bnf_mapping_object.type_attr = TYPE_ATTR_JSON
	      is_response=True
	    if(current_option and (not is_response)):
	      current_option.bnf_mapping_elements.append(bnf_mapping_object)
	    elif(current_response):
	      current_response.bnf_mapping_elements.append(bnf_mapping_object)
	    bnf_id += 1
		
    elif(group_match):
      current_page = None
      current_question = None
      current_response = None
      current_option = None
      current_option_letter = None
      current_group = elements.Group(group_match.group(1), group_match.group(2))
      groups_tree.insert(current_group.level_attr-1, current_group)
      while(len(groups_tree) > current_group.level_attr):
        groups_tree.pop()

      if(current_group.level_attr != 1):
        groups_tree[current_group.level_attr-2].group_elements.append(current_group)

    elif(page_match):
      current_question = None
      current_response = None
      current_option = None
      current_option_letter = None
      current_page = elements.Page(page_match.group(1))
      current_group.page_elements.append(current_page)
	
    elif(additional_comments):
      current_question = elements.Comment('.'.join(['c', str(comment_id)]))
      current_question.text_elements.append(elements.Text(additional_comments.group(1)))
      if(current_page):
        current_page.comment_ref_attr = current_question.id_attr
      else:
        current_group.comment_ref_attr = current_question.id_attr

      comment_id += 1
    
    elif(question_match):
      current_response = None
      current_option = None
      current_option_letter = None
      question_id = QUESTION_ID_PREFIX
      question_id += question_match.group(1)
      question = elements.Question(question_id)
      current_question = question
      if(current_page): #TODO: there must be a current_page here
        current_page.include_elements.append(elements.Include(question.id_attr))

    elif(question_title):
      if(CDATA_match):
	    question_title_CDATA = deleteCDATAContructs(line[7:])
	    current_question.title_element = question_title_CDATA
      if(question_title.group(1)):
        current_question.title_element = question_title.group(1)
    
    elif(question_indent):
        current_question.indent_attr = question_indent.group(1)
		
    elif(text_tag):
	  if(CDATA_match):
	    text_tag = deleteCDATAContructs(line[6:])
	    if(current_question):
		  current_question.text_elements.append(elements.Text(replace_with_json(text_tag)))
	    elif(current_page):
		  current_page.text_elements.append(elements.Text(replace_with_json(text_tag)))
	    else:
		  current_group.text_elements.append(elements.Text(replace_with_json(text_tag)))
	  elif(current_question):
	    set_text(text_tag, current_question, insert_response)
	  elif(current_page):
	    set_text(text_tag, current_page, insert_response)
	  else:
	    set_text(text_tag, current_group, insert_response)

    elif(response_text_tag):
      if(response_text_tag.group(1)):
        text_content = replace_with_json(response_text_tag.group(1))
        #TODO: set type to json?
        if(current_response):
          current_response.text_elements = [elements.Text(text_content)]
 
    elif(note_tag):
      if(CDATA_match): 
        if(note_tag.group(1)):
          note_content = deleteCDATAContructs(line[6:])
          if(current_option):
		    current_option.note_element = elements.Note(note_content)
		    if(insert_response):
		      current_option.note_element.type_attr = TYPE_ATTR_JSON
          elif(current_response):
		    current_response.note_elements = [elements.Note(note_content)]
		    if(insert_response):
		      current_response.note_elements[-1].type_attr = TYPE_ATTR_JSON
          else:
		    current_question.note_elements = [elements.Note(note_content)]
		    if(insert_response):
		      current_question.note_elements[-1].type_attr = TYPE_ATTR_JSON

      elif(note_tag.group(1)):
		note_content = replace_with_json(note_tag.group(1))
		if(current_option):
		  current_option.note_element = elements.Note(note_content)
		  if(insert_response):
		    current_option.note_element.type_attr = TYPE_ATTR_JSON

		elif(current_response):
		  current_response.note_elements = [elements.Note(note_content)]
		  if(insert_response):
		    current_response.note_elements[-1].type_attr = TYPE_ATTR_JSON

		else:
		  current_question.note_elements = [elements.Note(note_content)]
		  if(insert_response):
		    current_question.note_elements[-1].type_attr = TYPE_ATTR_JSON

    elif(response_note_tag):
      if(response_note_tag.group(1) and current_response):
	    response_note_content = replace_with_json(response_note_tag.group(1))
	    current_response.note_elements = [elements.Note(response_note_content)]
	    if(insert_response):
		  current_response.note_elements[-1].type_attr = TYPE_ATTR_JSON
    
    elif(question_when):
      if(question_when.group(1)):
        csv_when_attr = re.sub(' or ', ',q.', question_when.group(1)) 
        current_question.display_when_attr = QUESTION_ID_PREFIX + csv_when_attr

    elif(question_where):
      if(question_where.group(1)):
        csv_where_attr = re.sub(' or ', ',q.', question_where.group(1)) 
        current_question.display_where_attr = QUESTION_ID_PREFIX + question_where.group(1)

    elif(validation_tag):
      validation = {}
      if(validation_tag.group(1)):
        validation_pairs = validation_tag.group(1).split(";;") #Delimeters are ; and : enclosed in double quotes. Normal ; + : should display correctly
        for validation_pair in validation_pairs:
          validation_pair = validation_pair.split("::")
		  #TODO: should I really remove these spaces?
          validation[re.sub('^( )+|( )+$', '', validation_pair[0])] = re.sub('^( )+|( )+$', '', validation_pair[1])
          
      if current_option:
        current_option.validation_element = elements.Validation(None, validation)

      elif current_response:
        current_response.validation_elements.append(elements.Validation(None, validation))

    elif(response_validation_tag and current_response):
      validation = {}
      if(response_validation_tag.group(1)):
        validation_pairs = response_validation_tag.group(1).split(';;')
        for validation_pair in validation_pairs:
          validation_pair = validation_pair.split('::')
          #TODO: should I really remove these spaces?
          validation[re.sub('^( )+|( )+$', '', validation_pair[0])] = re.sub('^( )+|( )+$', '', validation_pair[1])

      current_response.validation_elements.append(elements.Validation(None, validation))

    elif(blank_line):
      current_question = None
      current_response = None
      current_option = None

    elif(radio_option): #test with CDATA
      if(not current_response):
        current_response = elements.Response('select one')
        current_option_letter = 'A'
        current_question.response_elements.append(current_response)
	  
      if(CDATA_match):
        radioString = deleteCDATAContructs(line)
        option_id = current_question.id_attr + '.' + current_option_letter
        option_text = elements.Text(replace_with_json(radioString, option_id))
      else:	  
        option_id = current_question.id_attr + '.' + current_option_letter
        option_text = elements.Text(replace_with_json(radio_option.group(1), option_id))
	  
      if(cloze_response):
		option_text.type_attr = TYPE_ATTR_JSON
      if(insert_response):
	    option_text.type_attr = TYPE_ATTR_JSON
	  
      option = elements.Option(option_id, None, option_text)
      current_option_letter = chr(ord(current_option_letter) + 1)
      current_response.option_elements.append(option)
      current_option = option

    elif(select_box_option):
      if(not current_response):
        current_response = elements.Response('select multi')
        current_option_letter = 'A'
        current_question.response_elements.append(current_response)
      
      if(CDATA_match):
        switchString = deleteCDATAContructs(line)
        option_id = current_question.id_attr + '.' + current_option_letter
        option_text = elements.Text(replace_with_json(switchString, option_id))
      else:
	    option_id = current_question.id_attr + '.' + current_option_letter
	    option_text = elements.Text(replace_with_json(select_box_option.group(1), option_id))
      if(cloze_response):
        option_text.type_attr = TYPE_ATTR_JSON
      if(insert_response):
        option_text.type_attr = TYPE_ATTR_JSON
		
      option = elements.Option(option_id, None, option_text)
      current_option_letter = chr(ord(current_option_letter) + 1)
      current_response.option_elements.append(option)
      current_option = option
	  
    elif(option_clone and current_option):
	  test = re.sub(" ","",option_clone.group(1)) #addresses a bug that occurred when spaces were in clone statement lines.
	  #raise Exception(test)
	  current_option.clone_attr = test

    elif(textbox_response):
      current_response = elements.Response('textbox')
      current_question.response_elements.append(current_response)

    elif(memo_response):
      current_response = elements.Response('memo')
      current_question.response_elements.append(current_response)

    elif(cloze_response):
      #close_response.group(0) = original text
	  #response_text = outputted text
	  #id_attr = 1.5
	  #TYPE_ATTR_JSON = json
      response_text = elements.Text(replace_with_json(cloze_response.group(0), current_question.id_attr), TYPE_ATTR_JSON)
      current_response = elements.Response('cloze', [response_text])
      current_question.response_elements.append(current_response)

    #elif(insert_response):
    elif(bnf_mapping):
      set_bnf(bnf_mapping, insert_response, bnf_id, current_option, current_response)
      bnf_id += 1
    
    elif(response_bnf_mapping):
      set_bnf(response_bnf_mapping, insert_response, bnf_id, current_option, current_response,True)
      bnf_id += 1
	
    elif(instructions_tag):
      if(CDATA_match):
		completeString = deleteCDATAContructs(line[13:])
		if(current_question):
			set_instructions(current_question, completeString, insert_response)		
		elif(current_page):
			set_instructions(current_page, completeString, insert_response)	
		elif(current_group):
			set_instructions(current_group, completeString, insert_response)
	  
      elif(current_question):
        set_instructions(current_question, line[line.index(':')+1:], insert_response)

      elif(current_page):
        set_instructions(current_page, line[line.index(':')+1:], insert_response)

      elif(current_group):
        set_instructions(current_group, line[line.index(':')+1:], insert_response)
		
		
def set_instructions(current_object, line, insert_response):
  #TODO: raise type error
  #TODO: crete module for all regexes
  current_object.instructions_elements.append(elements.Instructions(replace_with_json(line)))
  if(insert_response):
    current_object.instructions_elements[-1].type_attr = TYPE_ATTR_JSON

def set_bnf(bnf_mapping, insert_response, bnf_id, current_option, current_response, is_response=False):
  bnf_mapping_object = elements.BnfMapping('b.' + str(bnf_id), replace_with_json(bnf_mapping.group(2)))
  if(bnf_mapping.group(1)):
    raw_bnf_when_attr = re.sub(' ', '', bnf_mapping.group(1))
    bnf_when_attr_list = []
    raw_bnf_when_attr_list = raw_bnf_when_attr.split(',')
    for bnf_when_value in raw_bnf_when_attr_list:
      bnf_when_attr_list.append(QUESTION_ID_PREFIX + bnf_when_value)

    bnf_mapping_object.when_attr = ','.join(bnf_when_attr_list)

  if(insert_response):
    bnf_mapping_object.type_attr = TYPE_ATTR_JSON

  if(current_option and (not is_response)):
    current_option.bnf_mapping_elements.append(bnf_mapping_object)

  elif(current_response):
    current_response.bnf_mapping_elements.append(bnf_mapping_object)

def set_text(text_tag, current_object, insert_response):
  if(text_tag.group(1)):
    text_content = replace_with_json(text_tag.group(1))
    current_object.text_elements = [elements.Text(text_content)]
    if(insert_response):
      current_object.text_elements[-1].type_attr = TYPE_ATTR_JSON

