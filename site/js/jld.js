var JldVisualization = function (monthlyData, weeklyData, containers) {
	this.weekdays = [ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ];

	this.data = monthlyData;
	this.weeklyData = weeklyData;
	this.containers = containers;
	this.defaultArtistName = d3.select(containers.artistmonthlyname).text();
	
	this.setMonthlyData(monthlyData);
	this.setWeeklyData(weeklyData);
};

JldVisualization.prototype.setMonthlyData = function(data) {
	this.data = data;
	
	if (data == null) return;

	var parseDate = d3.time.format("%Y-%m").parse;
	this.data.forEach(function(row) {
		row.month = parseDate(row.month);
		row.plays = +row.plays;
	});
};

JldVisualization.prototype.setWeeklyData = function(data) {
	var jld = this;

	jld.weeklyData = data;
	
	if (data == null) return;

	jld.weeklyData.forEach(function(row) {
		row.weekday = jld.weekdays[+row.weekday];
		row.plays = +row.plays;
	});
};

JldVisualization.prototype.makeMonthlyArtistSelector = function() {
	var jld = this;

	$(this.containers.artistmonthlyname).html("");
	$(this.containers.artistmonthlyname)
		.append($("<select>")
			.attr("id", "monthly-artist-select")
			.on("change", function() {
				d3.select(jld.containers.artistmonthlychart).selectAll("*").remove();
				jld.listeningBehaviorMonthlyArtistChart($(this).val());
			}));

	var addedArtists = [];
	for (var idx in this.data) {
		if (addedArtists.indexOf(this.data[idx].artist) != -1) continue;
		addedArtists.push(this.data[idx].artist);
		var $opt = $("<option>")
			.val(this.data[idx].artist)
			.text(this.data[idx].artist);
		$("#monthly-artist-select").append($opt);
	}
};
				
JldVisualization.prototype.makeWeeklyArtistSelector = function() {
	var jld = this;

	$(this.containers.artistweeklyname).html("");
	$(this.containers.artistweeklyname)
		.append($("<select>")
			.attr("id", "weekly-artist-select")
			.on("change", function() {
				d3.select(jld.containers.artistweeklychart).selectAll("*").remove();
				jld.listeningBehaviorWeeklyArtistChart($(this).val());
			}));

	var addedArtists = [];
	for (var idx in this.weeklyData) {
		if (addedArtists.indexOf(this.weeklyData[idx].artist) != -1) continue;
		addedArtists.push(this.weeklyData[idx].artist);
		var $opt = $("<option>")
			.val(this.weeklyData[idx].artist)
			.text(this.weeklyData[idx].artist);
		$("#weekly-artist-select").append($opt);
	}
};
				
