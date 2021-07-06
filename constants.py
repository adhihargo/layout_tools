# ========== constants for Open Document Spreadsheet creation ==========
CONTENT_FN = "content.xml"
CONTENT_DOCATTRS = set([
    ("xmlns:office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0"),
    ("xmlns:style", "urn:oasis:names:tc:opendocument:xmlns:style:1.0"),
    ("xmlns:text", "urn:oasis:names:tc:opendocument:xmlns:text:1.0"),
    ("xmlns:table", "urn:oasis:names:tc:opendocument:xmlns:table:1.0"),
    ("xmlns:fo", "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"),
    ("xmlns:meta", "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"),
    ("office:version", "1.2")])
SETTINGS_FN = "settings.xml"
SETTINGS_DOCATTRS = set([
    ("xmlns:office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0"),
    ("xmlns:xlink", "http://www.w3.org/1999/xlink"),
    ("xmlns:config", "urn:oasis:names:tc:opendocument:xmlns:config:1.0"),
    ("xmlns:ooo", "http://openoffice.org/2004/office"),
    ("office:version", "1.2")])
META_FN = "meta.xml"
META_DOCATTRS = set([
    ("xmlns:office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0"),
    ("xmlns:xlink", "http://www.w3.org/1999/xlink"),
    ("xmlns:dc", "http://purl.org/dc/elements/1.1/"),
    ("xmlns:meta", "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"),
    ("xmlns:ooo", "http://openoffice.org/2004/office"),
    ("xmlns:grddl", "http://www.w3.org/2003/g/data-view#"),
    ("office:version", "1.2")])
MANIFEST_FN = "META-INF/manifest.xml"
MANIFEST_DATA = r'''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:version="1.2" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>
 <manifest:file-entry manifest:full-path="settings.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''
MIMETYPE_FN = "mimetype"
MIMETYPE_DATA = "application/vnd.oasis.opendocument.spreadsheet"
STYLES_FN = "styles.xml"