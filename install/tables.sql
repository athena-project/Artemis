--
-- Table structure for table `form`
--

DROP TABLE IF EXISTS `form`;

CREATE TABLE `form` (
  `url_hash` varchar(32),
  `url` text(4096), 
  `body` text, 
  `nature` varchar(2),
  PRIMARY KEY (`url_hash`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
