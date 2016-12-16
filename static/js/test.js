var test = function(post_id, user_id) {
	var answers = {}, // array of all answers
			db_answers = {},
			correct = [], // array of unique_id's listed as correct
			db_exists = false, // default
			answer = $('span.answer'), // nodeList of answers
			save = $('#save'), // save button
			total = $('#total'),
			score = $('#score'),
			reset = $('#reset');

	var deleteTest = function() {
		$.ajax({
			type: 'POST',
			url: '/deletetest/' + post_id + '/' + user_id,
			data: JSON.stringify([post_id, user_id]),
			contentType: 'application/json; charset=utf-8',
			success: function(result) {
				$('#result').html(result);
				$('#modalBtn').trigger('click');
				setTimeout(function() {
					location.reload();
				}, 3000);
			},
			error: function(result) {
				$('#result').html('Error deleting progress:' + result);
				$('#modalBtn').trigger('click');
				setTimeout(function() {
					location.reload();
				}, 3000);
			}
		});
	};

	answer.each(function(index) {
		var id = 'id_' + index.toString();
		// add an id to each answer
		$(this).attr('id', id);

		// create array of blank answers with val = 0 as default
		var text = $(this).text();
		var val = index.toString() + ',0,' + text;
		answers[id] = ['0', '0', text];
	});

	// initialize scoreboard
	var totalAnswers = Object.keys(answers).length;
	score.text(correct.length);
	total.text(totalAnswers);

	$.ajax({
			url: '/showpost_test/' + post_id + '/json'
		}).done(function(data) {
			var results = data.Answers;
			if (results) {
				var totalDbAnswers = results.length;
				db_exists = true;
				var similar = true;

				// check if db and present tests length are =
				if (totalDbAnswers == totalAnswers) {
					// check each
					results.forEach(function(x) {
						var a = x.answer.split('##').slice(1);
						var db = x.answer.split('##')[0];
						var id = a[0].split(',')[0];
						var val_arr = a[0].split(',').slice(1);
						val_arr.unshift(db);
						db_answers[id] = val_arr;
						// check if current post has the same value as
						// the json served
						if (answers[id][2] !== val_arr[3]) {
							similar = false;
						}
					});
				} else {
					similar = false;
				}
				console.log(similar);
				// change attributes and display previous answers marked correct
				if (similar) {
					$.each(db_answers, function(k, v) {
						if (v[2] == '1') {
							$('#' + k).toggleClass('answerShow');
							answers[k][1] = '1';
							correct.push(k);
							score.text(correct.length);
						}
					});
				} else {
					// delete all prevous database answers
				}
			}
	}).fail(function() {
		$('#result').html('You have started a new Test, click Save Test to save your progress.');
		$('#modalBtn').trigger('click');
		score.text(correct.length);
	});

	answer.click(function() {
		// toggle CSS visibility
		$(this).toggleClass('answerShow');

		// look for id in array 'correct'
		var unique_id = $(this).attr('id');

		var text = $(this).text();
		var index = correct.indexOf(unique_id);
		if (index == -1) {
			correct.push(unique_id);
			answers[unique_id][1] = '1';
		} else {
			correct.splice(index, 1);
			answers[unique_id][1] = '0';
		}
		score.text(correct.length);
	});

	reset.click(function() {
		deleteTest();
	});

	save.click(function() {
		// send POST data
		// 'values' array will hold all saved answers with boolean
		var values = [];
		// default url is for adding a new test
		var url = '/savetest/' + post_id + '/' + user_id;

		if (!db_exists) {
			// no database id's found, this means the data is new
			$.each(answers, function(k, v) {
				values.push('0##' + k + ',' + v.join(','));
			});

		} else {
			// existing database id's, submit different values
			$.each(answers, function(k, v) {
				values.push(db_answers[k][0] + '##' + k + ',' + v.join(','));
			});
			url = '/updatetest/' + post_id + '/' + user_id;
		}
		console.log('This will be saved');
		console.log(values);
		$.ajax({
			url: url,
			type: 'POST',
			data: JSON.stringify(values),
			contentType: 'application/json; charset=utf-8',
			success: function(result) {
				$('#result').html(result);
				$('#modalBtn').trigger('click');
				// setTimeout(function() {
				// 	location.reload();
				// 	$('#result').html(result);
				// 	$('#modalBtn').trigger('click');
				// }, 3000);
			},
			error: function(result) {
				$('#result').html(result);
				$('#modalBtn').trigger('click');
				setTimeout(function() {
					location.reload();
				}, 3000);
			}
		});
	});
};
