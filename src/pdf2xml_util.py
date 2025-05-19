import itertools
import xml.etree.ElementTree as ET
from functools import reduce


def word_object (ele):
    word = {}
    word['word_node'] = ele
    word['word_id'] = ele.get('id')
    word['word_text'] = ele.text
    word['word_length'] = len(ele.text)
    word['left'], word['bottom'], word['right'], word['top'] = [round(float(x)) for x in ele.get('bbox').split(',')]
    word['word_width'] = word['right'] - word['left']
    word['word_height'] = word['top'] - word['bottom']
    word['word_bbox'] = ele.get('bbox')
    word['annotations'] = []
    word['font'] = ele.get('font')
    word['size'] = str(round(float(ele.get('size'))))

    if ele.text in [u'\u2022',u'\u25E6',u'\u2219',u'\u2023',u'\u2043', u'\u25cf']:
        word['annotations'].append('marker')

    return (word)


def page_object(page_ele):
    page = {}
    wordlist = [word_object(word_ele) for word_ele in page_ele.iter('word')]
    page['words'] = sorted(wordlist, key = lambda word: (-word['bottom'], word['left']))
    #page['left'], page['bottom'], page['right'], page['top'] = [float(x) for x in page_ele.get('bbox').split(',')]
    page['left'] = round(min([x['left'] for x in wordlist]))
    page['right'] = round(max([x['right'] for x in wordlist]))
    page['top'] = round(max([x['top'] for x in wordlist]))
    page['bottom'] = round(min([x['bottom'] for x in wordlist]))
    page['wcount'] = len([x for x in page['words'] if  'marker' not in x['annotations']])
    p = [x['font']+'-'+x['size'] for x in page['words'] if 'marker' not in x['annotations']]
    page['word_fonts'] = sorted(set([(y,p.count(y)) for y in p]), key=lambda kv: kv[1], reverse=True)
    page['wwidth_avg'] = round(reduce(lambda x, y: (y['right'] - y['left'] + 1) + x, page['words'], 0)/len(page['words']))
    return (page)

#-------------------------------------------------------------------------------
# get_box_wordlist and get_box_fragments are utility methods to find words and
# fragments within a box
#-------------------------------------------------------------------------------
def get_box_wordlist(box, page):
    wordlist = [word for word in page['words'] if word['left'] >= box['left'] and word['right'] <= box['right'] and word['top'] <= box['top'] and word['bottom'] >= box['bottom']]
    return wordlist

def get_box_fragments(box, page):
    fragments = [f for f in page['fragments'] if f['left'] >= box['left'] and f['right'] <= box['right'] and f['top'] <= box['top'] and f['bottom'] >= box['bottom']]
    return fragments

#-------------------------------------------------------------------------------
# prepare_page collects lines, spaces and fragments on the page
#-------------------------------------------------------------------------------
def prepare_page(page):
    page['fragments'] = []
    page['lines'] = get_lines(page, page)

    for line in page['lines']:
        wds = get_box_wordlist(line, page)
        wds = sorted(wds, key = lambda x:(-round(x['bottom']),round(x['left'])))
        line['words'] = wds
        line['fragments'] = []
    collect_word_spaces(page)

    for line in page['lines']:
        tmp = reduce(lambda x, y: create_fragments(y, x), line['words'], (line,page))
        page['fragments'].extend(line['fragments'])
        #wds = []
        #temp = reduce(lambda x, y: wds.extend(y), [x['words'] for x in line['fragments']], [])
        #print(len(line['fragments']), '-', [x['word_text'] for x in wds])
    #collect_fragment_spaces(page)

    #calculate lincespacing that constitute section break and offset
    a, b = itertools.tee(page['lines'])
    next(b, None)
    hgutters = [(x[0]['bottom'], x[0]['bottom'] - x[1]['top']) for x in zip(a, b)]

    p = [x[1] for x in hgutters]
    page['section_break'] = round(1.25 * ((max([(x,p.count(x)) for x in set(p)], key=lambda kv: kv[1]))[0]))
    print ('page section break -', page['section_break'])



