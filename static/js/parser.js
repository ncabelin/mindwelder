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
		// var format = $(this).data('format');
		// var highlight = window.getSelection();
		// if (highlight.toString()) {
		// 	var wrap = '<' + format + '>' + highlight + '</' + format + '>&nbsp;';
		// 	var text = $('#editor').html()
		// 	$('#editor').html(text.concat(wrap));
		// } else {
		// 	var text = $('#editor').html()
		// 	$('#editor').html(text + 'asfasdfasdf');
		// }
    var sel, range;
    if (window.getSelection && (sel = window.getSelection()).rangeCount) {
    		console.log(sel)
        range = sel.getRangeAt(0);
        range.collapse(true);
        var span = document.createElement("span");
        span.id = "myId";
        span.appendChild( document.createTextNode(window.getSelection().toString()+"..") );
        range.insertNode(span);
        if (window.getSelection) {
				  if (window.getSelection().empty) {  // Chrome
				    window.getSelection().empty();
				  } else if (window.getSelection().removeAllRanges) {  // Firefox
				    window.getSelection().removeAllRanges();
				  }
				} else if (document.selection) {  // IE?
				  document.selection.empty();
				}

        // Move the caret immediately after the inserted span
        range.setStartAfter(span);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
    }
	});


	$('#editor').wysiwyg();
})