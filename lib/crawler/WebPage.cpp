#include "WebPage.h"



namespace Athena{
    namespace Artemis{

        WebPage::WebPage(){}

        WebPage::WebPage(string url, string contentType, unsigned int size, string content, unsigned int modified){
            setUrl( url );
            setContent( contentType );
            setSize( size );
            setContent( content );
            setModified( modified );
            type = WebRessources::PAGE;
        }

        WebPage::WebPage(unsigned int id, string url, string contentType, unsigned int size, string content, unsigned int modified){
            WebPage(url, contentType, size, content, modified);
            setId( id );


        }



        void WebPage::setUrl(string param){
            url = param;
            extractDir();
            extractDomain();
        }



        list<string> WebPage::collectURL( ){
            GumboOutput* output = gumbo_parse(content.c_str());
            list< string > links;

            fetchLinks(output->root, links);
            gumbo_destroy_output(&kGumboDefaultOptions, output);
            return urlFromLinks( links );

        }

        void WebPage::fetchLinks(GumboNode* node, list< string >& links){
            if (node->type != GUMBO_NODE_ELEMENT)
                return;

            GumboAttribute* href;
            vector<int>::iterator it1= find( hrefElements.begin(), hrefElements.end(), node->v.element.tag );
            if ( it1 != hrefElements.end() && ( href = gumbo_get_attribute(&node->v.element.attributes, "href") ) ){
                links.push_back( href->value );
            }

            /*GumboAttribute* src;
            vector<int>::iterator it2= find( srcElements.begin(), srcElements.end(), node->v.element.tag );
            if ( it1 != srcElements.end() && ( src = gumbo_get_attribute(&node->v.element.attributes, "src") ) ){
                links.push_back( src->value );
            }*/



            GumboVector* children = &node->v.element.children;
            for (int i = 0; i < children->length; ++i){
                fetchLinks( static_cast<GumboNode*>(children->data[i]), links);
            }
        }

        list< string > WebPage::urlFromLinks(list< string >& links){
            string protocol("");
            string newUrl("");
            list< string > urls;

            for(list< string >::iterator it=links.begin(); it!=links.end(); it++ ){
                protocol=(*it).substr(0,  protocol.find_first_of('//')+2 );//Https
                if( protocol == "https://" || protocol == "http://" )
                    newUrl = (*it);
                else if( protocol[0] == '/' && protocol[1] == '/' ){
                    newUrl = protocol.substr(0, protocol.size()-2 ) + (*it);
                }else
                    if( protocol[0] == '/' ){
                        newUrl = domain + (*it).substr(1, (*it).size());
                    }else
                        newUrl = dir + (*it);

                urls.push_back(newUrl);
            }
            return urls;
        }


    }
}