#-------------------------------------------------------------------------------
# merge_boxes_horrizontally takes list of boxes on a 2D (x,y) plane and merges
# them together if there is any overlap on the x coordinate.
# The retrun value is a list of boxes that cannot be further merged on the
# x-coordinate
#-------------------------------------------------------------------------------
def merge_boxes_horrizontally(boxes):
    boxes = sorted(boxes, key = lambda box: (box['right']))
    merged_boxes = []
    while len(boxes) > 0:
        b1 = boxes.pop(0)
        x1_list = list(range(round(b1['left']), round(b1['right']+1)))
        merge_flag = False
        for b2 in boxes:
            x2_list = list(range(round(b2['left']), round(b2['right']+1)))
            overlap = len(list(set(x1_list).intersection(x2_list)))

            #ASSUMPTION: columns are merged if there is any overlap
            if overlap > 0:
                #merge b1 and b2 into b
                #print ('Merging boxes ................')
                b = {}
                b['left'] = min(b1['left'], b2['left'])
                b['right'] = max(b1['right'], b2['right'])
                b['top'] = max(b1['top'], b2['top'])
                b['bottom'] = min(b1['bottom'], b2['bottom'])
                boxes.append(b)
                boxes.remove(b2)
                merge_flag = True
                #print ('..... merged boxes')
                break
        if not (merge_flag):
            merged_boxes.append(b1)
    merged_boxes = sorted(merged_boxes, key = lambda box: (box['right']))
    return merged_boxes


#-------------------------------------------------------------------------------
# get_columns gets non-overlapping columns based on text fragments on the page
# It looks for fragment with in the target box and calls
# merge_boxes_horrizontally to find non-overlapping columns
#-------------------------------------------------------------------------------
def get_columns(box, page):
    fragments = get_box_fragments(box, page)
    columns = merge_boxes_horrizontally(fragments)

    # merge columns if the left column has only fragments that are 'bullet'
    a, b = itertools.tee(columns)
    tobe_merged=[]
    next(b, None)
    for p in zip(a, b):
        total_fragments = get_box_fragments(p[0], page)
        bullet_fragments = [x for x in total_fragments if x['annotation'] == 'bullet']
        if len(total_fragments) == len(bullet_fragments):
            tobe_merged.append(p)

    for p in tobe_merged:
        c1, c2 = p[0], p[1]
        c = {}
        c['left'] = min(c1['left'], c2['left'])
        c['right'] = max(c1['right'], c2['right'])
        c['top'] = max(c1['top'], c2['top'])
        c['bottom'] = min(c1['bottom'], c2['bottom'])
        columns.remove(c1)
        columns.remove(c2)
        columns.append(c)
    return columns


#-------------------------------------------------------------------------------
# merge_boxes_vertically takes list of boxes on a 2D (x,y) plane and merges
# them together if there is overlap 25% on the y coordinate.
# The retrun value is a list of boxes that cannot be further merged on the
# y-coordinate
#-------------------------------------------------------------------------------
def merge_boxes_vertically(boxes):
    boxes = sorted(boxes, key = lambda box: (-box['bottom']))
    merged_boxes = []
    while len(boxes) > 0:
        b1 = boxes.pop(0)
        y1_list = list(range(round(b1['bottom']), round(b1['top']+1)))
        merge_flag = False
        for b2 in boxes:
            y2_list = list(range(round(b2['bottom']), round(b2['top']+1)))
            overlap = len(list(set(y1_list).intersection(y2_list)))

            #ASSUMPTION: columns are merged if there is any overlap
            if (float(overlap)/len(y1_list) > 0.25) or  (float(overlap)/len(y2_list) > 0.25):
                #merge b1 and b2 into b
                #print ('Merging boxes ................')
                b = {}
                b['left'] = min(b1['left'], b2['left'])
                b['right'] = max(b1['right'], b2['right'])
                b['top'] = max(b1['top'], b2['top'])
                b['bottom'] = min(b1['bottom'], b2['bottom'])
                boxes.append(b)
                boxes.remove(b2)
                merge_flag = True
                #print ('..... merged boxes')
                break
        if not (merge_flag):
            merged_boxes.append(b1)
    merged_boxes = sorted(merged_boxes, key = lambda box: (-box['bottom']))
    return merged_boxes

