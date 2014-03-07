#ifndef WEBPAGE_H_INCLUDED
#define WEBPAGE_H_INCLUDED

#include "WebRessource.h"

using namespace std;

namespace Athena{
    namespace Artemis{

        class WebPage : public WebRessource{
            protected :
                string domain;
                string dir;
                vector< int > hrefElements;
                vector< int > srcElements;

            public :
                WebPage();
                WebPage(string url, string contentType, unsigned int size, string content, unsigned int modified);
                WebPage(unsigned int id, string url, string contentType, unsigned int size, string content, unsigned int modified);

                virtual void setUrl(string param);

                virtual list<string> collectURL();
                virtual void fetchLinks(GumboNode* node, list<string>& links);
                virtual list< string > urlFromLinks(list<string>& links);
        };

    }
}


#endif // WEBPAGE_H_INCLUDED
