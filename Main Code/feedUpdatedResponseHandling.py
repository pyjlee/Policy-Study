"""Module to create objects for the elements Classes based in a specific plain
text format. More information in utils/docx_format.txt"""

import re
import json
from papofeed import elements, extractor

QUESTION_ID_PREFIX = 'q.'
TYPE_ATTR_JSON = 'json'
PLAIN_TEXT_TAGS_REGEX = '((\[MEMO\]|\[TEXTBOX\]|\[NUMERICAL\]|\[\|(.*\|)+\]|\[:(.*:)+\]|\[INSERT\])(?:\{([^}]*)\})?)'

	
def replace_with_json(line, id_attr=''):
  """For each line of the plain text string, replaces the SPECIAL FIELDS with
  JSON code described in utils/questionnaire_tag_description.docx"""

  embedded_json_letter = 'a'
  match = re.search(PLAIN_TEXT_TAGS_REGEX, line)
  def json_validation():
    #TODO: We need to extract 'default' from here and up to cloze
    validation = {}
    if(match.group(5)):
      validation_pairs = match.group(5).split(';')
      for validation_pair in validation_pairs:
        validation_pair = validation_pair.split(':')
        #TODO: should I really remove these spaces?
        validation[re.sub('^( )+|( )+$', '', validation_pair[0])] = re.sub('^( )+|( )+$', '', validation_pair[1])
    return validation

  while(match):
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
      validation = json_validation()
      if(validation):
        for key in validation.iterkeys():
          if(key in insert_attributes):
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
  
  """convertRegCatToXML
  Input: Array of stripped raw categories
  Output: Array of regular categories with the values in the input array held in double quotes
  Functionality: Converts each item in the input array into a list, inserts double quotes at the end and beginning of the qref value,
  turns it back into a string, and adds it to an array of converted regular category that it then returns.
  """
  def convertRegCatToXML(convertedRegularCategoryArray):
	counter = 0
	while(counter < len(convertedRegularCategoryArray)):
	  rawText = list(convertedRegularCategoryArray[counter])
	  rawText.insert(0,'"')
	  rawText.insert(rawText.index(':'), '"')
	  convertedCategoryText = ''.join(rawText)
	  convertedRegularCategoryArray[counter] = convertedCategoryText
	  counter += 1
	return convertedRegularCategoryArray
  
  """convertModArrayToXML
  Input: Array of instances of mods
  Output: Array of mods that have correct XML formatting, including missing quotes and "mod": {" at the beginning of the mod string
  Functionality: Converts each item in the input array into a list, adds a douvle quote to the end of the qref itenm 
  """   
  def convertModArrayToXML(convertedModArray):
    counter = 0
    #raise Exception(convertedModArray)
    while (counter < len(convertedModArray)):
	  rawTextList = list(convertedModArray[counter])
	  tempIndex = ''.join(rawTextList).rfind('"')
	  rawTextList.pop(tempIndex)
	  #raise Exception(''.join(rawTextList))
	  secondQuoteIndex = rawTextList.index(':')
	  rawTextList.insert(secondQuoteIndex, '"') #add the second quote to missing from the qref @ secondQuoteIndex
	  newRawText= ''.join(rawTextList)
	  convertedString = '"mod": {"' + str(newRawText)
	  convertedModArray[counter] = convertedString
	  counter += 1
    
    return convertedModArray
  
  def convertInsertArrayToXML(convertedInsertArray):
	#must check if the word endModType is present at the end of the string. If so, then the quotes are singles and add a " after the ending }}
    #if begModType is at the end, no ending }}
	#remove begModType and endModType Text, add quotes
	#raise Exception(convertedInsertArray)
	counter = 0
	while (counter < len(convertedInsertArray)):
	  rawText = convertedInsertArray[counter]
	  if(rawText.startswith('begModType')): #if beginning to a mod, remove beginning desc, no ending brackets
		tempArray = list(convertedInsertArray[counter])
		firstQuoteIndex = tempArray.index(' ') + 1
		tempArray.insert(firstQuoteIndex, '"')
		tempArray.append('"')
		tempArrayBegRemoved = tempArray[10:]
		tempArrayBegRemoved.insert(0,'"')
		qrefEndIndex = tempArrayBegRemoved.index(':')
		tempArrayBegRemoved.insert(qrefEndIndex,'"')
		newRawText = ''.join(tempArrayBegRemoved)
		convertedInsertArray[counter] = newRawText
		convertedString = '{"insert": {' + convertedInsertArray[counter] + ', '
		convertedInsertArray[counter] = convertedString
	  elif(rawText.endswith('endModType')): #if ending to a mod, replace double quotes with singles, add " to end + remove ending desc. 
		tempArray = list(convertedInsertArray[counter])
		firstQuoteIndex = tempArray.index(' ') + 1
		tempArray.insert(firstQuoteIndex, '\'')
		tempArrayEndRemoved = tempArray[:-10]
		tempArrayEndRemoved.append('\'')
		tempArrayEndRemoved.insert(0,'"')
		qrefEndIndex = tempArrayEndRemoved.index(':')
		tempArrayEndRemoved.insert(qrefEndIndex,'\'')
		tempArrayEndRemoved.pop(0)
		tempArrayEndRemoved.insert(0, '\'')
		newRawText = ''.join(tempArrayEndRemoved)
		convertedInsertArray[counter] = newRawText
		convertedString = '{\'insert\':{' + convertedInsertArray[counter] + '}}"'
		convertedInsertArray[counter] = convertedString
	  else: #just add the double quotes
	    tempArray = list(convertedInsertArray[counter])
	    firstQuoteIndex = tempArray.index(' ') + 1
	    tempArray.insert(firstQuoteIndex, '"')
	    tempArray.append('"')
	    tempArray.insert(0,'"')
	    qrefEndIndex = tempArray.index(':')
	    tempArray.insert(qrefEndIndex,'"')
	    newRawText = ''.join(tempArray)
	    convertedInsertArray[counter] = newRawText
	    convertedString = '{"insert": {' + convertedInsertArray[counter] + '}}'
	    convertedInsertArray[counter] = convertedString
	  counter += 1
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
  
  def cleanupModStatement(fullStatement):
  
  
    return fullStatement
  
  """cleanupFinalStatement(String fullStatement)
  Input: the converted line with a few errors still remaining
  Output: the final string, ready for writing
  Functionality: 1. Gets rid of [ prefacing "mod", 2. Adds { to ending mod inserts. 3. Adds the q. to the first mod insert. 4. Adds the 2 ending brackets to the mod """
  def cleanupFinalStatement(fullStatement): #Gets rid of [ in mods and adds a ' {' to ending mod inserts.
	fullStatement = list(fullStatement)
	insertSequence1 = ':\'in'
	startMod1 = '["mo'
	counter = 0
	countInsertQref = 0
	while(counter < len(fullStatement)-9): #check for insertSequence1 and startMod1
	  currentPart = fullStatement[counter] + fullStatement[counter+1] + fullStatement[counter+2] + fullStatement[counter+3]
	  firstInsertQrefCheck = ''.join(fullStatement[counter:counter+8]) #checks for qref": ", creates a string out of the list returned by fullStatement[counter:counter+8]
	  if(currentPart == insertSequence1):
	    fullStatement.insert(counter+1, ' {') #1
	  elif(currentPart == startMod1):
	    fullStatement.pop(counter) #2
	  if(firstInsertQrefCheck == 'qref": "'):#look for qref": ", if there is no q after the ", then add the q.
	    if(fullStatement[counter+8] != 'q' ):
		  fullStatement.insert(counter+8, 'q.') #3
	  counter += 1
	fullStatement = ''.join(fullStatement)
	
	#add 2 ending brackets to a mod - find the index of a mod, then the index of the 3rd ending bracket.
	#find index of mod - make string from mod start to end.
	counter = 0
	modString = '"mod"'
	while(counter < len(fullStatement)-5):
	  modCheckString = fullStatement[counter:counter+5]
	  if(modCheckString == modString):
	    modIndex = counter
	    tempString = fullStatement[modIndex:]
	    endModIndex = find_nth(tempString, '}', 3)#now we have the index of the smaller string
	    #go back to the original string, insert at counter+endModIndex
	    fullStatementList = list(fullStatement)
	    fullStatementList.insert(counter+endModIndex, '}}')
	    fullStatement = ''.join(fullStatementList)
	  counter += 1

	return fullStatement

  """convertToXML(string line, boolean mod)"""
  def convertToXML(line, mod):
	
	fullStatement = line
	lineLength = len(line)

	insertArray = []
	convertedInsertArray = []
	modArray = []
	convertedModArray = []
	regularCategoryArray = []
	convertedRegularCategoryArray = []
	
	linePosition = 0
	viewCatNum = 12

	#Look for MOD or REGULAR CATEGORY. Both are :", but Mod has a '{' a few characters before it. 
	while (linePosition < lineLength):
	  if (linePosition + 2 < lineLength):
	    colonChar = line[linePosition]
	    spaceChar = line[linePosition+1]
	    dQuoteChar = line[linePosition+2] #these hold two characters as the loop goes through the string
	    checkModSequence = colonChar + spaceChar + dQuoteChar
	    if(checkModSequence == ': "'):
		  tempSubString = line[:linePosition]
		  lastQIndex = tempSubString.rfind('q.')
		  modOrRegularString = line[lastQIndex-1:linePosition]
		  if '{' in modOrRegularString:#If { is found (means it is a mod)
			placeholderString = line[lastQIndex-6:] #-6 is to include the [MOD] portion of the string
			startOfModString = placeholderString[:find_nth(placeholderString,'[',2)+1] #MOD]{q.4.10.4.D: "Special Characters": [
			modContentsString = startOfModString[startOfModString.index('q'):find_nth(startOfModString,'[',2)+1] #q.4.10.4.D: "Special Characters": [
			modArray.append(startOfModString)
			convertedModArray.append(modContentsString)
		  else:
			startOfCategoryString = line[linePosition-viewCatNum:]
			lastQIndex = startOfCategoryString.find('q.')
			secondQuoteIndex = find_nth(startOfCategoryString, '"', 2)
			realCategoryString = startOfCategoryString[lastQIndex:secondQuoteIndex+1]
			regularCategoryArray.append(realCategoryString)
			convertedRegularCategoryArray.append(realCategoryString)
	  linePosition += 1  
	#Look for INSERT
	#need to mark mod inserts as so because we need to put those in single quotes, not double like the rest
	linePosition = 0
	while (linePosition < lineLength):
	  if (linePosition + 2 < lineLength):
		firstChar = line[linePosition]
		secondChar = line[linePosition+1]
		thirdChar = line[linePosition+2]
		checkInsertSequence = firstChar + secondChar + thirdChar
		if(checkInsertSequence == '[IN'): #Once we find an insert 	  
		  placeholderString = line[linePosition:] #placeholder string holds the start of an index to the end of the array
		  startOfInsertString = placeholderString[:placeholderString.index('}')+1]#beginning of index to the end of the index
		  realInsertString = ''
		  #scan the rest of the string. If there is another } before another {, then it is ending part of a mod ( {example} )
		  #check for the presence of both. Must find both, and index of } must be smaller than index of {, or just }
		  modTestString = placeholderString[placeholderString.index('}')+1:] #the string after startOfInsertString
		  if('}' in modTestString and '{' in modTestString): #check if there are both
		    #check if its the first part of a mod statement (Goes insert->mod->insert)
		    #to check, see if [MOD] is right after the end of the insert
		    #get placeholder string, find index of }, then look to see if [MOD] is right afterwards
			startModCheckIndex = placeholderString.index('}')
			firstChar = placeholderString[startModCheckIndex+1]
			secondChar = placeholderString[startModCheckIndex+2]
			thirdChar = placeholderString[startModCheckIndex+3]
			startModCheckSequence = firstChar + secondChar + thirdChar
			if(startModCheckSequence == '[MO'):
			  realInsertString = 'begModType' + startOfInsertString[startOfInsertString.index('{')+1:startOfInsertString.index('}')]
			elif(modTestString.index('}') < modTestString.index('{')): #check if } comes before {
			  realInsertString = startOfInsertString[startOfInsertString.index('{')+1:startOfInsertString.index('}')] + 'endModType'
			else: #else, presence of { and } just indicate another separate insert
			  realInsertString = startOfInsertString[startOfInsertString.index('{')+1:startOfInsertString.index('}')]
		  elif('}' in modTestString and not '{' in modTestString): #if only }, then it must be the closing of the mod
			  realInsertString = startOfInsertString[startOfInsertString.index('{')+1:startOfInsertString.index('}')] + 'endModType'
		  else: #if none, then it's a normal insert as the last insert/mod statement in the line
		    realInsertString = startOfInsertString[startOfInsertString.index('{')+1:startOfInsertString.index('}')]
		  insertArray.append(startOfInsertString)
		  convertedInsertArray.append(realInsertString)
	  linePosition +=1


	#convert regular categories in convertedInsertArray into XML, then replace it in the array
	convertedRegularCategoryArray = convertRegCatToXML(convertedRegularCategoryArray)
	fullStatement = replaceArrayWithXML(fullStatement, regularCategoryArray, convertedRegularCategoryArray)

    #convert mod statements in convertedModArray into XML, then replace it in the array	
	convertedModArray = convertModArrayToXML(convertedModArray)
	fullStatement = replaceArrayWithXML(fullStatement, modArray, convertedModArray)

	#convert insert statements in convertedInsertArray into XML, then replace it in the array
	convertedInsertArray = convertInsertArrayToXML(convertedInsertArray)
	fullStatement = replaceArrayWithXML(fullStatement, insertArray, convertedInsertArray)

	#Loop through regularCategoryArray, look for matches in fullStatement(the line), delete it, and replace each match with the #corresponding counter # in convertedRegularCategoryArray
	counter = 0
	arrayPos = 0
	while(counter < len(fullStatement) and arrayPos < len(modArray)):#loop through the line
	  #turn originalString into a list
	  #delete the [ at the end, add a {
	  #turn it back into a string
	  originalString = modArray[arrayPos]
	  originalString = list(originalString)
	  originalString.pop()
	  originalString.append('{')
	  originalString = ''.join(originalString)
	  convertedString = convertedModArray[arrayPos]
	  if(originalString in fullStatement):#check to see if the reg category is in the original line.
	    fullStatement = fullStatement.replace(originalString, convertedString)
	    arrayPos += 1
	  counter += 1  
	
	fullStatement = cleanupFinalStatement(fullStatement)
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
    textbox_response = re.search('^\[TEXTBOX\]', line)
    memo_response = re.search('^\[MEMO\]', line)
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
        validation_pairs = validation_tag.group(1).split('";"') #Delimiters are ; and : enclosed in double quotes. Normal ; + : should display correctly
        for validation_pair in validation_pairs:
          validation_pair = validation_pair.split('":"')
		  #TODO: should I really remove these spaces?
          validation[re.sub('^( )+|( )+$', '', validation_pair[0])] = re.sub('^( )+|( )+$', '', validation_pair[1])

      if current_option:
        current_option.validation_element = elements.Validation(None, validation)

      elif current_response:
        current_response.validation_elements.append(elements.Validation(None, validation))

    elif(response_validation_tag and current_response):
      validation = {}
      if(response_validation_tag.group(1)):
        validation_pairs = response_validation_tag.group(1).split('";"')
        for validation_pair in validation_pairs:
          validation_pair = validation_pair.split('":"')
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

      option = elements.Option(option_id, None, option_text)
      current_option_letter = chr(ord(current_option_letter) + 1)
      current_response.option_elements.append(option)
      current_option = option

    elif(option_clone and current_option):
      current_option.clone_attr = option_clone.group(1)

    elif(memo_response):
      handle_response("MEMO", current_question,line)
	  
    elif(textbox_response):
      handle_response("TEXTBOX", current_question,line)      

    elif(cloze_response):
	  #Look for [MEMO] or [TEXTBOX]
	  memoMatch = re.search("MEMO", line)
	  textBoxMatch = re.search("[TEXTBOX]", line)
	  
	  if(memoMatch):
	    #find where the memo is + go from the first instance of the { to the first instance of the }
		memoStringStart = line[memoMatch.start()-1:]
		memoStringComplete = memoStringStart[:memoStringStart.find('}')+1]
		handle_response("MEMO", current_question,memoStringComplete)

		#do regular memo stuff
		#delete memo string from original string
		
	  #if(textBoxMatch):
	    #raise Exception("textBox Found")
	  
	  #raise Exception('HEY')
	  response_text = elements.Text(replace_with_json(cloze_response.group(0), current_question.id_attr), TYPE_ATTR_JSON)
	  current_response = elements.Response('cloze', [response_text])
	  current_question.response_elements.append(current_response)
	  
	  
	  
    #elif(insert_response): """###############################################"""
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
		