#------------------------------------------------------------------------------
# get_segments identify segments (rows) that group text with in a box.
#------------------------------------------------------------------------------
def get_sections(box, page):
    fragments = get_box_fragments(box, page)

    #print ('# of fragments in get_sections (COL) -', len(fragments), '........', 'COL top', box['top'], 'COL bottom', box['bottom'])
    #for f in fragments:
    #    print (f['top'], f['bottom'], [w['word_text'] for w in f['words']])

    fragments = merge_boxes_vertically(fragments)

    #print ('# of fragments in get_sections (COL) -', len(fragments), '........', 'COL top', box['top'], 'COL bottom', box['bottom'])
    #for f in fragments:
    #    print (f['top'], f['bottom'])
    #    print ([w['word_text'] for w in get_box_wordlist(f, page)])

    #identify sections by finding horizontal spacers
    sections = []
    section = None
    if len(fragments) == 1:
        h = [box['top'], box['bottom']]
    else:
        #calculate lincespacing that constitute section break and offset
        a, b = itertools.tee(fragments)
        next(b, None)
        hgutters = [(x[0]['bottom'], x[0]['bottom'] - x[1]['top']) for x in zip(a, b)]
        """
        p = [x[1] for x in hgutters]
        section_break = (max([(x,p.count(x)) for x in set(p)], key=lambda kv: kv[1]))[0]
        offset = round(0.25 * section_break)
        #print ('hgutters - ', hgutters)
        #print ('section break -', section_break, 'offset - ', offset)
        """

        h = [box['top']]
        #h.extend([x[0] for x in hgutters if x[1] > section_break + offset])
        h.extend([x[0] for x in hgutters if x[1] > page['section_break']])
        h.append(box['bottom'])
        #print ('section breaks - ', h)

    a, b = itertools.tee(h)
    next(b, None)
    for p in zip(a, b):
        frags = [x for x in fragments if p[0] > x['bottom'] >= p[1] ]
        section = {}
        section['left'], section['right'] = box['left'], box['right']
        section['top'] = max([x['top'] for x in frags])
        section['bottom'] = min([x['bottom'] for x in frags])
        sections.append(section)

    #print ('# of sections in the COL - ', len(sections))
    #for s in sections:
    #    print('SECTION box - ', s['top'], s['bottom'])
    #print('.')
    return sections

#------------------------------------------------------------------------------
# get_segments identify segments (columns and rows) that group text with in a
# box.
# The logic is to first find columns and then finding sections within columns.
# This is repleated recurrsively until it cannot break the box further into new
# columns/rows
#------------------------------------------------------------------------------
def get_segments(box, page):
    columns = get_columns(box, page)
    for col in columns:
        #print (ctab, 'COL .....', '(left)-', col['left'], '(right)-', col['right'], '(top)-', col['top'], '(bottom)-', col['bottom'])
        #print(tab, '(left)-', col['left'], '(right)-', col['right'], '(top)-', col['top'], '(bottom)-', col['bottom'])
        rows = get_sections(col, page)
        if len(rows) == 1:
            page['segments'].append(rows[0])
        else:
            for row in rows:
                #print ('printing row information .....')
                #print('(left)-', row['left'], '(right)-', row['right'], '(top)-', row['top'], '(bottom)-', row['bottom'])
                #print ([x['word_text'] for x in get_box_wordlist(row, page)])
                #print ('-')
                get_segments(row, page)

#------------------------------------------------------------------------------
# get_lines identify lines in a box based on the words within the box.
# It then sets some key properties on the line
#------------------------------------------------------------------------------
def get_lines(box, page):
    words = get_box_wordlist(box, page)
    lines = merge_boxes_vertically(words)
    return lines


#------------------------------------------------------------------------------
# collect_word_spaces identify word spacing by identifying words in a line and
# then caluclating space based on x-coordniate
#------------------------------------------------------------------------------
def collect_word_spaces(page):
    page['wspaces'] = []
    for line in page['lines']:
        line['wspaces'] = []
        a, b = itertools.tee(line['words'])
        next(b, None)
        for pair in zip(a, b):
            w1, w2 = pair[0], pair[1]
            #a line can have words that are in multiple rows due to merging of lines
            #the following if condition ensures that space is calculated only for subsequent
            #words in the line that are in the same row
            if w1['right'] <= w2['left']:
                space = {}
                space['left'], space['right'], space['top'], space['bottom'] = w1['right'], w2['left'], w1['top'], w1['bottom']
                line['wspaces'].append(space)
                page['wspaces'].append(space)

        if len(line['wspaces']) > 0:
            line['wspaces_avg'] = round(reduce(lambda x, y: (y['right'] - y['left']) + x, line['wspaces'], 0)/len(line['wspaces']))
        else:
            line['wspaces_avg'] = 0
    page['wspaces_avg'] = round(reduce(lambda x, y: (y['right'] - y['left']) + x, page['wspaces'], 0)/len(page['wspaces']))
    #print(len(page['wspaces']), page['wspaces_avg'])


