var	vaccineChoice = {};
vaccineChoice['B/Shangdong/7/97'] = "1999-09-25";
vaccineChoice['B/HongKong/330/2001'] = "2002-09-25";
vaccineChoice['B/Malaysia/2506/2004'] = "2006-09-25";
vaccineChoice['B/Brisbane/60/2008'] = "2009-09-25";
var vaccineStrains = Object.keys(vaccineChoice);

var restrictTo = {"region":"all"};

var genome_annotation = {'HA1':[[1,1,1], [1,160,346]],
                         'HA2':[[1.2,1.2,1.2], [346,450,600]]}

var regions = ["Africa", "SouthAmerica", "WestAsia", "Oceania", "Europe", "JapanKorea", "NorthAmerica", "SoutheastAsia", "SouthAsia", "China"]
var regionColors = ["#5097BA", "#60AA9E", "#75B681", "#8EBC66", "#AABD52", "#C4B945", "#D9AD3D", "#E59637", "#E67030", "#DF4327"]
