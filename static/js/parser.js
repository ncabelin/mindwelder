$(document).ready(function() {
	var questions = $('.question'),
			answers = $('.answer');

	$('span').click(function() {
		console.log(this)
		$(this).toggleClass('answerShow')
	});
})