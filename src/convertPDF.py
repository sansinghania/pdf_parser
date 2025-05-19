from flask import Flask, render_template, Response
import pdf2xml_converter as pdf2xml_converter
import listPDFfiles as listPDFfiles
app = Flask(__name__)

@app.route('/convertPDF')
@app.route('/convertPDF/index')
def default():
    return render_template('index.html')

""" 
@app.route('/convertPDF/text/<filename>')
@app.route('/convertPDF/text')
def pdf2txt(filename = 'sampleresume.pdf'):
    path = 'test/'
    #return pdfconverter.pdf2txt(path+filename)
    return Response(pdfconverter.pdf2txt(path+filename), mimetype='text')

@app.route('/convertPDF/html/<filename>')
@app.route('/convertPDF/html')
def pdf2html(filename = 'sampleresume.pdf'):
    path = 'test/'
    #return pdfconverter.pdf2html(path+filename)
    return Response(pdfconverter.pdf2html(path+filename), mimetype='text/html')

@app.route('/convertPDF/xml/<filename>')
@app.route('/convertPDF/xml')
def pdf2xml(filename = 'sampleresume.pdf'):
    path = 'test/'
    return Response(pdfconverter.pdf2xml(path+filename), mimetype='text/xml')
    #return pdfconverter.pdf2xml() 
"""

@app.route('/convertPDF/xml_custom/<filename>')
@app.route('/convertPDF/xml_custom')
def pdf2xml_custom(filename = 'sampleresume.pdf'):
    print (filename);    
    path = 'PDFFiles/'
    return Response(pdf2xml_converter.pdf2xml(path+filename), mimetype='text/xml')

@app.route('/convertPDF/listfiles')
def listfiles():
    return Response(listPDFfiles.listfiles(), mimetype='text/xml')

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5001)