JldVisualization.prototype.listeningBehaviorStreamGraph = function () {
	var jld = this;

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

	var dataPerArtist = {};
	var data = this.data.forEach(function(row) {
		if (dataPerArtist[row.artist] == undefined) dataPerArtist[row.artist] = [];
		dataPerArtist[row.artist].push({ x: row.month, y: row.plays, artist: row.artist });
	});
	data = d3.values(dataPerArtist);
	
	var dataPerMonthYear = {};
	this.data.forEach(function(row) {
		var monthYear = d3.time.format("%b %Y")(row.month);
		if (dataPerMonthYear[monthYear] == undefined) dataPerMonthYear[monthYear] = [];
		if (row.plays > 0) dataPerMonthYear[monthYear].push(row.artist);
	});

	var n = data.length, 			// number of layers (artists)
			m = data[0].length,		// number of samples per layer (months)
			stack = d3.layout.stack().offset("silhouette"),
			layers = stack(data);

	/*var width = 960,
			height = 400;*/
	var margin = {top: 30, right: 40, bottom: 20, left: 40},
			width = 960 - margin.left - margin.right,
			height = 400 - margin.top - margin.bottom,
			barWidth = Math.floor(width / data.length) - 1;

	var minX = d3.min(layers, function(layer) { return d3.min(layer, function(e) { return e.x; }); }),
			maxX = d3.max(layers, function(layer) { return d3.max(layer, function(e) { return e.x; }); });

	var x = d3.time.scale()
			.domain([minX, maxX])
			.range([0, width]);

	var y = d3.scale.linear()
			.domain([0, d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); })])
			.range([height, 0]);

	var xAxis = d3.svg.axis()
			.scale(x)
			.ticks(d3.time.months, 4)
			.tickFormat(d3.time.format("%b %Y"))
			.orient("bottom");

	var color = d3.scale.linear()
			.domain([0, n-1])
			.range(["#dad", "#656"]);

	var area = d3.svg.area()
			.x(function(d) { return x(d.x); })
			.y0(function(d) { return y(d.y0); })
			.y1(function(d) { return y(d.y0 + d.y); });

	var svg = d3.select(jld.containers.streamgraph).append("svg")
			.attr("width", width + margin.left + margin.right)
			.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");
	
	svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + (-margin.top) + ")")
			.call(xAxis);

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
				d3.select(jld.containers.artistweeklychart).selectAll("*").remove();
				jld.listeningBehaviorWeeklyArtistChart(d[0].artist);
				d3.select(jld.containers.artistmonthlychart).selectAll("*").remove();
				jld.listeningBehaviorMonthlyArtistChart(d[0].artist);
			});

	var vertical = svg.append("g")
		.attr("height", height)
		.style("visibility", "hidden");

	vertical.append("line")
		.attr("x0", 0)
		.attr("x1", 0)
		.attr("y0", 0)
		.attr("y1", height)
		.style("stroke", "darkgray")
		.style("stroke-width", "2px");
	
	var textMonth = vertical.append("text")
		.attr("class", "stream-info")
		.attr("x", "7px")
		.attr("y", "13px")
		.text("NA");

	var textCurrent = vertical.append("text")
		.attr("class", "stream-info")
		.attr("x", "25px")
		.attr("y", height - 35)
		.attr("width", "25px")
		.attr("text-anchor", "end")
		.text("NA");
	
	var textGained = vertical.append("text")
		.attr("class", "stream-info")
		.attr("x", "25px")
		.attr("y", height - 20)
		.attr("width", "25px")
		.attr("text-anchor", "end")
		.attr("fill", "green")
		.text("+NA");

	var textLost = vertical.append("text")
		.attr("class", "stream-info")
		.attr("x", "25px")
		.attr("y", height - 5)
		.attr("width", "25px")
		.attr("text-anchor", "end")
		.attr("fill", "red")
		.text("-NA");

	d3.select(jld.containers.streamgraph)
		.on("mousemove", function() {
			 mousex = d3.mouse(this)[0] - margin.left + 5;
			 vertical.attr("transform", "translate(" + mousex + ", 0)");
			 
			 var selectedDate = x.invert(mousex);
			 var monthYearFormat = d3.time.format("%b %Y");
			 var selectedMonthYear = monthYearFormat(selectedDate);
			 var previousMonthYear = monthYearFormat(new Date(selectedDate).addMonths(-1));

			 var currentArtists = dataPerMonthYear[selectedMonthYear];
			 var previousArtists = dataPerMonthYear[previousMonthYear];

			 if (previousArtists == undefined) {
				 textGained.text("+0");
				 textLost.text("-0");
			 } else {
				 var gainedArtists = currentArtists.filter(function(x) { return previousArtists.indexOf(x) < 0; });
				 var lostArtists = previousArtists.filter(function(x) { return currentArtists.indexOf(x) < 0; });
				 textGained.text("+" + gainedArtists.length);
				 textLost.text("-" + lostArtists.length);
			 }

			 textMonth.text(selectedMonthYear);
			 if (currentArtists != undefined) textCurrent.text(currentArtists.length);
		})
		.on("mouseover", function() {
			vertical.style("visibility", "visible");
			mousex = d3.mouse(this)[0] - margin.left + 5;
			vertical.attr("transform", "translate(" + mousex + ", 0)");
		})
		.on("mouseout", function() {
			vertical.style("visibility", "hidden");
		});
	
};

