$(document).ready(function() {
	var questions = $('.question'),
			answers = $('.answer');

	$('span').click(function() {
		$(this).toggleClass('answerShow')
	});

	$('#submit').click(function() {
		content = $('#editor').html()
		$('#editForm').append('<textarea name="post_content">' + content + '</textarea>');
		$('#editForm').submit();
		console.log(content);
	});

	$('.btn-format').click(function() {
		var format = $(this).data('format');
		var highlight = window.getSelection();
		var wrap = '<' + format + '>' + highlight + '</' + format + '>';
		var text = $('#editor').html()
		$('#editor').html(text.replace(highlight, wrap));
	});

	$('#editor').wysiwyg();
})