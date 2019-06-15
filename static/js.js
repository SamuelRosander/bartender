function minus() {
  var drink_size = document.getElementById("drink_size").value;
  if (drink_size > 2) {
    document.getElementById("drink_size").value = (Number(drink_size) - 1);
  }
}
function plus() {
  var drink_size = document.getElementById("drink_size").value;
  if (drink_size < 15) {
    document.getElementById("drink_size").value = (Number(document.getElementById("drink_size").value) + 1);
  }
}
function make_drink(drink) {
  $("#modal-fade").show();
  window.location = "/make_drink/" + drink + "/" + document.getElementById("drink_size").value;
}
