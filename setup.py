from distutils.core import setup
import os

setup(name="athena-artemis",
        version="3.4.9.dev1",
        description="a scalable, decentralized and fault-tolerant web crawler",
        author="Laurent Prosperi",
        author_email="laurent.prosperi@ens-cachan.fr",
        url="https://github.com/athena-project/Artemis",
        platforms=["linux"],
        license="GPL V2",
        download_url="https://pypi.python.org/pypi/athena-artemis",
        classifiers=[
            'Development Status :: 3 - Alpha',  #https://pypi.python.org/pypi?%3Aaction=list_classifiers

            'Intended Audience :: Developers',
            'Intended Audience :: Information Technology',
            'Intended Audience :: Science/Research',
            'Topic :: Multimedia :: Graphics :: Viewers',

            'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',

            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6'
        ],
        package_dir = {"artemis": "src", "artemis.tests":"tests"},
        scripts = ['master.py', 'slave.py', 'monitor.py', 'admin.py', 'slave.py'],
        packages=["artemis", "artemis.accreditation", "artemis.db", 
                  "artemis.extractors", "artemis.handlers", "artemis.network", "artemis.tests"],
        requires=["transmissionrpc", "stem", "lxml", "pycurl"],
        data_files=[
            ("conf/artemis", [ os.path.join("conf", k) for k in os.listdir("conf") ]),
            ("certs/artemis", [ os.path.join("certs", k) for k in os.listdir("certs") ]),
            ("conf/artemis", ["accreditation.sql"] ),
        ]
    )


