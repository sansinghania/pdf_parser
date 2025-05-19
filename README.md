# pdf_parser
A pdf parser that identifes words, sentenses, sections/layout of the pdf.

Intention of this project is to do a PoC to parse a given pdf document and identify the layout and text of the document. 
The text can then be logically grouped and fed to ML/AI APIs to get more relavant results. The implementation make use of following libraries
- Python Flask - to build the front end for users to select a PDF file
- pdfminer
- jasonpath - to be able to parse json strings

```
URL: http://localhost:5001/convertPDF/index
```

<img width="1361" alt="Screenshot 2025-05-18 at 11 48 25 PM" src="https://github.com/user-attachments/assets/3f43a514-19f5-43ea-acfb-1c158a69d3fc" />
