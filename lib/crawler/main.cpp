#include <cstdlib>
#include <iostream>
#include "Artemis/WebCrawler.h"
#include "Artemis/HTTPHandler.h"
#include <pthread.h>

//#include <cstdlib>
//#include "mongo/client/dbclient.h"

using namespace std;
using namespace Athena;
using namespace Artemis;



#include <QCoreApplication>

/*int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);
    
    return a.exec();
}*/

void* echo(void* t){
    cout<< "marche"<<endl;

}


int main(){
    /*WebCrawler artemis( 20, 1024*1024, 1, 36000, "a.log");
    artemis.setDir("Extras");
    artemis.addUrl("http://fr.openclassrooms.com");
    artemis.crawl();*/

    //HTTPHandler handler;
    //cout<<(handler.get("http://commons.wikimedia.org/wiki/acceuil?uselang=fr")).second<<endl;



    /*pthread_t th1;
    pthread_create( &th1, NULL, echo, NULL);

    pthread_join( th1, NULL);*/

    return 0;
}
