import os
#import pdf2xml_converter as pdf2xml_converter

def listfiles():
    path_pdf = 'PDFFiles'
    filelist = os.listdir(path_pdf)
    filelist = filter(lambda x: (x.split('.'))[1] == 'pdf', filelist)
    filelist = map(lambda x: path_pdf + '/' + x, filelist)
    xmlstr = ''
    for file in filelist:
        xmlstr = xmlstr + '<file>' + file + '</file>'
    xmlstr = '<filelist>' + xmlstr + '</filelist>'
    return xmlstr

"""
THIS PIECE OF CODE IS NOT NEEDED

for pdffilename in os.listdir(path_pdf):
        pdffile = path_pdf+'/'+pdffilename
        if os.path.isdir(pdffile):
            continue
        if (pdffilename.split('.'))[1] == 'pdf':
            print ('processing .....', pdffile)
            return pdf2pdf2xml_converter.pdf2xml(pdffile)
"""
