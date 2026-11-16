// Interacciones del cuestionario: una pregunta por pantalla y respuesta inmediata.
document.addEventListener('DOMContentLoaded', () => {
  const limites = {
    nombre: 100,
    apellido: 100,
    cedula: 30,
    correo: 190,
    carrera: 120,
    titulo: 180,
    descripcion: 500,
    contenido: 20000,
    imagen: 20,
    enunciado: 2000,
    opcion_a: 500,
    opcion_b: 500,
    opcion_c: 500,
    opcion_d: 500,
    explicacion: 700,
  };
  document.querySelectorAll('form.formulario').forEach((formulario) => {
    formulario.querySelectorAll('input[type="text"], input[type="email"], textarea').forEach((campo) => {
      if (limites[campo.name]) campo.maxLength = limites[campo.name];
      if (campo.name === 'cedula') campo.inputMode = 'text';
      campo.addEventListener('blur', () => { campo.value = campo.value.trim(); });
    });
    formulario.querySelectorAll('input[type="password"][autocomplete="new-password"]').forEach((campo) => {
      campo.maxLength = 72;
    });
    formulario.addEventListener('submit', (evento) => {
      formulario.querySelectorAll('input[type="text"], input[type="email"], textarea').forEach((campo) => {
        campo.value = campo.value.trim();
      });
      if (!formulario.reportValidity()) evento.preventDefault();
    });
  });

  const datos = window.datosCuestionario;
  if (!datos) return;

  const iniciar = document.querySelector('#iniciar-reto');
  const cuestionario = document.querySelector('#cuestionario');
  const preguntaNodo = document.querySelector('#quiz-pregunta');
  const retro = document.querySelector('#quiz-retro');
  const siguiente = document.querySelector('#quiz-siguiente');
  const repetir = document.querySelector('#quiz-repetir');
  const barra = document.querySelector('#quiz-barra');
  const numero = document.querySelector('#quiz-numero');
  const resultado = document.querySelector('#resultado-quiz');
  if (!iniciar || !cuestionario || !preguntaNodo || !retro || !siguiente || !repetir || !barra || !numero || !resultado
      || !Array.isArray(datos.preguntas) || datos.preguntas.length !== 5) return;
  let indice = 0;
  let respuestas = {};

  datos.preguntas.forEach((pregunta) => {
    pregunta.opcionesMezcladas = ['a', 'b', 'c', 'd']
      .map((clave) => ({ clave, texto: pregunta[`opcion_${clave}`] }))
      ;
    for (let posicion = pregunta.opcionesMezcladas.length - 1; posicion > 0; posicion -= 1) {
      const aleatoria = Math.floor(Math.random() * (posicion + 1));
      [pregunta.opcionesMezcladas[posicion], pregunta.opcionesMezcladas[aleatoria]] = [
        pregunta.opcionesMezcladas[aleatoria],
        pregunta.opcionesMezcladas[posicion],
      ];
    }
  });

  function mostrarPregunta() {
    const pregunta = datos.preguntas[indice];
    numero.textContent = `Pregunta ${indice + 1} de ${datos.preguntas.length}`;
    barra.style.width = `${((indice + 1) / datos.preguntas.length) * 100}%`;
    preguntaNodo.innerHTML = `<h2 class="pregunta-texto">${escapar(pregunta.enunciado)}</h2><div class="opciones">${pregunta.opcionesMezcladas.map((opcion, posicion) => `<label class="opcion"><input type="radio" name="respuesta" value="${opcion.clave}"><span><strong>${String.fromCharCode(65 + posicion)}.</strong> ${escapar(opcion.texto)}</span></label>`).join('')}</div>`;
    retro.textContent = '';
    retro.className = 'retroalimentacion';
    siguiente.disabled = true;
    siguiente.textContent = 'Enviar respuesta';
    preguntaNodo.querySelectorAll('input').forEach((opcion) => opcion.addEventListener('change', () => {
      if (respuestas[pregunta.id]) return;
      respuestas[pregunta.id] = opcion.value;
      const acerto = opcion.value === pregunta.respuesta_correcta;
      retro.textContent = `${acerto ? '¡Correcto! Vas muy bien.' : 'Esta vez no. Sigue aprendiendo.'} ${pregunta.explicacion}`;
      retro.classList.add(acerto ? 'correcto' : 'incorrecto');
      preguntaNodo.querySelectorAll('input').forEach((radio) => { radio.disabled = true; });
      siguiente.disabled = false;
      siguiente.textContent = indice === datos.preguntas.length - 1 ? 'Ver resultado' : 'Siguiente pregunta';
    }));
  }

  async function guardarResultado() {
    siguiente.disabled = true;
    siguiente.textContent = 'Guardando…';
    const cuerpo = new URLSearchParams({
      csrf: datos.csrf,
      accion: 'enviar_cuestionario',
      leccion_id: datos.leccion,
      respuestas: JSON.stringify(respuestas),
    });
    try {
      const destino = document.body.dataset.quizUrl || `index.php?pagina=leccion&id=${datos.leccion}`;
      const respuesta = await fetch(destino, { method: 'POST', body: cuerpo });
      const json = await respuesta.json();
      if (!json.ok) throw new Error(json.error || 'No se pudo guardar el resultado.');
      cuestionario.hidden = true;
      resultado.hidden = false;
      const mensaje = json.aciertos === 5 ? '¡Excelente! Dominas este tema.' : json.aciertos >= 3 ? '¡Buen trabajo! Cada intento te ayuda a aprender.' : '¡Terminaste! Repetirlo te ayudará a recordar más.';
      const resultadosUrl = document.body.dataset.resultsUrl || 'index.php?pagina=resultados';
      resultado.innerHTML = `<p class="etiqueta">ACTIVIDAD COMPLETADA</p><h2>${mensaje}</h2><strong>${json.aciertos} / ${json.total}</strong><p>${json.porcentaje}% de respuestas correctas. Tu avance quedó guardado.</p><button class="boton boton-principal" type="button" id="volver-a-intentar">Repetir cuestionario</button> <a class="boton boton-borde" href="${resultadosUrl}">Ver mis resultados</a>`;
      resultado.querySelector('#volver-a-intentar').addEventListener('click', reiniciar);
      iniciar.hidden = false;
    } catch (error) {
      retro.textContent = error.message;
      retro.className = 'retroalimentacion incorrecto';
      siguiente.disabled = false;
      siguiente.textContent = 'Intentar guardar de nuevo';
    }
  }

  function reiniciar() {
    indice = 0;
    respuestas = {};
    resultado.hidden = true;
    cuestionario.hidden = false;
    iniciar.hidden = true;
    mostrarPregunta();
  }

  function escapar(valor) {
    const nodo = document.createElement('span');
    nodo.textContent = valor;
    return nodo.innerHTML;
  }

  iniciar.addEventListener('click', () => { iniciar.hidden = true; cuestionario.hidden = false; mostrarPregunta(); });
  repetir.addEventListener('click', reiniciar);
  siguiente.addEventListener('click', () => {
    if (!respuestas[datos.preguntas[indice].id]) return;
    if (indice < datos.preguntas.length - 1) { indice += 1; mostrarPregunta(); } else guardarResultado();
  });
});