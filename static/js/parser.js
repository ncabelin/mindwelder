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
    var sel, range;
    if (window.getSelection && (sel = window.getSelection()).rangeCount) {
    		console.log(sel)
        range = sel.getRangeAt(0);
        range.collapse(true);
        var span = document.createElement(format);
        span.id = "myId";
        span.appendChild( document.createTextNode(window.getSelection().toString() + '\n') );
        document.execCommand('delete');
        range.insertNode(span);
        console.log('bozo2')

        // Move the caret immediately after the inserted span
        range.setStartAfter(span);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
    }
	});


	$('#editor').wysiwyg();
})