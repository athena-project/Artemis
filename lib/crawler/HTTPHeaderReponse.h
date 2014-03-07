#ifndef HTTPHEADERREPONSE_H_INCLUDED
#define HTTPHEADERREPONSE_H_INCLUDED

#include <string>
#include <fstream>
#include <boost/algorithm/string.hpp> //trim

using namespace std;
using namespace boost::algorithm;

namespace Athena{
    namespace Artemis{

        class HTTPHeaderReponse{
            protected :
                string contentType;
            public :
                HTTPHeaderReponse();
                HTTPHeaderReponse(string const& header);

                string getContentType();

                void setField(string const& name, string const& content);
                void parse(string const& header);

        };


    }




}





#endif // HTTPHEADERREPONSE_H_INCLUDED


