--
-- Table structure for table `hash`
--

DROP TABLE IF EXISTS `hash`;

CREATE TABLE `hash` (
  `id` BIGINT(11) NOT NULL AUTO_INCREMENT,
  `hash` varchar(128), 
  `rType` varchar(2),
  PRIMARY KEY (`id`),
  KEY key_hash (`hash`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;



--
-- Table structure for table `urlrecord`
--

DROP TABLE IF EXISTS `urlrecord`;

CREATE TABLE `urlrecord` (
  `id` BIGINT(11) NOT NULL AUTO_INCREMENT,
  `protocol` varchar(256), 
  `domain` varchar(256),
  `url` text(4096),
  `lastHas512` varchar(128),
  `lastVisited` double,
  PRIMARY KEY (`id`),
  KEY key_url (`url`(50)),
  KEY key_lastSha512 (`lastSha512`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

--
-- Table structure for table `html`
--

DROP TABLE IF EXISTS `html`;

CREATE TABLE `html` (
  `id` BIGINT(11) NOT NULL AUTO_INCREMENT,
  `url` text(4096),
  `domain` varchar(256),
  `relatedRessources` text,
  `sizes` text,
  `contentTypes` text,
  `times` text,
  `has512` varchar(128),
  `lastUpdate` double,
  `chunks` text,
  `revision` INT,
  PRIMARY KEY (`id`),
  KEY key_url (`url`(50))
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
