#include "WebPageManager.h"


namespace Athena{
    namespace Artemis{
        WebPageManager::WebPageManager(char* host, char* login, char* password, char* dbName){
            db = new QSqlDatabase( QSqlDatabase::addDatabase("QMYSQL") );
            db->setHostName( host );
            db->setUserName( login );
            db->setPassword( password );
            db->setDatabaseName( dbName );

            query = new QSqlQuery();
            if( !db->open() )
                throw (db->lastError().text()).toStdString();

        }

        WebPageManager::~WebPageManager(){
            db->close();
        }

        void WebPageManager::INSERT(WebPage* page){
            query->prepare("INSERT INTO artemis.webPage( url, contentType, size, content, modified) VALUES (:url, :contentType, :size, :content, :modified)");

            query->bindValue( ":url" , page->getUrl().c_str() );
            query->bindValue(":contentType", page->getContentType().c_str());
            query->bindValue(":size", page->getSize() );
            query->bindValue(":content", page->getContent().c_str() );
            query->bindValue(":modified", QVariant( page->getModified() ) );
            query->exec();
        }

        void WebPageManager::UPDATE(WebPage* page){
            query->prepare("UPDATE artemis.webPage SET( url, contentType, size, content, modified) VALUES (:url, :contentType, :size, :content, :modified) WHERE id=:id");

            query->bindValue(":id", page->getId() );
            query->bindValue( ":url" , page->getUrl().c_str() );
            query->bindValue(":contentType", page->getContentType().c_str());
            query->bindValue(":size", page->getSize() );
            query->bindValue(":content", page->getContent().c_str() );
            query->bindValue(":modified", QVariant( page->getModified() ) );
            query->exec();

        }

        void WebPageManager::DELETE(WebPage* page){
            query->prepare("DELETE FROM artemis.webPage WHERE id=:id");

            query->bindValue(":id", page->getId() );
            query->exec();
        }

        WebPage* WebPageManager::getFromUrl(string url){
            query->prepare("SELECT id, url, contentType, size, content, modified FROM artemis.webPage WHERE url=:url");

            query->bindValue(":url", url.c_str() );
            query->exec();

            if( query->first() ){
                     return new WebPage( query->value( "id" ).toUInt(),
                                         query->value( "url").toString().toStdString(),
                                         query->value( "contentType" ).toString().toStdString(),
                                         query->value( "size" ).toUInt(),
                                         query->value( "content" ).toString().toStdString(),
                                         query->value( "modified" ).toUInt()

                                         );
            }
            return new WebPage();


        }



    }
}
