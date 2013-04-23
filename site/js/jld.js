var JldVisualization = function (data, containers) {
	this.data = data;
	this.containers = containers;
	this.defaultArtistName = d3.select(containers.artistname).text();
};
				
JldVisualization.prototype.listeningBehaviorStreamGraph = function () {
	var jld = this;
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
		res[row.artist].push({ x: new Date(fields[0], fields[1]), y: +row.plays, artist: row.artist });
	});
	data = d3.values(res);//.slice(0,45);
	
	var n = data.length, 			// number of layers (artists)
			m = data[0].length,		// number of samples per layer (months)
			stack = d3.layout.stack().offset("wiggle"),
			layers = stack(data);

	var width = 960,
			height = 400;

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
			//.range(["#ada", "#565"]);
			.range(["#dad", "#656"]);
			//.range(["#f0b7a1", "#bf6e4e"]);

	var area = d3.svg.area()
			.x(function(d) { return x(d.x); })
			.y0(function(d) { return y(d.y0); })
			.y1(function(d) { return y(d.y0 + d.y); });

	var svg = d3.select(jld.containers.streamgraph).append("svg")
				.attr("width", width)
				.attr("height", height);

	var stream = svg.selectAll("path")
			.data(layers)
		.enter().append("path")
			.attr("d", area)
			.style("fill", function(d, i) { return color(i); })
			.on("mouseover", function(d, i) {
				d3.select(this)
					.style("cursor", "pointer")
					.style("stroke", "black")
					.style("fill", function() { return d3.rgb(color(i)).darker(); });
			}).on("mousemove", function(d, i) {
				var m = d3.mouse(d3.select("body").node());
				d3.select(jld.containers.streamtooltip)
					.style("left", (m[0] + 15) + "px")
					.style("top", (m[1] + 10) + "px")
					.text(d[0].artist);
			}).on("mouseout", function(d, i) {
				d3.select(this)
					.style("stroke", null)
					.style("fill", function() { return color(i); });
				d3.select(jld.containers.streamtooltip).text("");
			}).on("click", function(d, i) {
				d3.select(jld.containers.artistchart).selectAll("*").remove();
				jld.listeningBehaviorArtistChart(d[0].artist);
			});
};


JldVisualization.prototype.listeningBehaviorArtistChart = function (artist) {
	var jld = this;
	var data = this.data;

	d3.select(jld.containers.artistname).text('"' + artist + '"');

	data = data.filter(function(row) {
		return row.artist == artist;
	});

	var margin = {top: 20, right: 40, bottom: 30, left: 40},
			width = 960 - margin.left - margin.right,
			height = 300 - margin.top - margin.bottom,
			barWidth = Math.floor(width / data.length) - 1;
	
	var formatDate = d3.time.format("%b %Y");
	var parseDate = d3.time.format("%Y-%m").parse;

	var x = d3.time.scale()
			.range([barWidth / 2, width - barWidth / 2]);

	var y = d3.scale.linear()
			.range([height, 0]);

	var xAxis = d3.svg.axis()
			.scale(x)
			.ticks(d3.time.months, 4)
			.tickFormat(d3.time.format("%b %Y"))
			.orient("bottom");

	var yAxis = d3.svg.axis()
			.scale(y)
			.orient("left");

	var svg = d3.select(jld.containers.artistchart).append("svg")
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
			.attr("x", function(d) { return x(d.month) - barWidth/2; })
			.attr("width", barWidth)
			.attr("y", function(d) { return y(d.plays); })
			.attr("height", function(d) { return height - y(d.plays); })
			.on("mouseover", function(d, i) {
				d3.select(this)
					.style("cursor", "pointer")
					.style("stroke", "black")
					.style("fill", function() { return d3.rgb(d3.select(this).style("fill")).darker(); });
				d3.select(jld.containers.artisttooltip)
					.style("display", "block");
			}).on("mousemove", function(d, i) {
				var m = d3.mouse(d3.select("body").node());
				d3.select(jld.containers.artisttooltip)
					.style("left", (m[0] + 15) + "px")
					.style("top", (m[1] + 10) + "px")
					.text(formatDate(d.month) + ": " + d.plays);
			}).on("mouseout", function(d, i) {
				d3.select(this)
					.style("stroke", null)
					.style("fill", function() { return d3.rgb(d3.select(this).style("fill")).brighter(); });
				d3.select(jld.containers.artisttooltip)
					.style("display", "none")
					.text("");
			});
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

JldVisualization.prototype.clear = function() {
	for (var key in this.containers) {
		d3.select(this.containers[key]).selectAll("*").remove();
	}

	d3.select(this.containers.artistname).text(this.defaultArtistName);
};
