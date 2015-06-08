var	vaccineChoice = {};
vaccineChoice['A/California/07/2009'] = "2009-09-25";
var vaccineStrains = Object.keys(vaccineChoice);

var restrictTo = {"region":"all"};

var genome_annotation = {'HA1':[[1,1,1], [1,160,327]],
                         'HA2':[[1.2,1.2,1.2], [327,450,580]]}

var regions = ["Africa", "SouthAmerica", "WestAsia", "Oceania", "Europe", "JapanKorea", "NorthAmerica", "SoutheastAsia", "SouthAsia", "China"]
var regionColors = ["#5097BA", "#60AA9E", "#75B681", "#8EBC66", "#AABD52", "#C4B945", "#D9AD3D", "#E59637", "#E67030", "#DF4327"]
