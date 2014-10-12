from Html import *
from Text import *

#Correspndance between rType and contentType
contentTypeRules={
	"application/javascript":"text",
	"application/xhtml+xml":"html",
	"application/xml":"text",
	"text/css":"text",
	"text/html":"html",
	"text/plain":"text",
	"text/xml":"text",
}

rTypes={
	"text":[Text, TextRecord, TextManager, TextHandler],
	"html":[Html, HtmlRecord, HtmlManager, HtmlHandler]
}
