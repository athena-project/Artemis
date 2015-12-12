from distutils.core import setup
import os

setup(name="Artemis",
		version="3.0",
		description="",#will come soon
		author="Laurent Prosperi",
		author_email="laurent.prosperi@ens-cachan.fr",
		url="",#will come soon
		platforms="",#will come soon
		license="",#will come soon
		package_dir = {"artemis": "src"},
		packages=["artemis"],
		requires=["transmissionrpc", "stem", "redis", "pymysql", "lxml",
			"amqp", "pycurl"],
		data_files=[("log", os.listdir("log")),
                  ("conf", os.listdir("conf")),
                  ("certs", os.listdir("certs")),
                  ("extras", os.listdir("extras"))
                  #("/etc/init.d", ["init-script"])
                  ]
    )