#------------------------------------------------------------------------------
# collect_fragment_spaces identify fragment spacing by identifying fragments
# in a line and then caluclating space based on x-coordniate
#------------------------------------------------------------------------------
def collect_fragment_spaces(page):
    page['fspaces'] = []
    for line in page['lines']:
        line['fspaces'] = []
        a, b = itertools.tee(line['fragments'])
        next(b, None)
        for pair in zip(a, b):
            f1, f2 = pair[0], pair[1]
            #a line can have words that are in multiple rows due to merging of lines
            #the following if condition ensures that space is calculated only for subsequent
            #words in the line that are in the same row
            if f1['right'] <= f2['left']:
                space = {}
                space['left'], space['right'], space['top'], space['bottom'] = f1['right'], f2['left'], f1['top'], f1['bottom']
                line['fspaces'].append(space)
                page['fspaces'].append(space)

        if len(line['fspaces']) > 0:
            line['fspaces_avg'] = round(reduce(lambda x, y: (y['right'] - y['left']) + x, line['fspaces'], 0)/len(line['fspaces']))
        else:
            line['fspaces_avg'] = 0
    page['fspaces_avg'] = round(reduce(lambda x, y: (y['right'] - y['left']) + x, page['fspaces'], 0)/len(page['fspaces']))
    #print(len(page['wspaces']), page['wspaces_avg'])


#------------------------------------------------------------------------------
# create_fragments accumulate words in a line and creates fragments that are
# identical in font and size
#------------------------------------------------------------------------------
def create_fragments(w, argx):
    #print (w['word_text'], len(line['fragments']))
    line, page = argx[0], argx[1]
    l = len(line['fragments'])

    if w['word_text'] in [u'\u2022',u'\u25E6',u'\u2219',u'\u2023',u'\u2043', u'\u25cf', u'\uf0d8', u'\uf0b7', u'\uf0a7']:
        x = {}
        x['words'] = [w]
        x['top'], x['bottom'] = round(w['top']), round(w['bottom'])
        x['left'], x['right'] = round(w['left']), round(w['right'])
        #font of the fragment is marked as bullet. this will change to the font of the first real word
        x['font'], x['size'] = 'bullet', w['size']
        #the fragment is identified as bullet and will remain as bullet
        x['annotation'] = 'bullet'
        line['fragments'].append(x)
        return (line,page)
    if l > 0:
        x = line['fragments'][l-1]
        #if x['font'] == w['font'] and x['size'] == w['size'] and 0 <= w['left'] - x['right'] <= 1.25 * page['wspaces_avg']:
        if x['font'] == w['font'] and x['size'] == w['size'] and 0 <= w['left'] - x['right'] <= 0.50* page['wwidth_avg']:
            x['words'].append(w)
            x['right'] = round(w['right'])
            return (line, page)

    x = {}
    x['words'] = [w]
    x['top'], x['bottom'] = round(w['top']), round(w['bottom'])
    x['left'], x['right'] = round(w['left']), round(w['right'])
    x['font'], x['size'] = w['font'], w['size']
    x['indent'] = w['left']
    x['annotation'] = ''
    line['fragments'].append(x)
    return (line,page)



def merge_boxes(b1, b2):
    rslt = [b1, b2]
    y1_list = list(range(round(b1['bottom']), round(b1['top']+1)))
    y2_list = list(range(round(b2['bottom']), round(b2['top']+1)))
    overlap = len(list(set(y1_list).intersection(y2_list)))

    if (float(overlap)/len(y1_list) > 0.25) or  (float(overlap)/len(y2_list) > 0.25):
        #merge b1 and b2 into b
        #print ('Merging boxes ................')
        b = {}
        b['words'] =[]
        b['left'] = min(b1['left'], b2['left'])
        b['right'] = max(b1['right'], b2['right'])
        b['top'] = max(b1['top'], b2['top'])
        b['bottom'] = min(b1['bottom'], b2['bottom'])
        rslt = [None, b]
    return rslt

"""
def mark_lines(page):
    wordlist = page['words']

    #fetch h-lines
    ln = [round(page['top'] + 1)]
    ln.extend([round(x['bottom']) for x in wordlist])
    ln = sorted(set(ln), reverse=True)

    #set left, top, right for the line based on the words it contains
    lines = []
    a, b = itertools.tee(ln)
    next(b, None)
    for pair in zip(a, b):
        ln_words = [x for x in wordlist if pair[0] > round(x['bottom']) >= pair[1]]
        line = {}
        line['bottom'] = pair[1]
        line['top'] = round(max([x['top'] for x in ln_words]))
        #line['left'] = round(min([x['left'] for x in ln_words]))
        #line['right'] = round(max([x['right'] for x in ln_words]))
        line['left'], line['right'] = page['left'], page['right']
        lines.append(line)


    #merge overlapping lines into one
    new_lines = []
    line1, line2 = None, None
    for line in lines:
        line1 = line2
        line2 = line
        if line1 != None and line2 != None:
            rslt = merge_boxes(line1, line2)
            if rslt[0] != None:
                new_lines.append(rslt[0])
            line2 = rslt[1]
    new_lines.append(line2)


    line_id = 0
    for line in new_lines:
        line_id += 1
        line['id'] = 'lin-' + str(line_id)

        wds = [x for x in wordlist if (line['top'] >= round(x['top']) and round(x['bottom']) >= line['bottom'])]
        #wds = sorted(wds, key = lambda x:round(x['left']))
        wds = sorted(wds, key = lambda x:(-round(x['bottom']),round(x['left'])))
        line['words'] = wds

        line['fragments'] =[]

        #line['words'][0]['annotations'] = line['words'][0]['annotations'].append('ln-begin')

        line['wcount'] = len([x for x in line['words'] if 'marker' not in x['annotations']])
        p = [x['font']+'-'+x['size'] for x in line['words'] if 'marker' not in x['annotations']]
        line['word_fonts'] = sorted(set([(y,p.count(y)) for y in p]), key=lambda kv: kv[1], reverse=True)
        line['annotations'] = None

    page['lines'] = new_lines

    #for line in new_lines:
    #    print ('line ------', line['id'], line['top'], line['bottom'])
    #    print ([x['word_text'] for x in line['words']], '-', line['wcount'], line['word_fonts'])
"""


