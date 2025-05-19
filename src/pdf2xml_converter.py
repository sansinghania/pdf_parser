import xml.etree.ElementTree as ET
from xml.dom import minidom
import string
from pdfconverter import convert_pdf
from pdf2xml_util import post_process_xml

def pdf2xml(pdfFilename):
    word_delimiter = [' ', '']

    #step01: generating xml file using pdfminer utility
    text = convert_pdf(pdfFilename, 'xml')

    #replace some hidden unicode chars with equivalent chars
    text = text.replace(u'\u00AD', '-')


    root = ET.fromstring(text)

    #step02: build words and parts of textline by joning characters
    wc = 0
    for child in root.iter('textline'):
        word, font, size, bbox = '', '', '', ''

        textlist = child.findall('text')
        for text in textlist:
            #if text.text in word_delimiter:
            if (text.text in string.whitespace) or (text.text in u'\u00A0\u200B'):
                if word != '':
                    ele = ET.SubElement(child, 'word')
                    ele.text = word
                    ele.set('font',font)
                    ele.set('size',size)
                    ele.set('bbox',bbox)
                    wc += 1
                    ele.set('id', 'wc-'+str(wc))
                    word, font, size, bbox = '', '', '', ''
            elif 'font' in (text.attrib):   
                # if text.text not in string.printable:
                #     print ("non-printable text -" + repr(text.text) + '/' + text.text + "- end of text", text.text.encode(), ord(text.text))

                textfont, textsize, textbbox = text.attrib['font'], text.attrib['size'], text.attrib['bbox']
                if word == '':
                    font, size, bbox = textfont, textsize, textbbox
                    word = word + text.text
                else:
                #elif 9textfont == font and textsize == size): (NO NEED TO CHECK FOR FORMATTING WITH IN A WORD)
                    word = word + text.text
                    bbox = bbox.replace((bbox.split(','))[2],(textbbox.split(','))[2])

            child.remove(text)

        if word != '':
            ele = ET.SubElement(child, 'word')
            ele.text = word
            ele.set('font',font)
            ele.set('size',size)
            ele.set('bbox',bbox)
            wc += 1
            ele.set('id', 'wc-'+str(wc))


    #step03: remove unwanted nodes from the xml (layout, rect)
    pages = root.findall('page')
    print ("number of pages -" + str(len(pages)))
    for page in pages:
        nodelist = page.findall('layout')
        for node in nodelist:
            page.remove(node)
        nodelist = page.findall('rect')
        for node in nodelist:
            page.remove(node)

        #remove empty txtboxes and txtlines
        txtboxlist = page.findall('textbox')
        for txtbox in txtboxlist:
            wordlist = list(txtbox.iter('word'))
            if len(wordlist) == 0:
                #print ("empty txtbox -" + str(len(wordlist)))
                page.remove(txtbox)
            else:
                #print ("txtbox not empty -" + str(len(wordlist)))
                txtlinelist = list(txtbox.iter('textline'))
                for txtline in txtlinelist:
                    wordlist = list(txtline.iter('word'))
                    #print ("txtline -" + str(len(wordlist)))
                    if len(wordlist) == 0:
                        #print ("......empty txtline -" + str(len(wordlist)))
                        txtbox.remove(txtline)

        #remove all txtboxes and make txtlines as direct child of page
        txtlinelist = list(page.iter('textline'))
        txtboxlist = list(page.iter('textbox'))
        for txtbox in txtboxlist:
            page.remove(txtbox)
        for txtline in txtlinelist:
            page.append(txtline)

    #step04: redfine textline coordinates based on words
    txtlinelist = list(root.iter('textline'))
    tlc = 0
    for txtline in txtlinelist:
        txtline_coords = [-1.0, -1.0, -1.0, -1.0]
        tlc += 1
        wordlist = txtline.findall('word')
        for word in wordlist:
            word_coords = (word.attrib['bbox']).split(',')
            word_coords[0], word_coords[1], word_coords[2], word_coords[3] = float(word_coords[0]), float(word_coords[1]), float(word_coords[2]), float(word_coords[3])
            if txtline_coords[0] == -1.0 or txtline_coords[0] > word_coords[0]:
                txtline_coords[0] = word_coords[0]
            if txtline_coords[1] == -1.0 or txtline_coords[1] > word_coords[1]:
                txtline_coords[1] = word_coords[1]
            if txtline_coords[2] == -1.0 or txtline_coords[2] < word_coords[2]:
                txtline_coords[2] = word_coords[2]
            if txtline_coords[3] == -1.0 or txtline_coords[3] < word_coords[3]:
                txtline_coords[3] = word_coords[3]
        txtlinebbox  = str(txtline_coords[0]) + ',' + str(txtline_coords[1]) + ',' + str(txtline_coords[2]) + ',' + str(txtline_coords[3])
        txtline.set('bbox', txtlinebbox)
        #txtline.set('midaxis', str((txtline_coords[1]+txtline_coords[3])/2) + ',' + str((txtline_coords[0]+txtline_coords[2])/2))
        txtline.set('id', 'tlc-'+str(tlc))
        #print ("txtline x axis - ", ((txtline.attrib['midaxis']).split(','))[0])

    # do post Processing
    post_process_xml(root);

    #
    # TXTBOXES DID NOT ADD ANY VALUE TO UNDERSTAND THE PDF
    #
    """
    #step05: redfine textbox coordinates based on textlines
    txtboxlist = list(root.iter('textbox'))
    for txtbox in txtboxlist:
        txtbox_coords = [-1.0, -1.0, -1.0, -1.0]
        txtlinelist = txtbox.findall('textline')
        for txtline in txtlinelist:
            txtline_coords = (txtline.attrib['bbox']).split(',')
            txtline_coords[0], txtline_coords[1], txtline_coords[2], txtline_coords[3] = float(txtline_coords[0]), float(txtline_coords[1]), float(txtline_coords[2]), float(txtline_coords[3])
            if txtbox_coords[0] == -1.0 or txtbox_coords[0] > txtline_coords[0]:
                txtbox_coords[0] = txtline_coords[0]
            if txtbox_coords[1] == -1.0 or txtbox_coords[1] > txtline_coords[1]:
                txtbox_coords[1] = txtline_coords[1]
            if txtbox_coords[2] == -1.0 or txtbox_coords[2] < txtline_coords[2]:
                txtbox_coords[2] = txtline_coords[2]
            if txtbox_coords[3] == -1.0 or txtbox_coords[3] < txtline_coords[3]:
                txtbox_coords[3] = txtline_coords[3]
        txtboxbbox  = str(txtbox_coords[0]) + ',' + str(txtbox_coords[1]) + ',' + str(txtbox_coords[2]) + ',' + str(txtbox_coords[3])
        txtbox.set('bbox', txtboxbbox)
    """





    xmlstr = ET.tostring(root, encoding='utf8').decode('utf8')
#    with open('/app/test/sampleresume.words.xml', 'w', encoding='utf8') as xml_file:
#        xml_file.write(xmlstr)

    return xmlstr
