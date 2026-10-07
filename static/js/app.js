document.addEventListener('DOMContentLoaded', () => {
  const menu = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  if (menu && sidebar) {
    menu.addEventListener('click', () => {
      const open = sidebar.classList.toggle('open');
      menu.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', event => {
      if (sidebar.classList.contains('open') && !sidebar.contains(event.target) && event.target !== menu) {
        sidebar.classList.remove('open');
        menu.setAttribute('aria-expanded', 'false');
      }
    });
  }

  const exampleButton = document.getElementById('load-example');
  if (exampleButton) {
    exampleButton.addEventListener('click', () => {
      const values = {dni:'12345678',nombre:'Caso Lima',dependientes:2,ingreso:4500000,prestamo:30000000,plazo:12,credito:750,residencial:5000000,comerciales:2000000,lujo:1000000,banco:15000000,educativo:'tecnico',autonomo:'no'};
      for (const [key, value] of Object.entries(values)) document.getElementById(key).value = value;
    });
  }

  const saveButton = document.getElementById('save-result');
  if (saveButton) {
    saveButton.addEventListener('click', async () => {
      const feedback = document.getElementById('save-feedback');
      saveButton.disabled = true;
      try {
        const token = document.querySelector('#individual-form [name=csrfmiddlewaretoken]').value;
        const response = await fetch(saveButton.dataset.url, {method:'POST',headers:{'X-CSRFToken':token}});
        const data = await response.json();
        feedback.textContent = data.message || 'No se pudo guardar el resultado.';
        if (!response.ok) saveButton.disabled = false;
        else saveButton.textContent = 'Guardado en reportes ✓';
      } catch {
        feedback.textContent = 'No se pudo conectar. Inténtalo de nuevo.';
        saveButton.disabled = false;
      }
    });
  }

  const batchForm = document.getElementById('batch-form');
  if (batchForm) {
    const fileInput = document.getElementById('archivo');
    const fileName = document.getElementById('file-name');
    const zone = document.querySelector('.dropzone');
    fileInput.addEventListener('change', () => { fileName.textContent = fileInput.files[0]?.name || 'Selecciona un archivo .xlsx'; });
    for (const eventName of ['dragover','dragleave','drop']) {
      zone.addEventListener(eventName, event => {
        event.preventDefault();
        zone.classList.toggle('dragging', eventName === 'dragover');
        if (eventName === 'drop' && event.dataTransfer.files.length) {
          fileInput.files = event.dataTransfer.files;
          fileName.textContent = fileInput.files[0].name;
        }
      });
    }
    batchForm.addEventListener('submit', async event => {
      event.preventDefault();
      const message = document.getElementById('batch-message');
      const button = document.getElementById('batch-submit');
      const download = document.getElementById('batch-download');
      message.hidden = false;
      message.classList.remove('error');
      message.textContent = 'Procesando solicitudes…';
      button.disabled = true;
      try {
        const response = await fetch(batchForm.action,{method:'POST',body:new FormData(batchForm)});
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error((data.errors || ['No se pudo procesar el archivo.']).join(' '));
        const count = data.resultados.length;
        document.getElementById('batch-count').textContent = count;
        download.classList.remove('disabled');
        download.removeAttribute('aria-disabled');
        message.textContent = `${count} solicitudes procesadas. Ya puedes descargar el resultado.`;
      } catch (error) {
        message.classList.add('error');
        message.textContent = error.message || 'No se pudo procesar el archivo.';
      } finally { button.disabled = false; }
    });
  }
});