def merge_lines(l1, l2, parent):
    rslt = [l1, l2]

    if len(l1['fragments'])>1 or len(l2['fragments'])>1:
        None
    elif l2['fragments'][0]['annotation'] == 'bullet':
        None
    else:

        f1, f2 = l1['fragments'][0], l2['fragments'][0]
        f1_word = f1['words'][len(f1['words'])-1]
        f1_rmargin = round(parent['right'] - f1_word['right'])
        f2_fwordwidth = f2['words'][0]['word_width']
        print('--------------------')
        print ('f1 -', [x['word_text'] for x in f1['words']])
        print('fragment1 -', f1['font'], f1['size'], f1['left'], f1['right'], f1['top'], f1['bottom'])
        print ('f2 -', [x['word_text'] for x in f2['words']])
        print('fragment2 -', f2['font'], f2['size'], f2['left'], f2['right'], f2['top'], f2['bottom'])
        print (f1_rmargin, f2_fwordwidth)
        #print (word['right'] - word['left'])

        if f1['font'] == f2['font'] and f1['size'] == f2['size'] and f1['indent'] == f2['indent'] and f1_rmargin < f2_fwordwidth:
            print (' ************  merging f1 and f2')
            print('l1 -', l1['left'], l1['right'], l1['top'], l1['bottom'])
            print('l2 -', l2['left'], l2['right'], l2['top'], l2['bottom'])
            #print ('f1 -', [x['word_text'] for x in f1['words']])
            #print ('f2 -', [x['word_text'] for x in f2['words']])
            #print('fragment1 -', f1['left'], f1['right'], f1['top'], f1['bottom'])
            #print('fragment2 -', f2['left'], f2['right'], f2['top'], f2['bottom'])

            f = {}
            f['left'] = min(f1['left'], f2['left'])
            f['right'] = max(f1['right'], f2['right'])
            f['top'] = max(f1['top'], f2['top'])
            f['bottom'] = min(f1['bottom'], f2['bottom'])
            f['indent'] = f1['indent']
            f['font'] = f1['font']
            f['size'] = f1['size']
            f['words'] = []
            f['words'].extend(f1['words'])
            f['words'].extend(f2['words'])

            l = {}
            l['left'] = f['left']
            l['right'] = f['right']
            l['top'] = f['top']
            l['bottom'] = f['bottom']
            l['fragments'] = [f]
            l['words'] = f['words']
            print('New line -', l['left'], l['right'], l['top'], l['bottom'])
            print('New fragment -', f['left'], f['right'], f['top'], f['bottom'])


            #wds = []
            #temp = reduce(lambda x, y: wds.extend(y), [x['words'] for x in l1['fragments']], [])
            #temp = reduce(lambda x, y: wds.extend(y), [x['words'] for x in l2['fragments']], [])


            rslt = [None, l]

    return rslt



