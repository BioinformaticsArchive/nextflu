var	vaccineChoice = {};
vaccineChoice['A/Fujian/411/2002'] = "2003-09-25";
vaccineChoice['A/California/7/2004'] = "2005-02-21";
vaccineChoice['A/Wisconsin/67/2005'] = "2006-02-21";
vaccineChoice['A/Brisbane/10/2007'] = "2007-09-25";
vaccineChoice['A/Perth/16/2009'] = "2009-09-25";
vaccineChoice['A/Victoria/361/2011'] = "2012-02-21";
vaccineChoice['A/Texas/50/2012'] = "2013-09-25";
vaccineChoice['A/Switzerland/9715293/2013'] = "2014-09-25";
var vaccineStrains = Object.keys(vaccineChoice);

var restrictTo = {"region":"all"};

var genome_annotation = {'HA1':[[1,1,1], [1,160,329]],
						 'HA2':[[1.2,1.2,1.2], [329,450,580]]}

var regions = ["Africa", "SouthAmerica", "WestAsia", "Oceania", "Europe", "JapanKorea", "NorthAmerica", "SoutheastAsia", "SouthAsia", "China"]
var regionColors = ["#5097BA", "#60AA9E", "#75B681", "#8EBC66", "#AABD52", "#C4B945", "#D9AD3D", "#E59637", "#E67030", "#DF4327"]