JldVisualization.prototype.listeningBehaviorWeeklyTopArtistChart = function(artist) {
	var jld = this;

	var topArtist = {};
	for (var idx in jld.weekdays)
		topArtist[jld.weekdays[idx]] = { topArtist: "NA", plays: 0 };

	this.weeklyData.forEach(function(row) {
		if (topArtist[row.weekday].plays < row.plays) {
			topArtist[row.weekday].topArtist = row.artist;
			topArtist[row.weekday].plays = row.plays;
		}
	});

	var data = [];
	for (var weekday in topArtist)
		data.push({
			weekday: weekday,
			artist: topArtist[weekday].topArtist,
			plays: topArtist[weekday].plays
		});

	var margin = {top: 20, right: 40, bottom: 30, left: 50},
			width = 960/2 - margin.left - margin.right,
			height = 300 - margin.top - margin.bottom,
			barWidth = Math.floor(height / data.length) - 1;
	
	var y = d3.scale.ordinal()
			.domain(jld.weekdays)
			.rangeBands([0, height], 0);

	var x = d3.scale.linear()
			.domain([0, d3.max(data, function(d) { return d.plays; })])
			.range([0, width]);

	var xAxis = d3.svg.axis()
			.scale(x)
			.orient("bottom");

	var yAxis = d3.svg.axis()
			.scale(y)
			.ticks(7)
			.orient("left");

	var svg = d3.select(jld.containers.topartistweeklychart).append("svg")
			.attr("width", width + margin.left + margin.right)
			.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	var barContainer = svg.selectAll(".bar-week")
			.data(data)
		.enter().append("g")
			.on("mouseover", function(d, i) {
				d3.select(jld.containers.topartistweeklytooltip)
					.style("display", "block");
			}).on("mousemove", function(d, i) {
				var m = d3.mouse(d3.select("body").node());
				d3.select(jld.containers.topartistweeklytooltip)
					.style("left", (m[0] + 15) + "px")
					.style("top", (m[1] + 10) + "px")
					.text(d.weekday + ": " + d.plays);
			}).on("mouseout", function(d, i) {
				d3.select(jld.containers.topartistweeklytooltip)
					.style("display", "none")
					.text("");
			});

	barContainer.append("rect")
			.attr("class", "bar-week")
			.attr("y", function(d) { return y(d.weekday); })
			.attr("height", barWidth)
			.attr("x", 0)
			.attr("width", function(d) { return x(d.plays); })
			.on("mouseover", function(d, i) {
				d3.select(this)
					.style("stroke", "black")
					.style("fill", function() { return d3.rgb(d3.select(this).style("fill")).darker(); });
			}).on("mouseout", function(d, i) {
				d3.select(this)
					.style("stroke", null)
					.style("fill", function() { return d3.rgb(d3.select(this).style("fill")).brighter(); });
			});

	barContainer.append("text")
		.attr("class", "top-artist-text")
		.attr("x", ".71em")
		.attr("y", function(d) { return y(d.weekday); })
		.attr("dy", "1.71em")
		.text(function(d) { return d.artist == "NA" ? "" : d.artist; });

	svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + height + ")")
			.call(xAxis)
		.append("text")
			.attr("x", width)
			.attr("dy", "-.71em")
			.style("text-anchor", "end")
			.text("Play Count");

	svg.append("g")
			.attr("class", "y axis")
			.call(yAxis);
};

JldVisualization.prototype.listeningBehaviorWeeklyArtistChart = function(artist) {
	var jld = this;

	$(jld.containers.artistweeklyname)
		.find("select option")
		.filter(function() {
			return $(this).val() == artist;
		}).prop("selected", true);

	var data = this.weeklyData.filter(function(row) {
		return row.artist == artist;
	});

	var margin = {top: 20, right: 40, bottom: 30, left: 40},
			width = 960/2 - margin.left - margin.right,
			height = 300 - margin.top - margin.bottom,
			barWidth = Math.floor(width / data.length) - 1;
	
	var x = d3.scale.ordinal()
			.domain(jld.weekdays)
			.rangeBands([0, width], 0);

	var y = d3.scale.linear()
			.domain([0, d3.max(data, function(d) { return d.plays; })])
			.range([height, 0]);

	var xAxis = d3.svg.axis()
			.scale(x)
			.ticks(7)
			.orient("bottom");

	var yAxis = d3.svg.axis()
			.scale(y)
			.orient("left");

	var svg = d3.select(jld.containers.artistweeklychart).append("svg")
			.attr("width", width + margin.left + margin.right)
			.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + height + ")")
			.call(xAxis);

	svg.selectAll(".bar-week")
			.data(data)
		.enter().append("rect")
			.attr("class", "bar-week")
			.attr("x", function(d) { return x(d.weekday); })
			.attr("width", barWidth)
			.attr("y", function(d) { return y(d.plays); })
			.attr("height", function(d) { return height - y(d.plays); })
			.on("mouseover", function(d, i) {
				d3.select(this)
					.style("stroke", "black")
					.style("fill", function() { return d3.rgb(d3.select(this).style("fill")).darker(); });
				d3.select(jld.containers.artistweeklytooltip)
					.style("display", "block");
			}).on("mousemove", function(d, i) {
				var m = d3.mouse(d3.select("body").node());
				d3.select(jld.containers.artistweeklytooltip)
					.style("left", (m[0] + 15) + "px")
					.style("top", (m[1] + 10) + "px")
					.text(d.weekday + ": " + d.plays);
			}).on("mouseout", function(d, i) {
				d3.select(this)
					.style("stroke", null)
					.style("fill", function() { return d3.rgb(d3.select(this).style("fill")).brighter(); });
				d3.select(jld.containers.artistweeklytooltip)
					.style("display", "none")
					.text("");
			});

	svg.append("g")
			.attr("class", "y axis")
			.call(yAxis)
		.append("text")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.text("Play Count");
};