def mark_sections(page):
    wordlist = page['words']
    linelist = page['lines']

    #calculate lincespacing that constitute section break and offset
    a, b = itertools.tee(linelist)
    next(b, None)
    lines = [(linelist[0], linelist[0]['top'], linelist[0]['bottom'], linelist[0]['top'] - linelist[0]['bottom'])] # add the first line
    lines.extend([(x[1], x[0]['bottom'], x[1]['bottom'], x[0]['bottom'] - x[1]['bottom']) for x in zip(a, b)])
    #lines.extend([(x[1], x[0]['bottom'], x[1]['top'], x[0]['bottom'] - x[1]['top']) for x in zip(a, b)])

    q = [y[3] for y in lines]
    section_break = (max([(x,q.count(x)) for x in set(q)], key=lambda kv: kv[1]))[0]
    offset = round(0.25 * section_break)

    #print ('(section break)-', section_break, '(offset)-', offset)
    #for line in lines:
    #    print ('(#fragments)-', len(line[0]['fragments']), '(line width)-',line[3], '---', [word['word_text'] for word in line[0]['words']])

    #find first line of sections based on section breaks
    section_fl = [x[0] for x in lines if x[3] > (section_break + offset)]
    #print ([(x['top'], x['bottom']) for x in section_fl])

    #set left, right, top and bottom of the section
    sectionlist = []
    section = None
    for line in linelist:
        if line in section_fl or line == linelist[0]:
            if section != None:
                #section['left'] = min([x['left'] for x in wordlist if (section['top'] >= round(x['top']) and round(x['bottom']) >= section['bottom'])])
                #section['right'] = max([x['right'] for x in wordlist if (section['top'] >= round(x['top']) and round(x['bottom']) >= section['bottom'])])
                section['left'], section['right'] = page['left'], page['right']
                sectionlist.append(section)
            section = {}
            section['top'] = line['top']
            section['bottom'] = line['bottom']
        else:
            section['bottom'] = line['bottom']
    if section != None:
        #section['left'] = min([x['left'] for x in wordlist if (section['top'] >= round(x['top']) and round(x['bottom']) >= section['bottom'])])
        #section['right'] = max([x['right'] for x in wordlist if (section['top'] >= round(x['top']) and round(x['bottom']) >= section['bottom'])])
        section['left'], section['right'] = page['left'], page['right']
        sectionlist.append(section)

    #merge overlapping sections into one
    new_sectionlist = []
    section1, section2 = None, None
    for section in sectionlist:
        section1 = section2
        section2 = section
        if section1 != None and section2 != None:
            rslt = merge_boxes(section1, section2)
            if rslt[0] != None:
                new_sectionlist.append(rslt[0])
            section2 = rslt[1]
    new_sectionlist.append(section2)

    section_id = 0
    for section in new_sectionlist:
        section_id += 1
        section['id'] = 'sec-' + str(section_id)

        lns = [x for x in linelist if (section['top'] >= round(x['top']) and round(x['bottom']) >= section['bottom'])]
        lns = sorted(lns, key = lambda x:round(x['bottom']), reverse=True)
        section['lines'] = lns

        wds = []
        temp = reduce(lambda x, y: wds.extend(y), [x['words'] for x in section['lines']], [])
        section['words'] = wds

        #section['left'] = round(min(x['left'] for x in section['words']))
        #section['right'] = round(max(x['right'] for x in section['words']))

        spacers = [x for x in page['wspaces'] if (section['top'] >= round(x['top']) and round(x['bottom']) >= section['bottom'])]
        section['wspaces'] = [x for x in spacers if x['right']-x['left'] > 1.25 * page['wspaces_avg']]

        #post_process_sections(section, page)

    page['sections'] = new_sectionlist


def post_process_sections(section, page):
    #sapcers = [x for x in page['wspaces'] if (section['top'] >= round(x['top']) and round(x['bottom']) >= section['bottom'])]
    #identify lines with bullets

    new_lines = []
    line1, line2 = None, None
    for line in section['lines']:
        line1 = line2
        line2 = line
        if line1 != None and line2 != None:
            rslt = merge_lines(line1, line2, section)
            if rslt[0] != None:
                new_lines.append(rslt[0])
            line2 = rslt[1]
    new_lines.append(line2)
    section['lines'] = new_lines

