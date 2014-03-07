#ifndef WEBRESSOURCE_H_INCLUDED
#define WEBRESSOURCE_H_INCLUDED

#include <string>
#include <list>
#include <vector>
#include <algorithm>    // std::find


#include "gumbo.h"

using namespace std;

namespace Athena{
    namespace Artemis{

        class WebRessource{
            protected :
                int type;

                unsigned int id;
                unsigned int size;
                string url;
                string contentType;
                string content;
                unsigned int modified;
            public :
                WebRessource();
                WebRessource(string url, string contentType, unsigned int size, string content, unsigned int modified);
                WebRessource(unsigned int id, string url, string contentType, unsigned int size, string content, unsigned int modified);

                int getId();
                string getUrl();
                string getContentType();
                unsigned int getSize();
                string getContent();
                unsigned int getModified();

                void setId(int param);
                virtual void setUrl(string param);
                void setContentType(string param);
                void setSize(unsigned int param);
                void setContent(string param);
                void setModified(unsigned int param);


                string extractDomain();
                string extractDir();

                virtual list<string> collectURL();
                virtual void fetchLinks(GumboNode* node, list<string>& links);
                virtual list< string > urlFromLinks(list<string>& links);
        };

    }
}

#endif // WEBRESSOURCE_H_INCLUDED
