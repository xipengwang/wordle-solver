var WORDLE_LENGTH = 5;
var current_wordle_word = null;

window.onload = function() {
  var wordle_word = $('#wordle_word').children();
  for (let i = 0; i < wordle_word.length; i++) {
    wordle_word[i].innerHTML = "";
  }

}

$(document).ready(function() {

  $('#show_wordle_word').on("change", function() {
    // console.log(this.checked)
    var wordle_word = $('#wordle_word').children();
    for (let i = 0; i < wordle_word.length; i++) {
      if(this.checked && current_wordle_word != null)
        wordle_word[i].innerHTML = current_wordle_word[i];
      else
        wordle_word[i].innerHTML = "";
    }
  });

  $("#datepicker").on("change", function(){
    var start_date = new Date("2021-06-19");
    var current_date = new Date($(this).val());
    var diff = current_date.setHours(0, 0, 0, 0) - start_date.setHours(0, 0, 0, 0);
    var idx = Math.round(diff / 864e5) % words.length;
    current_wordle_word = words[idx]
    console.log(current_wordle_word)
    var wordle_word = $('#wordle_word').children();
    for (let i = 0; i < current_wordle_word.length; i++) {
      if($('#show_wordle_word').is(':checked')) {
        wordle_word[i].innerHTML = current_wordle_word[i];
      }
      else
        wordle_word[i].innerHTML = "";
    }
  });


  $("#helpbutton").on("click", function() {
    console.log("Help!!!")
    $(".custom-model-main").addClass('model-open');
  });
  $(".close-btn, .bg-overlay").click(function(){
    $(".custom-model-main").removeClass('model-open');
  });
});
