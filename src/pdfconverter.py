from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, XMLConverter, HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import BytesIO

def convert_pdf(path, format='text', codec='utf-8', password=''):
    rsrcmgr = PDFResourceManager()
    retstr = BytesIO()
    laparams = LAParams()
    if format == 'text':
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    elif format == 'html':
        device = HTMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    elif format == 'xml':
        device = XMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    else:
        raise ValueError('provide format, either text, html or xml!')
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    maxpages = 0
    caching = True
    pagenos=set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue().decode()
    fp.close()
    device.close()
    retstr.close()

    #fix the missing tag issue in the output from pdfMiner????
    if format == 'xml':
        text = text+'</pages>'
    return text

def pdf2xml(pdfFilename):
    print("executing pdf2xml")
    #pdfFilename = '/app/test/sampleresume.pdf'
    text = convert_pdf(pdfFilename, 'xml')
    print('conversion complete....')
    return text

def pdf2txt(pdfFilename):
    print("executing pdf2txt")
    #pdfFilename = '/app/test/sampleresume.pdf'
    text = convert_pdf(pdfFilename, 'text')
    print('conversion complete....')
    return text

def pdf2html(pdfFilename):
    print("executing pdf2html")
    #pdfFilename = '/app/test/sampleresume.pdf'
    text = convert_pdf(pdfFilename, 'html')
    print('conversion complete....')
    return text

if __name__ == '__main__':
    print("pdf2txt loaded")
    pdfFilename = '/app/test/sampleresume.pdf'
    text = convert_pdf(pdfFilename, 'xml')
    print('conversion complete.... printing text')
    with open('/app/test/sampleresume.txt', 'w', encoding='utf-8') as xml_file:
        xml_file.write(text)
