$(function() {
	// pretty print pre tag
	$('pre').addClass('prettyprint');

	// remove all <br> tags in pre tags
	var pre = document.querySelectorAll('pre');
 	pre.forEach(function(x) {
 		x.innerHTML = x.innerHTML.replace(/<br>/g, '');
 	});

 	// format all tables
 	$('table').addClass('table-bordered').addClass('table');
});