document.addEventListener('DOMContentLoaded', () => {
  const menu = document.getElementById('menu-toggle');
  const navigation = document.getElementById('main-nav');
  if (menu && navigation) {
    menu.addEventListener('click', () => {
      const open = navigation.classList.toggle('open');
      menu.setAttribute('aria-expanded', String(open));
      menu.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
    });
  }

  const individualForm = document.getElementById('individual-form');
  const exampleButton = document.getElementById('load-example');
  if (individualForm && exampleButton) {
    exampleButton.addEventListener('click', () => {
      const values = {
        dni: '12345678', nombre: 'Caso Lima', dependientes: 2,
        ingreso: 4500000, prestamo: 30000000, plazo: 12, credito: 750,
        residencial: 5000000, comerciales: 2000000, lujo: 1000000,
        banco: 15000000, educativo: 'tecnico', autonomo: 'no',
      };
      for (const [key, value] of Object.entries(values)) {
        individualForm.elements.namedItem(key).value = value;
      }
      individualForm.elements.namedItem('dni').focus();
      individualForm.dispatchEvent(new Event('input', { bubbles: true }));
    });

    const submitButton = document.getElementById('evaluate-submit');
    individualForm.addEventListener('submit', () => {
      submitButton.disabled = true;
      submitButton.textContent = 'Evaluando con el modelo…';
    });

    const scenarioVariable = document.getElementById('scenario-variable');
    const scenarioValue = document.getElementById('scenario-value');
    const scenarioButton = document.getElementById('scenario-submit');
    const scenarioFeedback = document.getElementById('scenario-feedback');
    const saveButton = document.getElementById('save-result');
    const downloadLink = document.querySelector('.result-actions a[href]');
    if (scenarioVariable && scenarioValue && scenarioButton) {
      const limits = {
        prestamo: { min: 1000, max: 1000000000 },
        plazo: { min: 1, max: 20 },
        credito: { min: 0, max: 1000 },
      };
      const setScenarioField = () => {
        const field = scenarioVariable.value;
        scenarioValue.min = limits[field].min;
        scenarioValue.max = limits[field].max;
        scenarioValue.value = individualForm.elements.namedItem(field).value;
        scenarioFeedback.hidden = true;
      };
      scenarioVariable.addEventListener('change', setScenarioField);

      // A saved result always belongs to the profile that produced it.
      const original = new FormData(individualForm);
      const originalValues = [...original.entries()]
        .filter(([key]) => key !== 'csrfmiddlewaretoken');
      const markStale = () => {
        const changed = originalValues.some(([key, value]) =>
          individualForm.elements.namedItem(key).value !== value);
        scenarioButton.disabled = changed;
        if (saveButton && saveButton.textContent.includes('Guardar')) saveButton.disabled = changed;
        if (downloadLink) {
          downloadLink.classList.toggle('disabled', changed);
          if (changed) {
            downloadLink.setAttribute('aria-disabled', 'true');
            downloadLink.tabIndex = -1;
          } else {
            downloadLink.removeAttribute('aria-disabled');
            downloadLink.removeAttribute('tabindex');
          }
        }
        let notice = document.getElementById('stale-result');
        if (changed && !notice) {
          notice = document.createElement('p');
          notice.id = 'stale-result';
          notice.className = 'notice';
          notice.setAttribute('role', 'status');
          notice.textContent = 'El perfil cambió. Vuelve a evaluar para comparar o guardar este resultado.';
          document.getElementById('analysis-panel').prepend(notice);
        } else if (!changed && notice) {
          notice.remove();
        }
        if (changed) scenarioFeedback.hidden = true;
      };
      individualForm.addEventListener('input', markStale);
      individualForm.addEventListener('change', markStale);
      individualForm.addEventListener('reset', () => setTimeout(markStale, 0));

      scenarioButton.addEventListener('click', async () => {
        scenarioValue.required = true;
        if (!scenarioValue.reportValidity()) return;
        const data = new FormData(individualForm);
        data.set('variable', scenarioVariable.value);
        data.set('valor', scenarioValue.value);
        scenarioButton.disabled = true;
        scenarioButton.textContent = 'Calculando…';
        scenarioFeedback.hidden = false;
        scenarioFeedback.classList.remove('error');
        scenarioFeedback.textContent = 'Evaluando ambos escenarios con el modelo…';
        try {
          const response = await fetch(scenarioButton.dataset.url, {
            method: 'POST', body: data,
            headers: { 'X-CSRFToken': data.get('csrfmiddlewaretoken') },
          });
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || 'No se pudo comparar el escenario.');
          const format = value => Number(value).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
          const change = result.diferencia > 0 ? `+${format(result.diferencia)}` : format(result.diferencia);
          const title = document.createElement('strong');
          title.textContent = `${format(result.escenario.probabilidad)}% · ${result.escenario.estado}`;
          const baseline = document.createElement('span');
          baseline.textContent = `Caso actual: ${format(result.actual.probabilidad)}% · ${result.actual.estado}`;
          const difference = document.createElement('span');
          difference.textContent = `Cambio: ${change} puntos porcentuales`;
          scenarioFeedback.replaceChildren(baseline, title, difference);
        } catch (error) {
          scenarioFeedback.classList.add('error');
          scenarioFeedback.textContent = error.message || 'No se pudo conectar. Inténtalo de nuevo.';
        } finally {
          scenarioButton.disabled = false;
          scenarioButton.textContent = 'Comparar escenario ↗';
          markStale();
        }
      });
    }
  }

  const saveButton = document.getElementById('save-result');
  if (saveButton) {
    saveButton.addEventListener('click', async () => {
      const feedback = document.getElementById('save-feedback');
      saveButton.disabled = true;
      try {
        const token = document.querySelector('#individual-form [name=csrfmiddlewaretoken]').value;
        const response = await fetch(saveButton.dataset.url, {
          method: 'POST', headers: { 'X-CSRFToken': token },
        });
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
    fileInput.addEventListener('change', () => {
      fileName.textContent = fileInput.files[0]?.name || 'Selecciona un archivo .xlsx';
    });
    for (const eventName of ['dragover', 'dragleave', 'drop']) {
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
        const response = await fetch(batchForm.action, { method: 'POST', body: new FormData(batchForm) });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error((data.errors || ['No se pudo procesar el archivo.']).join(' '));
        document.getElementById('batch-count').textContent = data.resultados.length;
        download.classList.remove('disabled');
        download.removeAttribute('aria-disabled');
        message.textContent = `${data.resultados.length} solicitudes procesadas. Ya puedes descargar el resultado.`;
      } catch (error) {
        message.classList.add('error');
        message.textContent = error.message || 'No se pudo procesar el archivo.';
      } finally {
        button.disabled = false;
      }
    });
  }
});
