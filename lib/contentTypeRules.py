from Html import *
from Text import *

contentTypeRules={
	"application/javascript":[Text,TextManager],
	"application/xhtml+xml":[Text,TextManager],
	"application/xml":[Text,TextManager],
	"text/css":[Text,TextManager],
	"text/html":[Html,HtmlManager],
	"text/plain":[Text,TextManager],
	"text/xml":[Text,TextManager]
}
