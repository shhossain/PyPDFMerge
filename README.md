# PyPDFMerge

Merge individual pages of PDF files into one page

## Demo

### Merging 2 pages into 1

| Before | After |
|---------|---------|
| ![Image 1](https://raw.githubusercontent.com/shhossain/PyPDFMerge/main/image.png) | ![Image 2](https://github.com/shhossain/PyPDFMerge/raw/main/image-1.png) |


## Installation

```bash
pip install PyPDFMerge
```

**NOTE**: You need visual studio build tools for C++ to install `PyPDFMerge` package. Refer to [this](https://pymupdf.readthedocs.io/en/latest/installation.html#installation-when-a-suitable-wheel-is-not-available) for more information.

## Usage

### Command Line

You can use the `PyPDFMerge` command to merge pdf files. It has the following options:

```bash
pdfmerger <path> [-o <output>] [-g <group_size>] [-q <quality>]
```

Example:

```bash
pdfmerger test.pdf
```

This will merge the `test.pdf` file and save it as `output.pdf` in the same directory.

**NOTE**: Output defaults to `output.pdf`, group size defaults to `2`, and quality defaults to `1.5`.

### Python

You can also use the `PyPDFMerge` package in your Python code. It has the following options:

```python
from pdfmerger import PDFMerge

pdf = PDFMerge(pdf_file=<path>, output_file=<output>, group_size=<group_size>, quality=<quality>, page_number=<page_number>)
pdf.run()
```

Example:

```python
from pdfmerger import PDFMerge

pdf = PDFMerge(pdf_file="./test.pdf", output_file="./output.pdf", group_size=2, quality=1.5)
pdf.run()
```
