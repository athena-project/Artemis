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
		packages=["artemis", "artemis.accreditation", "artemis.db", 
                  "artemis.extractors", "artemis.handlers", "artemis.network", "artemis.tests"],
		requires=["transmissionrpc", "stem", "lxml", "pycurl"],
		data_files=[
		  #("log", os.listdir("log")),
                  ("conf/artemis", [ os.path.join("conf", k) for k in os.listdir("conf") ]),
                  ("certs/artemis", [ os.path.join("certs", k) for k in os.listdir("certs") ]),
                  ("conf/artemis", ["accreditation.sql"] ),
                  #("extras", os.listdir("extras"))
                  #("/etc/init.d", ["init-script"])
                  ]
    )


