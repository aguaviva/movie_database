var genre_id_list = { 
	28:"Action",
	12:"Adventure",
	16:"Animation",
	35:"Comedy",
	80:"Crime",
	99:"Documentary",
	18:"Drama",    
	10751:"Family",
	14:"Fantasy",
	36:"History",  
	27:"Horror",          
	10402:"Music",           
	9648:"Mystery",         
	10749:"Romance",         
	878:"Science Fiction", 
	10770:"TV Movie",        
	53:"Thriller",        
	10752:"War",
	37:"Western"
}

function myclick(context)
{
	title = $(context).attr('id')

	desc = processed_movie_database[title]

	var genre_ids = desc["genre_ids"];
	var genres = []
	for(var i = 0; i < genre_ids.length; i++)
		genres.push(genre_id_list[genre_ids[i]])
	
	var year = (new Date(desc.date)).getFullYear()
	var res = desc["res"][0]+"x"+desc["res"][1]
	var video_codec = desc["video"]
	var audio_codec = desc["audio"]
	var duration = desc["duration"]
	var aud_langs = desc["aud_langs"]

	$("#poster").attr("src", "./es-ES/thumbs"+desc.thumb)

	$("#title").html(desc.title);
	$("#subtitle").html( year +" / " + duration + "m / " + genres.join(", "));
	$("#overview").html(desc.overview);
	

	tech_details = [res, video_codec, audio_codec]
	if (aud_langs.length>=1 && aud_langs[0].length>0)
		tech_details.push(aud_langs)
	$("#tech_details").html(tech_details.join(" / "));	

	$("#path").html(title);
	$('#myModal').modal('show');
}

var sorting_key = "title";

function mysort(list, key)
{ 
	return list.sort(function(a, b){
		if(a[key] < b[key]){
			return -1;
		}else if(a[key] > b[key]){
			return 1;
		}
		return 0;
	});
}

function populate()
{
	var searchTerm = $('.form-control').val();

	o = []
	for (const [key, value] of Object.entries(processed_movie_database))
	{			
		if (searchTerm!="" && value["title"].toLowerCase().search(searchTerm)==-1 )
			continue;

		value["filename"] = key;
		o.push(value)
	}

	o = mysort(o, sorting_key)

	$('#movie-grid').html("");

	var nowPlayingHTML = '';

	let i = 0
	for (const i in o)
	{					
		var data = o[i];
		var posterPath = "./es-ES/thumbs"+data.thumb;				
		nowPlayingHTML += '<div class="card-deck">';
		nowPlayingHTML += '<div class="card my-2 mx-1" style="width: 15rem; height: 21rem">';
		nowPlayingHTML += '<img loading="lazy" class="card-img-top" id="'+data.filename+'" src="'+posterPath+'" onclick="myclick(this)">';
		nowPlayingHTML += '</div>';
		nowPlayingHTML += '</div>';
	} 
	$('#movie-grid').append(nowPlayingHTML);
}

$(document).ready(function(){
	//reference entire search form
	$('#searchForm').submit(function(event){
		$('#movie-grid').html('');
		event.preventDefault();		
		populate();
	})

	$(function(){
		$(".dropdown-menu a").click(function(){	
		  $(".btn:first-child").text($(this).text());
		  $(".btn:first-child").val($(this).text());	
		  sorting_key = $(this).attr("key")	
		  populate();
	   });	
	});
	

	populate();	
});
