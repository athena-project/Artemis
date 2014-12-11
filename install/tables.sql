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
-- Table structure for table `text`
--

DROP TABLE IF EXISTS `text`;

CREATE TABLE `text` (
  `id` BIGINT(11) NOT NULL AUTO_INCREMENT,
  `url` text(4096),
  `domain` varchar(256),
  `relatedRessources` text,
  `sizes` text,
  `contentTypes` text,
  `times` text,
  `sha512` text,
  `lastUpdate` double,
  `chunks` text,
  `revision` INT,
  `parent` BIGINT,
  PRIMARY KEY (`id`),
  UNIQUE key_url (`url`(50))
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
  `sha512` text,
  `lastUpdate` double,
  `chunks` text,
  `revision` INT,
  `parent` BIGINT,
  PRIMARY KEY (`id`),
  UNIQUE key_url (`url`(50))
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;