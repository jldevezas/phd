var JldVisualization = function (userId) {
	this.userId = userId;
};

JldVisualization.prototype.listeningBehavior = function (containerId) {
	var n = 20, // number of layers
			m = 200, // number of samples per layer
			stack = d3.layout.stack().offset("wiggle"),
			layers = stack(d3.range(n).map(function() { return bumpLayer(m); }));

	var width = 960,
			height = 500;

	var x = d3.scale.linear()
			.domain([0, m - 1])
			.range([0, width]);

	var y = d3.scale.linear()
			.domain([0, d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); })])
			.range([height, 0]);

	var color = d3.scale.linear()
			//.range(["#aad", "#556"]);
			.range(["#ada", "#565"]);
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
			.style("fill", function() { return color(Math.random()); });
			
	// Inspired by Lee Byron's test data generator.
	function bumpLayer(n) {
		function bump(a) {
			var x = 1 / (.1 + Math.random()),
					y = 2 * Math.random() - .5,
					z = 10 / (.1 + Math.random());
			for (var i = 0; i < n; i++) {
				var w = (i / n - y) * z;
				a[i] += x * Math.exp(-w * w);
			}
		}

		var a = [], i;
		for (i = 0; i < n; ++i) a[i] = 0;
		for (i = 0; i < 5; ++i) bump(a);
		return a.map(function(d, i) { return {x: i, y: Math.max(0, d)}; });
	}
};