JldVisualization.prototype.listeningBehaviorMonthlyArtistChart = function (artist) {
	var jld = this;

	$(jld.containers.artistmonthlyname)
		.find("select option")
		.filter(function() {
			return $(this).val() == artist;
		}).prop("selected", true);

	var data = this.data.filter(function(row) {
		return row.artist == artist;
	});

	var margin = {top: 20, right: 40, bottom: 30, left: 40},
			width = 960 - margin.left - margin.right,
			height = 300 - margin.top - margin.bottom,
			barWidth = Math.floor(width / data.length) - 1;
	
	var formatDate = d3.time.format("%b %Y");

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

	var svg = d3.select(jld.containers.artistmonthlychart).append("svg")
			.attr("width", width + margin.left + margin.right)
			.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	x.domain(d3.extent(data, function(d) { return d.month; }));
	y.domain([0, d3.max(data, function(d) { return d.plays; })]);

	svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + height + ")")
			.call(xAxis);

	svg.selectAll(".bar-week")
			.data(data)
		.enter().append("rect")
			.attr("class", "bar")
			.attr("x", function(d) { return x(d.month) - barWidth / 2; })
			.attr("width", barWidth)
			.attr("y", function(d) { return y(d.plays); })
			.attr("height", function(d) { return height - y(d.plays); })
			.on("mouseover", function(d, i) {
				d3.select(this)
					.style("stroke", "black")
					.style("fill", function() { return d3.rgb(d3.select(this).style("fill")).darker(); });
				d3.select(jld.containers.artistmonthlytooltip)
					.style("display", "block");
			}).on("mousemove", function(d, i) {
				var m = d3.mouse(d3.select("body").node());
				d3.select(jld.containers.artistmonthlytooltip)
					.style("left", (m[0] + 15) + "px")
					.style("top", (m[1] + 10) + "px")
					.text(formatDate(d.month) + ": " + d.plays);
			}).on("mouseout", function(d, i) {
				d3.select(this)
					.style("stroke", null)
					.style("fill", function() { return d3.rgb(d3.select(this).style("fill")).brighter(); });
				d3.select(jld.containers.artistmonthlytooltip)
					.style("display", "none")
					.text("");
			});

	svg.append("g")
			.attr("class", "y axis")
			.call(yAxis)
		.append("text")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.text("Play Count");
};

JldVisualization.prototype.mostFrequentArtist = function(data) {
	frequency = {};
	data.forEach(function(row) {
		if (frequency[row.artist] == undefined)
			frequency[row.artist] = 0;
		if (row.plays > 0)
			frequency[row.artist]++;
	});
	return d3.max(d3.entries(frequency), function(e) { return e.key; });
};

JldVisualization.prototype.clear = function() {
	for (var key in this.containers) {
		d3.select(this.containers[key]).selectAll("*").remove();
	}

	d3.select(this.containers.artistmonthlyname).text(this.defaultArtistName);
	d3.select(this.containers.artistweeklyname).text(this.defaultArtistName);
};
