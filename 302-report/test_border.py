import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

doc = docx.Document()
section = doc.sections[0]
sectPr = section._sectPr
border_xml = parse_xml(
    f'<w:pgBorders {nsdecls("w")} w:offsetFrom="page">'
    f'<w:top w:val="single" w:sz="12" w:space="24" w:color="1B365D"/>'
    f'<w:left w:val="single" w:sz="12" w:space="24" w:color="1B365D"/>'
    f'<w:bottom w:val="single" w:sz="12" w:space="24" w:color="1B365D"/>'
    f'<w:right w:val="single" w:sz="12" w:space="24" w:color="1B365D"/>'
    f'</w:pgBorders>'
)
sectPr.append(border_xml)
doc.add_paragraph("Testing clean border in docx")
doc.save("302-report/test_border.docx")
print("Border docx created successfully!")
