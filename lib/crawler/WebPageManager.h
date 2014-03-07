#ifndef WEBPAGEMANAGER_H_INCLUDED
#define WEBPAGEMANAGER_H_INCLUDED


#include <QtSql>
#include <QVariant>

#include <iostream>
#include <sstream>
#include <stdexcept>

#include "WebPage.h"

using namespace std;

namespace Athena{
    namespace Artemis{

        class WebPageManager{
            protected :
                QSqlDatabase* db;
                QSqlQuery* query;



            public:
                WebPageManager(char* host, char* login, char* password, char* dbName);
                ~WebPageManager();

                void INSERT(WebPage* page);
                void UPDATE(WebPage* page);
                void DELETE(WebPage* page);
                WebPage* getFromUrl(string url);
        };
    }


}

#endif // WEBPAGEMANAGER_H_INCLUDED
