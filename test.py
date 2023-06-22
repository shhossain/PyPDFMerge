from pdfmerge import PDFMerge

path = "some.pdf"
pdf = PDFMerge(path, group_size=2, quality=1.5, debug=False, output_file="output.pdf")
pdf.run()