"""
#------------------------------------------------------------------------------
# create_fragments accumulate words in a line and creates fragments that are
# identical in font and size
#------------------------------------------------------------------------------
def create_logical_fragments(word, argx):
    #print (w['word_text'], len(line['fragments']))
    segment, page = argx[0], argx[1]
    l = len(line['l-fragments'])

    if w['word_text'] in [u'\u2022',u'\u25E6',u'\u2219',u'\u2023',u'\u2043', u'\u25cf', u'\uf0d8', u'\uf0b7', u'\uf0a7']:
        x = {}
        x['words'] = [w]
        #x['top'], x['bottom'] = round(w['top']), round(w['bottom'])
        #x['left'], x['right'] = round(w['left']), round(w['right'])
        #font of the fragment is marked as bullet. this will change to the font of the first real word
        x['font'], x['size'] = 'bullet', w['size']
        #the fragment is identified as bullet and will remain as bullet
        x['annotation'] = 'bullet'
        segment['l-fragments'].append(x)
        return (segment,page)
    if l > 0:
        x = segment['l-fragments'][l-1]
        if x['font'] == 'bullet' or (x['font'] == w['font'] and x['size'] == w['size']): # and 0 <= w['left'] - x['right'] <= 1.25 * page['wspaces_avg']:
            x['words'].append(w)
            x['font'], x['size'] = w['font'], w['size']
            #x['right'] = round(w['right'])
            return (segment, page)

    x = {}
    x['words'] = [w]
    #x['top'], x['bottom'] = round(w['top']), round(w['bottom'])
    #x['left'], x['right'] = round(w['left']), round(w['right'])
    x['font'], x['size'] = w['font'], w['size']
    #x['indent'] = w['left']
    x['annotation'] = ''
    segment['l-fragments'].append(x)
    return (segment,page)


#------------------------------------------------------------------------------
# create_fragments accumulate words in a line and creates fragments that are
# identical in font and size
#------------------------------------------------------------------------------
def merge_fragments(fragment, segment):
    fragments = line['fragments']

    # merge fragments if two subsequent fragments are close
    # (space <= page['fspaces_avg']) and are identical in font and size

    a, b = itertools.tee(fragments)
    tobe_merged=[]
    next(b, None)
    for p in zip(a, b):
        f1, f2 = p[0], p[1]
        if f1['annotation'] == 'bullet' or f2['annotation'] == 'bullet':
            break
        if f1['font'] == f2['font'] and f1['size'] == f2['size'] and 0 <= f2['left'] - f1['right'] <= 1.25 * page['fspaces_avg']:
            tobe_merged.apend(p)

    for p in tobe_merged:
        f1, f22 = p[0], p[1]
        f = {}
        f['left'] = min(f1['left'], f2['left'])
        f['right'] = max(f1['right'], f2['right'])
        f['top'] = max(f1['top'], f2['top'])
        f['bottom'] = min(f1['bottom'], f2['bottom'])
        f['words'] = f1['words']
        f['words'].extend(f2['words'])
        f['fornt'], f['size'], f['indent'] = f1['font'], f1['size'], f1['indent']
        f['annontation'] = ''
        fragments.remove(f1)
        fragments.remove(f2)
        fragments.append(f)
    return fragments
"""

def post_process_segment(segment, page):
    lines = get_lines(segment, page)
    for line in lines:
        line['fragments'] = sorted(get_box_fragments(line, page), key=lambda fragment: (fragment['left'], -fragment['bottom']))

    fragments = []
    temp = reduce(lambda x, y: fragments.extend(y), [x['fragments'] for x in lines], [])
    wds = []
    temp = reduce(lambda x, y: wds.extend(y), [x['words'] for x in fragments], [])
    print ([x['word_text'] for x in wds])

    #print ('# of fragments in the segment - ', len(fragments))
    #for fragment in fragments:
    #    print (fragment['left'], fragment['right'], fragment['top'], fragment['bottom'], fragment['font'], fragment['size'])
    #    print ([x['word_text'] for x in fragment['words']])
    #    print ('.')


def prepare_page_xml(pg, page):
    if pg.get('sections') == None:
        sectionlist = []
    else:
        sectionlist = pg['sections']

    #remove all existing nodes of the page
    txtlinelist = list(page.iter('textline'))
    for txtline in txtlinelist:
        page.remove(txtline)

    #create new nodes
    for section in sectionlist:
        section_ele = ET.SubElement(page, 'section')
        sectionbbox  = str(section['left']) + ',' + str(section['bottom']) + ',' + str(section['right']) + ',' + str(section['top'])
        section_ele.set('bbox', sectionbbox)


    if pg.get('segments') == None:
        segments = []
    else:
        segments = pg['segments']

    for segment in segments:
        segment_ele = ET.SubElement(page, 'segment')
        segmentbbox  = str(segment['left']) + ',' + str(segment['bottom']) + ',' + str(segment['right']) + ',' + str(segment['top'])
        segment_ele.set('bbox', segmentbbox)

        frgs = get_box_fragments(segment, pg)
        #temp = reduce(lambda x, y: frgs.extend(y), [x['fragments'] for x in section['lines']], [])
        for f in frgs:
            frg_ele = ET.SubElement(segment_ele, 'fragment')
            frgbbox  = str(f['left']) + ',' + str(f['bottom']) + ',' + str(f['right']) + ',' + str(f['top'])
            frg_ele.set('bbox', frgbbox)
            #wordlist = reduce(lambda x, y: extend_list(y, x), section['section_lines'], [])
            wordlist = get_box_wordlist(f, pg)
            for word in wordlist:
                wordbbox  = str(word['left']) + ',' + str(word['bottom']) + ',' + str(word['right']) + ',' + str(word['top'])
                ele = ET.SubElement(frg_ele, 'word')
                ele.text = word['word_text']
                ele.set('font',word['font'])
                ele.set('size',word['size'])
                ele.set('bbox',wordbbox)

        #for space in section['wspaces']:
        #    box  = str(space['left']) + ',' + str(space['bottom']) + ',' + str(space['right']) + ',' + str(space['top'])
        #    ele = ET.SubElement(section_ele, 'spacer')
        #    ele.set('bbox',box)
        #sectionbbox  = str(section_coords[0]) + ',' + str(section_coords[1]) + ',' + str(section_coords[2]) + ',' + str(section_coords[3])



