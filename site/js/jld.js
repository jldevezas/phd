var JldVisualization = function (data) {
	this.data = data;
};
				
JldVisualization.prototype.listeningBehaviorStreamGraph = function (containerId) {
	var data = this.data;
	/*var data = [
		{month:"2012-01", plays:10, artist:"a1"},
		{month:"2012-02", plays:30, artist:"a1"},
		{month:"2012-03", plays: 0, artist:"a1"},
		{month:"2012-04", plays:20, artist:"a1"},

		{month:"2012-01", plays:30, artist:"a2"},
		{month:"2012-02", plays:50, artist:"a2"},
		{month:"2012-03", plays:10, artist:"a2"},
		{month:"2012-04", plays: 0, artist:"a2"},

		{month:"2012-01", plays:30, artist:"a3"},
		{month:"2012-02", plays:20, artist:"a3"},
		{month:"2012-03", plays:10, artist:"a3"},
		{month:"2012-04", plays:30, artist:"a3"}
	];*/

	var res = {};
	data = data.forEach(function(row) {
		var fields = row.month.split('-');
		if (res[row.artist] == undefined) res[row.artist] = [];
		res[row.artist].push({ x: new Date(fields[0], fields[1]), y: +row.plays, z: row.artist });
	});
	data = d3.values(res);//.slice(0,70);
	
	var n = data.length, 			// number of layers (artists)
			m = data[0].length,		// number of samples per layer (months)
			stack = d3.layout.stack().offset("wiggle"),
			layers = stack(data);

	var width = 960,
			height = 500;

	var minX = d3.min(layers, function(layer) { return d3.min(layer, function(e) { return e.x; }); }),
			maxX = d3.max(layers, function(layer) { return d3.max(layer, function(e) { return e.x; }); });

	var x = d3.time.scale()
			.domain([minX, maxX])
			.range([0, width]);

	var y = d3.scale.linear()
			.domain([0, d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); })])
			.range([height, 0]);

	var color = d3.scale.linear()
			.domain([0, n-1])
			//.range(["#aad", "#556"]);
			.range(["#ada", "#565"]);
			//.range(["#dad", "#656"]);
			//.range(["#f0b7a1", "#bf6e4e"]);

	var area = d3.svg.area()
			.x(function(d) { return x(d.x); })
			.y0(function(d) { return y(d.y0); })
			.y1(function(d) { return y(d.y0 + d.y); });

	var svg = d3.select(containerId).append("svg")
			.attr("width", width)
			.attr("height", height);

	svg.selectAll("path")
			.data(layers)
		.enter().append("path")
			.attr("d", area)
			.style("fill", function(d, idx) { return color(idx); });
};


JldVisualization.prototype.listeningBehaviorArtistChart = function (containerId, artist) {
	var data = this.data;

	data = data.filter(function(row) {
		return row.artist == artist;
	});

	var margin = {top: 20, right: 40, bottom: 30, left: 40},
			width = 960 - margin.left - margin.right,
			height = 300 - margin.top - margin.bottom,
			barWidth = Math.floor(width / data.length) - 1;
	
	var parseDate = d3.time.format("%Y-%m").parse;

	var x = d3.time.scale()
			.range([barWidth / 2, width - barWidth / 2]);

	var y = d3.scale.linear()
			.range([height, 0]);

	var xAxis = d3.svg.axis()
			.scale(x)
			.tickFormat(d3.time.format("%b %Y"))
			.orient("bottom");

	var yAxis = d3.svg.axis()
			.scale(y)
			.orient("left");

	var svg = d3.select(containerId).append("svg")
			.attr("width", width + margin.left + margin.right)
			.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	data.forEach(function(d) {
		d.month = parseDate(d.month);
		d.plays = +d.plays;
	});

	x.domain(d3.extent(data, function(d) { return d.month; }));
	y.domain([0, d3.max(data, function(d) { return d.plays; })]);

	svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + height + ")")
			.call(xAxis);

	svg.append("g")
			.attr("class", "y axis")
			.call(yAxis)
		.append("text")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.text("Play Count");

	svg.selectAll(".bar")
			.data(data)
		.enter().append("rect")
			.attr("class", "bar")
			.attr("x", function(d) { return x(d.month); })
			.attr("width", barWidth)
			.attr("y", function(d) { return y(d.plays); })
			.attr("height", function(d) { return height - y(d.plays); });
};

JldVisualization.prototype.mostFrequentArtist = function() {
	var data = this.data;

	frequency = {};
	data.forEach(function(row) {
		if (frequency[row.artist] == undefined)
			frequency[row.artist] = 0;
		if (row.plays > 0)
			frequency[row.artist]++;
	});
	return d3.max(d3.entries(frequency), function(e) e.key);
};
