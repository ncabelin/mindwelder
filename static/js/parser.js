$(document).ready(function() {
	var questions = $('.question'),
			answers = $('.answer');

	$('span').click(function() {
		console.log(this)
		$(this).toggleClass('answerShow')
	});

	$('#submit').click(function() {
		content = $('#editor').html()
		$('#editForm').append('<textarea name="post_content">' + content + '</textarea>');
		$('#editForm').submit();
		console.log(content);
	});

	$('#answerBtn').click(function() {
		console.log('Fuck you');
		var highlight = window.getSelection();
		var wrap = '<a>' + highlight + '</a>';
		var text = $('#editor').html()
		$('#editor').html(text.replace(highlight, wrap));
	});

	$('#editor').wysiwyg();
})