"""
def prepare_page_xml(pg, page):
    if pg.get('sections') == None:
        sectionlist = []
    else:
        sectionlist = pg['sections']

    #remove all existing nodes of the page
    txtlinelist = list(page.iter('textline'))
    for txtline in txtlinelist:
        page.remove(txtline)

    #create new nodes
    for section in sectionlist:
        section_ele = ET.SubElement(page, 'section')
        sectionbbox  = str(section['left']) + ',' + str(section['bottom']) + ',' + str(section['right']) + ',' + str(section['top'])
        section_ele.set('bbox', sectionbbox)
        frgs = []
        temp = reduce(lambda x, y: frgs.extend(y), [x['fragments'] for x in section['lines']], [])
        for f in frgs:
            frg_ele = ET.SubElement(section_ele, 'fragment')
            frgbbox  = str(f['left']) + ',' + str(f['bottom']) + ',' + str(f['right']) + ',' + str(f['top'])
            frg_ele.set('bbox', frgbbox)
            #wordlist = reduce(lambda x, y: extend_list(y, x), section['section_lines'], [])
            wordlist = f['words']
            for word in wordlist:
                wordbbox  = str(word['left']) + ',' + str(word['bottom']) + ',' + str(word['right']) + ',' + str(word['top'])
                ele = ET.SubElement(frg_ele, 'word')
                ele.text = word['word_text']
                ele.set('font',word['font'])
                ele.set('size',word['size'])
                ele.set('bbox',wordbbox)
        for space in section['wspaces']:
            box  = str(space['left']) + ',' + str(space['bottom']) + ',' + str(space['right']) + ',' + str(space['top'])
            ele = ET.SubElement(section_ele, 'spacer')
            ele.set('bbox',box)
        #sectionbbox  = str(section_coords[0]) + ',' + str(section_coords[1]) + ',' + str(section_coords[2]) + ',' + str(section_coords[3])

    if pg.get('segments') == None:
        segments = []
    else:
        segments = pg['segments']

    for segment in segments:
        segment_ele = ET.SubElement(page, 'segment')
        segmentbbox  = str(segment['left']) + ',' + str(segment['bottom']) + ',' + str(segment['right']) + ',' + str(segment['top'])
        segment_ele.set('bbox', segmentbbox)
"""

def post_process_xml(root):
    pages = root.findall('page')
    for pg in pages:
        page = page_object(pg)
        prepare_page(page)

        page['segments'] = []
        get_segments(page, page)

        print ('************ # of segments = ', len(page['segments']), ' ***************')
        for segment in page['segments']:
            print('(left)-', segment['left'], '(right)-', segment['right'], '(top)-', segment['top'], '(bottom)-', segment['bottom'])
            post_process_segment(segment, page)

        #collect_spaces(page)
        #post_process_lines(page)
        mark_sections(page)
        prepare_page_xml(page, pg)

"""
        all_spacers = [get_space_coords(x) for x in zip(a, b)]
        word_spacers = [x for x in all_spacers if (x[2] >= x[0] and x[3] >= x[1])]
        line_spacers = [x for x in all_spacers if not (x[2] >= x[0] and x[3] >= x[1])]


        print (len(all_spacers), len(word_spacers), len(line_spacers))
        for line_spacer in line_spacers:
            print ('vertical spacing - ', round(line_spacer[1] - line_spacer[3]))

        for coord in all_spacers:
            if coord[0] > coord[2] and coord[1] > coord[3] + 3:
                bbox = str(coord[2]) + ',' + str(coord[3]) + ',' + str(coord[0]) + ',' + str(coord[1])
                ele = ET.SubElement(page, 'linespacer')
                ele.set('bbox',bbox)
            else:
                bbox = str(coord[0]) + ',' + str(coord[1]) + ',' + str(coord[2]) + ',' + str(coord[3])
                ele = ET.SubElement(page, 'spacer')
                ele.set('bbox',bbox)
"""
