var	vaccineChoice = {};
vaccineChoice['B/Beijing/184/93'] = "1998-11-01";
vaccineChoice['B/Sichuan/379/99'] = "2001-09-25";
vaccineChoice['B/Shanghai/361/2002'] = "2004-09-25";
vaccineChoice['B/Florida/4/2006'] = "2008-09-25";
vaccineChoice['B/Wisconsin/01/2010'] = "2012-02-25";
vaccineChoice['B/Massachusetts/02/2012'] = "2013-02-25";
vaccineChoice['B/PHUKET/3073/2013'] = "2014-09-25";
var vaccineStrains = Object.keys(vaccineChoice);

var restrictTo = {"region":"all"};

var genome_annotation = {'HA1':[[1,1,1], [1,160,346]],
                         'HA2':[[1.2,1.2,1.2], [346,450,600]]}

var regions = ["Africa", "SouthAmerica", "WestAsia", "Oceania", "Europe", "JapanKorea", "NorthAmerica", "SoutheastAsia", "SouthAsia", "China"]
var regionColors = ["#5097BA", "#60AA9E", "#75B681", "#8EBC66", "#AABD52", "#C4B945", "#D9AD3D", "#E59637", "#E67030", "#DF4327"]
