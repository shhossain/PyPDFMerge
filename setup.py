from setuptools import setup

version = '0.0.1'
description = 'Merge individual pages of PDF file into one page'

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

name = 'pdf_merger'
author = 'sifat (shhossain)'
email = '<hossain@gmail.com>'

with open('requirements.txt') as f:
    required = f.read().splitlines()

keywords = ['pdf-merger', 'pdf',]

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities',
    'Operating System :: OS Independent',
]

projects_links = {
    "Documentation": "https://github.com/shhossain/pdf-merger/blob/main/README.md",
    "Source": "https://github.com/shhossain/pdf-merger",
    "Bug Report": "https://github.com/shhossain/pdf-merger/issues",
}

setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=author,
    author_email=email,
    url=projects_links["Source"],
    project_urls=projects_links,
    packages=['pdfmerge'],
    install_requires=required,
    keywords=keywords,
    classifiers=classifiers,
    python_requires='>=3.6',
    entry_points={
        "console_scripts": [
            "pdfmerge = pdfmerge.main:main",
        ],
    }
)