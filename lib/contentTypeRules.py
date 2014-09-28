from Html import *
from Text import *

textHandler	= TextHandler( TextManager() )
htmlHandler = HtmlHandler( HtmlManager() )

contentTypeRules={
	"application/javascript":[Text,textHandler],
	"application/xhtml+xml":[Text,textHandler],
	"application/xml":[Text,textHandler],
	"text/css":[Text,textHandler],
	"text/html":[Html,htmlHandler],
	"text/plain":[Text,textHandler],
	"text/xml":[Text,textHandler]
}
