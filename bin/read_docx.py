import docx2txt

# TODO: Update to relative path
filename = "/Users/s.hendrickson/Documents/OneDrive - F5, Inc/Projects Folders/1-Chartering/Enhanced Services - Managerial Reporting/Project Charter Template.docx"

# extract text
text = docx2txt.process(filename)

# extract text and write images in /tmp/img_dir
text = docx2txt.process("file.docx", ".")

print(text)
