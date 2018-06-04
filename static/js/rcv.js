$(document).ready(function() {
	console.log("document ready");
	var socket = io.connect('http://' + document.domain + ':' + location.port + '/all');
	
	var words = [{text: "one", weight: 117},
		{text: "more", weight: 156},
		{text: "tweet", weight: 91},
		{text: "second", weight: 13},
		{text: "twit", weight: 26},
		{text: "twitting", weight: 13},
		{text: "new", weight: 91},
		{text: "nice", weight: 26},
		{text: "test", weight: 26},
		{text: "thats", weight: 26},
		{text: "just", weight: 39},
		{text: "fine", weight: 52},
		{text: "tweets", weight: 52},
		{text: "try", weight: 13},
		{text: "to", weight: 221},
		{text: "be", weight: 169},
		{text: "happy", weight: 26},
		{text: "era", weight: 13},
		{text: "diffuse", weight: 13},
		{text: "trending", weight: 13},
		{text: "topic", weight: 13},
		{text: "keep", weight: 26},
		{text: "on", weight: 104},
		{text: "tweeting", weight: 52},
		{text: "yes", weight: 26},
		{text: "here", weight: 13},
		{text: "lets", weight: 13},
		{text: "tttwwwww", weight: 26},
		{text: "the", weight: 377},
		{text: "app", weight: 91},
		{text: "is", weight: 130},
		{text: "up", weight: 52},
		{text: "and", weight: 117},
		{text: "running", weight: 26},
		{text: "guys", weight: 65},
		{text: "!", weight: 221},
		{text: "download", weight: 78},
		{text: "use", weight: 26},
		{text: "referral", weight: 26},
		{text: "code", weight: 26},
		{text: "you", weight: 169},
		{text: "get", weight: 91},
		{text: "during", weight: 26},
		{text: "your", weight: 117},
		{text: "registration", weight: 26},
		{text: "f", weight: 26},
		{text: "muh", weight: 6}]
	
	var data_sentiment = [{'sentiment':'positive','percentage':33.33},
                              {'sentiment':'negative','percentage':33.33},
                              {'sentiment':'neutral','percentage':33.33}]
							  
							  
	var data_geo = [{'kuala lumpur, malaysia':'','count':1},
					{'kepong, malaysia':'','count':1},
					{'sentul, malaysia':'','count':1},
					{'shah alam, malaysia':'','count':1},
					{'cyberjaya, malaysia':'','count':1},
					{'putrajaya, malaysia':'','count':1},
					{'sri petaling, malaysia':'','count':1},
					{'little india, malaysia':'','count':1},
					{'TM Reserch and Development,cyberjaya, malaysia':'','count':1},
					{'Masjid Jamek, malaysia':'','count':1},]
	
	var ping_pong_times = [];
    var start_time;
    window.setInterval(function() {
        start_time = (new Date).getTime();
        socket.emit('my_ping');
    }, 1000);
	
	var ping_status = document.getElementById("speed");
	var status_message = document.getElementById("status_message");
	
    socket.on('my_pong', function() {
                var latency = (new Date).getTime() - start_time;
                ping_pong_times.push(latency);
                ping_pong_times = ping_pong_times.slice(-30); // keep last 30 samples
                var sum = 0;
                for (var i = 0; i < ping_pong_times.length; i++)
                    sum += ping_pong_times[i];
                ping_status.innerHTML = Math.round(10 * sum / ping_pong_times.length) / 10 + ' ms';
    });
	
	socket.on('conn_response', function(msg) {
		status_message.innerHTML = msg.data;	
    });
	
	socket.on('search_request_received', function(msg) {
		status_message.innerHTML = msg.data;	
    });
	
	socket.on('rate_limit', function(msg) {
		status_message.innerHTML = ' Limit: ' + msg.limit + ' Remaining: ' + msg.remaining + ' Next Reset: ' +
									msg.rst_time + ' Page Count: ' + msg.page_count;	
    });
	
	
	socket.on('simple_cnt', function(msg) {
        document.getElementById("post-count").innerHTML = msg.count;
    });	
	
	socket.on('total_tweets', function(msg) {
		document.getElementById("twit-count").innerHTML = msg.data;		
    });
	
	socket.on('st_msg', function(msg) {
		status_message.innerHTML = msg.text;		
    });
	
    
	
	socket.on('tweet_locations', function(msg) {
        data_geo = JSON.parse(msg);
		drawEmptyMap();
		drawPointsOnMap();
    });	
	
	
	$("#search-button").click(function(){
		socket.emit('search', { 'search_word': document.getElementById("searchbox").value });
    });
	
	$("#stop-button").click(function(){
		socket.emit('stop_request');
    });
	
	var ping_data = null;

	socket.on('recent_tweets', function(msg) {
		console.log('recent tweets received !!');
		var twt_container = document.getElementById("recent-tweets")
		
		obj_array = JSON.parse(msg);
		var mediaData = '';
		for(var i=0;i<obj_array.length;i++){
			obj = obj_array[i]
			mediaData += '<li class="media">';
			mediaData += '<div class="media-left">';
			mediaData += '<a href=';
			mediaData += '"https://www.twitter.com/' + obj.user_screen_name + '">';
			mediaData += '<img class="media-object" src="' + obj.user_profile_image + '"alt="...">';
			mediaData += '</a>';
			mediaData += '</div>';
			mediaData += '<div class="media-body">';
			mediaData += '<h4 class="media-heading">' +  obj.user_name      +    '</h4>';
			mediaData += obj.text;
			mediaData += '</div>';
			mediaData += '</li>';
		}
		twt_container.innerHTML = mediaData;
		
    });
	
	socket.on('top_users', function(msg) {
		console.log('top users received');
		var twt_container1 = document.getElementById("influencers")
		
		obj_array = JSON.parse(msg);
		var mediaData = '';
		for(var i=0;i<obj_array.length;i++){
			obj = obj_array[i]

			mediaData += '<li class="media">';
			mediaData += '<div class="media-left">';
			mediaData += '<a href=';
			mediaData += '"https://www.twitter.com/' + obj.user_screen_name + '">';
			mediaData += '<img class="media-object" src="' + obj.user_profile_image + '"alt="...">';
			mediaData += '</a>';
			mediaData += '</div>';
			mediaData += '<div class="media-body">';
			mediaData += '<h4 class="media-heading">' +  obj.user_name      +    '</h4>';
			mediaData += obj.user_location + '  (' +obj.user_followers_count + ')';
			mediaData += '</div>';
			mediaData += '</li>';
		}

		twt_container1.innerHTML = mediaData;
		
    });
	
	socket.on('sentiments', function(msg) {
		
		console.log('sentiment received !');
		console.log(msg)
		var sdata = new google.visualization.DataTable();
		sdata.addColumn('string', 'sentiment');
		sdata.addColumn('number', 'percentage');
		
		data_sentiment = JSON.parse(msg);
		
		data_sentiment.forEach(function(row){
			sdata.addRow([row.sentiment,row.percentage]);
		});
	
		
		var pi_options = {
          is3D: true,
		  chartArea:{left:20,top:10,width:'100%',height:'80%'}
        };
		
		var chart = new google.visualization.PieChart(document.getElementById('sentiment'));
		chart.draw(sdata, pi_options);
		
    });
	
	socket.on('word_cloud', function(msg) {
		console.log('word cloud received !!');
		words = JSON.parse(msg)
        $('#wordcloud').jQCloud(words,{height:400,
												 //shape:'rectangular',
												 colors:['#d9534f','#f0ad4e','#5cb85c','#337ab7',
														 '#da6360','#f0b460','#6ab86a','#4181b8']})
    });
			
    socket.io.on('disconnect', function() {
		// handle server error here
		console.log('some error');
		conn_status.innerHTML = Math.round(10 * sum / ping_pong_times.length) / 10;
		conn_status.style.color = "green";
		conn_status.classList.toggle('fa-link');
    });
	
	
/* 	$('#wordcloud').jQCloud(words,{width:500,height:350,
								   center: { x: 0.6, y: 0.5 },
								   colors:['#d9534f','#f0ad4e','#5cb85c','#337ab7',
								           '#da6360','#f0b460','#6ab86a','#4181b8']}) */
	
	google.charts.load('current', {'packages':['geochart','gauge','corechart','map'],'mapsApiKey': 'AIzaSyAeKsa_dnhnQG9F-Yz6BuvK8Aac9wRWigg'});
	
	var map_options = {
			mapType: 'styledMap',
			showTooltip: true,
			showInfoWindow: true,
			useMapTypeControl: true,
			maps: {
			  // Your custom mapTypeId holding custom map styles.
			  styledMap: {
				name: 'Styled Map', // This name will be displayed in the map type control.
				styles: [
				  {featureType: 'poi.attraction',
				   stylers: [{color: '#fce8b2'}]
				  },
				  {featureType: 'road.highway',
				   stylers: [{hue: '#0277bd'}, {saturation: -50}]
				  },
				  {featureType: 'road.highway',
				   elementType: 'labels.icon',
				   stylers: [{hue: '#000'}, {saturation: 100}, {lightness: 50}]
				  },
				  {featureType: 'landscape',
				   stylers: [{hue: '#259b24'}, {saturation: 10}, {lightness: -22}]
				  }
			]}}
		  };
		  
	var map_obj = null;
	
	function drawEmptyMap(){
		  map_obj = new google.visualization.Map(document.getElementById('mapid'));
	}
	
	function drawPointsOnMap() {
		var gdata = new google.visualization.DataTable();
		gdata.addColumn('string', 'address');
		gdata.addColumn('number', 'count');	

		data_geo.forEach(function(row){
			gdata.addRow([row.address,row.count]);
		});
		
		if(map_obj != null){
			map_obj.draw(gdata, map_options);
		}else{
			alert('Error: No map object found');
		}
	}
	
});