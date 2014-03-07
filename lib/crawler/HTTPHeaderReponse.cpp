#include "HTTPHeaderReponse.h"

namespace Athena{
    namespace Artemis{
        HTTPHeaderReponse::HTTPHeaderReponse(){
        }

        HTTPHeaderReponse::HTTPHeaderReponse(string const& header){
            parse(header);
        }


        string HTTPHeaderReponse::getContentType(){
            return contentType;
        }


        void HTTPHeaderReponse::setField(string const& name, string const& content){
            if( name == "Content-Type" )
                contentType=content;

        }

        void HTTPHeaderReponse::parse(string const& header){
            int endLine=header.find_first_of("\n");
            int tmpEndLine=endLine;
            int spacer=0;
            string field=header.substr( 0, endLine );


            string name(""), content("");
            int i=0; //Prevent inifinty loop if the header is corrupted
            while( field.size()>0 && i<100  ){ //42 champs
                spacer= field.find_first_of(':');
                name=field.substr(0, spacer);
                content=field.substr(spacer+1, field.size());
                trim( name );
                trim( content );

                setField( name , content  );

                tmpEndLine=header.find_first_of("\n", endLine+2);
                field=header.substr( endLine+1,  tmpEndLine-endLine-2);
                endLine=tmpEndLine;
                i++;
            }
        }



    }


}