def handle_response(response_type, current_question, line):
  
  if(response_type == "MEMO"):
    current_response = elements.Response('memo')
    memoContents = re.search("[MEMO]", line)
    memoStart = memoContents.start() + 7
    memoEnd = line.rfind('}')
    memoContents = line[memoStart:memoEnd]
    memo = {}
    memo_pairs = memoContents.split('";"') #memo pairs is a list, with items separated by ;
    for memo_pair in memo_pairs:
	  memo_pair = memo_pair.split('":"')
	  memo[re.sub('^( )+|( )+$', '', memo_pair[0])] = re.sub('^( )+|( )+$', '',memo_pair[1])
    current_question.response_elements.append(current_response)
    current_response.memo_elements.append(elements.Memo(None, memo))
  
  if(response_type == "TEXTBOX"):
    current_response = elements.Response('textbox')
    textBoxContents = re.search("[TEXTBOX]", line)
    textBoxStart = textBoxContents.start() + 10
    textBoxEnd = line.rfind('}')
    textBoxContents = line[textBoxStart:textBoxEnd]
    textBox = {}
    textBox_pairs = textBoxContents.split('";"')
    for textBox_pair in textBox_pairs:
	  textBox_pair = textBox_pair.split('":"')
	  textBox[re.sub('^( )+|( )+$', '', textBox_pair[0])] = re.sub('^( )+|( )+$', '', textBox_pair[1])
    current_question.response_elements.append(current_response)
    current_response.textBox_elements.append(elements.textBox(None, textBox))  

		
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

