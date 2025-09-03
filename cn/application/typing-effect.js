  document.addEventListener("DOMContentLoaded", function() {
    var text = document.getElementById('typing-effect').innerText;
    var index = 0;
    document.getElementById('typing-effect').innerText = ''; // Borrar el texto inicial

    function typeWriter() {
      if (index < text.length) {
        document.getElementById('typing-effect').innerText += text.charAt(index);
        index++;
        setTimeout(typeWriter, 100); // Ajusta el tiempo para la velocidad de escritura
      }
    }

    typeWriter();
  });
