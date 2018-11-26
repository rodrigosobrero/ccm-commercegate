let app = new Object(this.self);

/**
 * Parámetros de configuración
 */
app.config = {
  api: '/api/v1/api/',
  fullScreenState: false,
  tableSelector: '#table',
}

/**
 * Iniciar tabla (DataTables)
 * @param {array} prm.api
 * @param {array} prm.columns
 * @param {array} prm.searchCols - Opcional
 * @param {array} prm.filters - Opcional
 */
app.iniTable = prm => {
  let table = $(app.config.tableSelector).DataTable({
    ajax: prm.api,
    buttons: [
      { extend: 'excelHtml5', className: 'btn-sm btn-ccm' },
      { extend: 'csvHtml5', className: 'btn-sm btn-ccm' },
      { extend: 'pdfHtml5', className: 'btn-sm btn-ccm' }
    ],
    bLengthChange: false,
    responsive: true,
    autoWidth: true,
    order: prm.order,
    language: {
      url: 'https://cdn.datatables.net/plug-ins/1.10.19/i18n/Spanish.json'
    },
    columns: prm.columns,
    searchCols: prm.searchCols,
    initComplete:
      function () {
        // Aplicar estilo thead-light al thead
        $(table.table().header()).addClass('thead-light');
        
        // Inicializa 'tooltip' y 'popover'
        $('body').tooltip({selector: '[data-toggle="tooltip"]'});
        $('body').popover({selector: '[data-toggle="popover"]'});

        // Inserta botones en el div #table-buttons
        table.buttons().container().appendTo('#table-buttons');
        $('#table-buttons .btn-group').addClass('shadow');

        // Borra input search nuevo e inicializa uno custom
        $('#table_filter').remove();
        $('#search-box').keyup(function () {
          table.search($(this).val()).draw();
        });

        // Inicializa plugin custom para filtro
        if (prm.filters) {
          app.dataTablesPlugin(this, prm.filters);
        }
      },
  });

  // table.on('processing.dt', () => { app.preloader(true) });
  // table.on('init.dt', () => { app.preloader() });
}

/**
 * DataTables custom plugin
 * @param {object} table - Objeto DataTable
 * @param {array} filters - 
 *        [{ filter_type: select (default) | date_range,
 *           column_number: número de columna, 
 *           filter_label: nombre del filtro }]
 */
app.dataTablesPlugin = function (table, filters) {
  if (table && filters) {
    let id = 0;

    filters.forEach(element => {
      element.filter_type = element.filter_type ? element.filter_type : 'select';

      $('.table-toolbar .row').prepend(`<div class="col-auto mr-2" id="table-toolbar-elem-${id}"></div>`);

      if (element.filter_type == 'select') {
        table.api().columns([element.column_number]).every(function () {
          let column = this;
          let select = `<div class="input-group input-group-sm">
                          <div class="input-group-prepend">
                            <label class="input-group-text" for="table-select-filter-${id}">
                              ${element.filter_label}
                            </label>
                          </div>
                          <select class="custom-select form-control form-control-sm" id="table-select-filter-${id}">
                            <option value="">${element.default ? element.default : 'Todos'}</option>
                          </select>
                        </div>`;

          $(select).prependTo('#table-toolbar-elem-' + id);

          $('#table-select-filter-' + id).on('change', function () {
            var val = $.fn.dataTable.util.escapeRegex(
              $(this).val()
            );
    
            column
              .search(val ? '^' + val + '$' : '', true, false)
              .draw();
          });
      
          column.cells('', column[0]).render('display').sort().unique().each(function (d, j) {
            var val = $('<div/>').html(d).text();
            $('#table-select-filter-' + id).append('<option value="' + val + '">' + val + '</option>')
          });
        });
      } else if (element.filter_type == 'date_range') {
        let dateRange = `<div class="input-group input-group-sm">
                            <div class="input-group-prepend">
                              <span class="input-group-text">${element.filter_label}</span>
                            </div>
                            <input type="text" id="table-daterange-filter-${id}" class="form-control" name="daterange" value="" style="min-width:180px">
                         </div>`;
        
        $(dateRange).prependTo('#table-toolbar-elem-' + id);

        $('input[name="daterange"]').daterangepicker({
          opens: 'left',
          applyButtonClasses: 'btn-danger',
          locale: {
            format: 'DD/MM/YYYY',
            applyLabel: 'Filtrar',
            cancelLabel: 'Cancelar',
            applyButtonClasses: 'btn-ccm',
            daysOfWeek: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
            monthNames: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
          }
        });

        $('#table-daterange-filter-' + id).on('apply.daterangepicker', function (ev, picker) {
          startDate = picker.startDate;
          endDate = picker.endDate;
      
          $.fn.dataTable.ext.search.push(
            function (settings, searchData, index, rowData, counter) {
              if (startDate != undefined) {
                columnStringDate = searchData[element.column_number];
                columnDate = moment(columnStringDate, 'DD/MM/YYYY');
      
                if (startDate == '' && columnDate.isBefore(endDate)) {
                  return true
                } else if (endDate == '' && columnDate.isAfter(startDate)) {
                  return true
                } else if (columnDate.isAfter(startDate) && columnDate.isBefore(endDate)) {
                  return true
                } else {
                  return false
                }
              }
            }
          );
      
          table.fnDraw();
        });
      }

      id++;
    });

    // Chequeo si existe algún 'date_range' para inicializar el plugin
    // const checkDateRange = obj => obj.filter_type === 'date_range';

    // if (filters.some(checkDateRange)) {
    //   $('input[name="daterange"]').daterangepicker({
    //     opens: 'left',
    //     locale: {
    //       format: 'DD/MM/YYYY',
    //       applyLabel: 'Filtrar',
    //       cancelLabel: 'Cancelar',
    //       applyButtonClasses: 'btn-ccm',
    //       daysOfWeek: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
    //       monthNames: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    //                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    //     }
    //   });
    // }
  }
}

/**
 * Formateadores
 */
app.renders = {};

app.renders.boolean = prm => {
  if (prm) {
    return 'Si'
  } else {
    return 'No'
  }
}

app.renders.creditCard = prm => {
  if (prm) {
    return `<span class="text-black-50">•••• •••• ••••</span> ${prm}`
  }
}

app.renders.date = prm => {
  if (moment(prm).isValid()) {
    return moment(prm).format('DD/MM/YYYY')
  } else {
    return ''
  }
}

app.renders.usersActions = (data, type, row) => {
  let btn = '';

  if (row.is_active) {
    btn += `<a href="javascript:void(0)" onclick="app.modalUserDesactivate('${row.user_id}')"
            class="btn btn-link btn-sm text-black-50" role="button" 
            data-toggle="tooltip" data-placement="top" title="Expirar">
              <i class="fas fa-user-slash fa-lg"></i>
            </a>`;
  } else {
    btn += `<a href="javascript:void(0)" onclick="app.modalUserActivate('${row.user_id}')"
            class="btn btn-link btn-sm text-black-50" role="button"
            data-toggle="tooltip" data-placement="top" title="Activar">
              <i class="fas fa-user-check fa-lg"></i>
            </a>`;
  }

  if (row.has_recurrence) {
    btn += `<a href="javascript:void(0)" onclick="app.modalUserPayments('${row.user_id}')" 
            class="btn btn-link btn-sm text-black-50" role="button" 
            data-toggle="tooltip" data-placement="top" title="Ver recurrencias">
              <i class="far fa-credit-card fa-lg"></i>
            </a>`;
  }

  return btn
}

app.renders.rePayUserDot = (data, type, row) => {
  let style = 'secondary';

  switch (row.status) {
    case 'CA':
    case 'PE':
      style = 'secondary';
      break;
    case 'AC':
      style = 'success';
      break;
    case 'ER':
    case 'RE':
      style = 'danger';
      break;
  }

  return `<span class="dot bg-${style}"></span>${data}`
}

app.renders.rePayMessage = prm => {
  if (prm) {
    return `<span class="d-inline-block text-truncate" 
              style="max-width: 80px;" 
              data-toggle="tooltip" 
              title="${prm}">
              ${prm}
            </span>`
  } else {
    return ''
  }
}

app.renders.rePayState = prm => {
  let text;
  let style = 'secondary';

  switch (prm) {
    case 'PE':
      text = 'Pendiente';
      break;
    case 'AC':
      text = 'Activo';
      style = 'success';
      break;
    case 'CA':
      text = 'Cancelado';
      break;
    case 'ER':
      text = 'Error';
      style = 'danger';
      break;
    case 'RE':
      text = 'Error en recurrencia';
      style = 'danger';
      break;
  }

  return `<span class="badge badge-${style}">${text}</span>`
}

app.renders.rePayActions = (data, type, row) => {
  let btn = `<a href="javascript:void(0)" 
              onclick="app.modalRePayUser('${row.user}')"
              class="btn btn-link btn-sm text-black-50" 
              role="button" data-toggle="tooltip" 
              data-placement="top" title="Detalle de usuario">
              <i class="fas fa-user fa-lg"></i>
             </a>
             <a href="javascript:void(0)"
              onclick="app.modalRePayDetail('${row.user}')"
              class="btn btn-link btn-sm text-black-50" 
              role="button" data-toggle="tooltip" 
              data-placement="top" title="Historial de pagos">
              <i class="fas fa-history fa-lg"></i>
             </a>`;

  if (row.status == 'AC' || row.status == 'RE') {
    btn += `<a href="javascript:void(0)" 
              onclick="app.modalRePayStop('${row.user}', '${row.user_payment_id}')" 
              class="btn btn-link btn-sm text-black-50" 
              role="button" data-toggle="tooltip" 
              data-placement="top" title="Desactivar recurrencia">
              <i class="fas fa-ban fa-lg"></i>
            </a>`;
  } 
  
  if (row.status == 'RE') {
    btn += `<a href="javascript:void(0)" 
              onclick="app.modalManualPay('${row.user_payment_id}')"
              class="btn btn-link btn-sm text-black-50" 
              role="button" data-toggle="tooltip" 
              data-placement="top" title="Pago manual">
              <i class="far fa-credit-card fa-lg"></i>
            </a>`;
  }

  return btn
}

app.renders.hisPayState = prm => {
  let style = 'secondary';
  let text;

  switch (prm) {
    case 'P':
      text = 'Procesando';
      break;
    case 'W':
      text = 'Esperando respuesta';
      break;
    case 'C':
      text = 'Cancelado';
      break;
    case 'E':
      text = 'Error';
      style = 'danger';
      break;
    case 'A':
      text = 'Aprobado';
      style = 'success';
      break;
    case 'R':
      text = 'Rechazado';
      style = 'warning';
      break;
  }

  return `<span class="badge badge-${style}">${text}</span>`
}

app.renders.hisPayActions = (data, type, row) => {
  let btn = '';
  let rowData = JSON.stringify(row);
  let rowBase64 = window.btoa(rowData);

  btn += `<a href="javascript:void(0)" 
            onclick="app.modalRePayUser('${row.user}')"
            class="btn btn-link btn-sm text-black-50" 
            role="button" data-toggle="tooltip" 
            data-placement="top" title="Detalle de usuario">
            <i class="fas fa-user fa-lg"></i>
          </a>
          <a href="javascript:void(0)" 
            onclick="app.modalHisDetail('${rowBase64}')"
            class="btn btn-link btn-sm text-black-50" 
            role="button" data-toggle="tooltip" 
            data-placement="top" title="Detalle">
            <i class="far fa-eye fa-lg"></i>
          </a>`;

  return btn
}

/**
 * Preloader
 * @param {boolean} prm
 */
app.preloader = prm => {
  if (prm) {
    $('.preloader').fadeIn();
  } else {
    $('.preloader').fadeOut();
  }
}

/**
 * Fullscreen
 * @param {boolean} prm
 */
app.fullScreen = prm => {
  let elem = document.documentElement;
  app.config.fullScreenState = prm;

  function open() {
    if (elem.requestFullscreen) {
      elem.requestFullscreen();
    } else if (elem.mozRequestFullScreen) {
      elem.mozRequestFullScreen();
    } else if (elem.webkitRequestFullscreen) {
      elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
      elem.msRequestFullscreen();
    }
  }

  function close() {
    if (document.exitFullscreen) {
      elem.exitFullscreen();
    } else if (document.mozCancelFullScreen) {
      elem.mozCancelFullScreen();
    } else if (document.webkitCancelFullscreen) {
      elem.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      elem.msExitFullscreen();
    }
  }

  prm ? open() : close();
}

/**
 * Cargador para botón
 * @param {string} prm.selector
 * @param {boolean} prm.loading
 */
app.loadingButton = prm => {
  if (prm.loading) {
    $(prm.selector)
      .addClass('ld-ext-right running')
      .append('<div class="ld ld-ring ld-spin"></div>');
  } else {
    $(prm.selector)
      .addClass('disabled')
      .removeClass('ld-ext-right running')
      .find('div')
      .remove();
  }
}

/**
 * Modal
 * @param {string} prm.class - (Opcional) Clase adicional para el modal
 * @param {string} prm.title - Título del modal
 * @param {string} prm.body - Contenido del modal
 * @param {string} prm.footer - (Opcional) Footer del modal
 * @param {string} prm.id - (Opcional)
 */
app.modal = prm => {
  let id = prm.id ? prm.id : 'modal';

  let modal = `<div class="modal fade" tabindex="-1" role="dialog" id="${id}">
                <div class="modal-dialog ${prm.class ? prm.class : ''}" role="document">
                  <div class="modal-content">
                    <div class="modal-header">
                      <h5 class="modal-title">${prm.title}</h5>
                      <button type="button" class="close" data-dismiss="modal" aria-label="Cerrar">
                        <span aria-hidden="true">&times;</span>
                      </button>
                    </div>
                    <div class="modal-body">${prm.body}</div>
                    ${prm.footer ? `<div class="modal-footer">${prm.footer}</div>` : ''}
                  </div>
                </div>`;

  $('body').append(modal);

  $('#' + id)
    .modal()
    .on('hidden.bs.modal', function () {
      $(this).remove();
    });
}

/**
 * Usuarios - Modal detalle de recurrencias
 * @param {string} prm
 */
app.modalUserPayments = prm => {
  $.ajax({
    url: app.config.api + 'payments/' + prm + '/2',
    method: 'GET'
  }).done((data) => {
    let recurrence = '';

    if (data) {
      recurrence += `<div class="alert alert-secondary shadow-sm">
                      <b>Usuario:</b> ${prm}
                     </div>`;

      data.data.forEach(element => {
        recurrence += `<div class="card shadow-sm mt-3">
                        <div class="card-body">
                          <div class="row">
                            <div class="col-5">
                              <p><b>Estado:</b> ${this.renders.rePayState(element.status)}</p>
                              <p><b>Reintentos:</b> ${element.retries}</p>
                              <p><b>Monto:</b> ${element.amount}</p>
                              <p><b>Moneda:</b> ${element.currency}</p>
                            </div>
                            <div class="col-7">
                              <p><b>Fecha de modificación:</b> ${this.renders.date(element.modification_date)}</p>
                              <p><b>Fecha de pago:</b> ${this.renders.date(element.creation_date)}</p>
                              <p><b>Recurrencia:</b> ${element.recurrence}</p>
                              <p><b>Reintentos:</b> ${element.retries}</p>
                            </div>
                          </div>
                        </div>
                       </div>`;
      });
    } else {
      recurrence += '<p>No hay datos para el usuario seleccionado.</p>'
    }

    app.modal({
      title: 'Pagos recurrentes',
      body: recurrence,
      footer: `${data.records > 2 ? `<a href="/ui/pagos-recurrentes/?usuario=${prm}" 
                                      class="btn btn-sm btn-secondary">Ver más recurrencias</a>` : ''}`
    });
  });
}

/**
 * Usuarios - Modal activar usuario
 * @param {string} prm
 */
app.modalUserActivate = prm => {
  this.modal({
    id: 'userActivate',
    title: 'Activar usuario',
    body: `<div class="alert alert-secondary shadow-sm">
            <b>Usuario:</b> ${prm}
           </div>
           <form id="activate_user" novalidate>
            <div class="form-group">
              <label for="days">Cantidad de días</label>
              <input type="hidden" id="user_id" name="user_id" value="${prm}">
              <input type="number" class="form-control" id="days" name="days" min="1" autofocus required>
              <div class="invalid-feedback">
                Ingrese la cantidad de días que estará activo el usuario.
              </div>
            </div>
           </form>`,
    footer: `<a href="javascript:void(0)" role="button" class="btn btn-sm btn-outline-secondary" data-dismiss="modal">Cerrar</a>
             <a href="javascript:void(0)" role="button" class="btn btn-sm btn-success" id="btnActivateUser">Activar</a>`
  });

  let form = $('#activate_user');

  $('#btnActivateUser').on('click', () => {
    if(form[0].checkValidity()) {
      let data = {
        'user_id': prm,
        'days': $('#days').val()
      }

      $.ajax({
        type: 'POST',
        url: '/ui/activateuser/',
        data: JSON.stringify(data),
        beforeSend: 
          this.loadingButton({
            selector: '#btnActivateUser',
            loading: true 
          })
      }).done(() => {
        alert = '<div class="alert alert-success" role="alert">Usuario activado correctamente.</div>';
        $(app.config.tableSelector).DataTable().ajax.reload();
      }).fail(() => {
        alert = '<div class="alert alert-danger" role="alert">Error al intentar activar el usuario.</div>';
      }).always(() => {
        $('.modal-body').prepend(alert);
        this.loadingButton({
          selector: '#btnActivateUser'
        });
      });
    } else {
      $('#activate_user').addClass('was-validated');
    }
  });
}

/**
 * Usuarios - Modal expirar usuario
 * @param {string} prm
 */
app.modalUserDesactivate = prm => {
  this.modal({
    id: 'userDesactivate',
    title: 'Expirar usuario',
    body: `<p>¿Está seguro que desea expirar al usuario <b>${prm}</b>?</p>`,
    footer: `<a href="javascript:void(0)" role="button" class="btn btn-sm btn-outline-secondary" data-dismiss="modal">Cerrar</a>
             <a href="javascript:void(0)" role="button" class="btn btn-sm btn-danger" id="btnExpireUser">Expirar</a>`
  });

  $('#btnExpireUser').on('click', () => {
    let data = { 'user_id': prm };

    $.ajax({
      type: 'POST',
      url: '/ui/expireuser/',
      data: JSON.stringify(data),
      beforeSend:
        this.loadingButton({
          selector: '#btnExpireUser',
          loading: true 
        })
    }).done(() => {
      alert = '<div class="alert alert-success" role="alert">Usuario expirado correctamente.</div>'
      $(app.config.tableSelector).DataTable().ajax.reload();
    }).fail(() => {
      alert = '<div class="alert alert-danger" role="alert">Error al intentar expirar el usuario.</div>';
    }).always(() => {
      this.loadingButton({
        selector: '#btnExpireUser'
      });
      $('.modal-body').prepend(alert);
    });
  });
}

/**
 * Recurrencias - Modal detener recurrencia
 * @param {string} user - ID del usuario
 * @param {string} id - ID de pago recurrente
 */
app.modalRePayStop = (user, id) => {
  this.modal({
    title: 'Desactivar recurrencia',
    body: `<div class="alert alert-secondary shadow-sm">
            <b>Usuario:</b> ${user}
           </div>
           <form id="desactivate_pay">
            <div class="form-group" novalidate>
              <label for="txtmessage">Mensaje</label>
              <input type="hidden" id="userpayment_id" name="userpayment_id" value="${id}">
              <textarea class="form-control" id="txtmessage" name="txtmessage"></textarea>
              <small id="emailHelp" class="form-text text-muted">Ingrese un mensaje (opcional).</small>
            </div>
           </form>`,
    footer: ` <a href="javascript:void(0)" class="btn btn-sm btn-outline-secondary" data-dismiss="modal">Cerrar</a>
              <a href="javascript:void(0)" class="btn btn-sm btn-danger" id="btnDesactivatePay">Desactivar</a>`
  });

  let form = $('#desactivate_pay');

  $('#btnDesactivatePay').on('click', () => {
      let data = {
        'userpayment_id': id,
        'txtmessage': $('#txtmessage').val()
      }

      $.ajax({
        type: 'POST',
        url: '/ui/deleteuserpayment/',
        data: JSON.stringify(data),
        beforeSend:
          this.loadingButton({
            selector: '#btnDesactivatePay',
            loading: true 
          })
      }).done(() => {
        alert = '<div class="alert alert-success" role="alert">Recurrencia desactivada correctamente.</div>';
        $(app.config.tableSelector).DataTable().ajax.reload();
      }).fail(() => {
        alert = '<div class="alert alert-danger" role="alert">Error al intentar desactivar la concurrencia.</div>';
      }).always(() => {
        $('.modal-body').prepend(alert);
        this.loadingButton({
          selector: '#btnDesactivatePay',
          loading: true 
        });
      });
  })

}

/**
 * Recurrencias - Modal detalle de usuario
 * @param {string} prm - ID del usuario
 */
app.modalRePayUser = prm => {
  $.ajax({
    url: app.config.api + 'users/' + prm,
    method: 'GET'
  }).done((data) => {
    let message;
    let footer;

    if (data.value) {
        message = `<div class="card shadow-sm">
                    <div class="card-body">
                      <div class="row">
                        <div class="col">
                          <p><b>ID:</b> ${prm}</p>
                          <p><b>Email:</b> ${data.value.email}</p>
                          <p><b>País:</b> ${data.value.country}</p>
                          <p><b>Fecha de creación:</b> ${this.renders.date(data.value.creation_date)}</p>
                          <p><b>Tarjeta de crédito:</b> ${this.renders.creditCard(data.value.card)}</p>
                        </div>
                      </div>
                    </div>
                   </div>`;

        if (data.value.is_active) {
          footer = `<a href="javascript:void(0)" 
                      class="btn btn-sm btn-danger" 
                      onclick="app.modalUserDesactivate('${prm}')" 
                      data-toggle="modal" data-dismiss="modal">
                        Expirar usuario
                      </a>`
        } else {
          footer = `<a href="javascript:void(0)" 
                      class="btn btn-sm btn-success" 
                      onclick="app.modalUserActivate('${prm}')" 
                      data-toggle="modal" data-dismiss="modal">
                        Activar usuario
                      </a>`
        }
    } else {
      message += '<p>No hay datos del usuario seleccionado.</p>'
    }

    app.modal({
      title: 'Detalles del usuario',
      body: message,
      footer: footer
    });
  });
}

/**
 * Recurrencias - Modal historial de pagos
 * @param {string} prm
 */
app.modalRePayDetail = prm => {
  $.ajax({
    url: app.config.api + 'paymenthistory/' + prm + '/10',
    method: 'GET'
  }).done((data) => {
    let recurrence = '';

    if (data) {
      recurrence += `<div class="alert alert-secondary shadow-sm">
                      <b>Usuario:</b> ${prm}
                     </div>
                     <table class="table">
                      <thead>
                        <tr>
                          <th scope="col">Integrador</th>
                          <th scope="col">Estado</th>
                          <th scope="col">Modificación</th>
                          <th scope="col">Manual</th>
                        </tr>
                      </thead>
                     <tbody>`;

      data.data.forEach(element => {
        recurrence += `<tr>
                        <td>${element.gateway_id}</td>
                        <td>${this.renders.hisPayState(element.status)}</td>
                        <td>${this.renders.date(element.modification_date)}</td>
                        <td>${this.renders.boolean(element.manual)}</td>
                       </tr>`;
      });
      recurrence += "</tbody></table>";
    } else {
      recurrence += '<p>No hay datos para el usuario seleccionado.</p>'
    }

    app.modal({
      class: 'modal-lg',
      title: 'Historial de pagos',
      body: recurrence,
      footer: `${data.records > 10 ? `<a href="/ui/historial-pagos/?usuario=${prm}" 
                                      class="btn btn-sm btn-secondary">Ver más registros</a>` : ''}`
    });
  });
}

/**
 * Recurrencias - Modal pago manual
 * @param {string} prm
 */
app.modalManualPay = prm => {
  this.modal({
    title: 'Pago manual',
    body: '¿Está seguro de que desea realizar el pago manual?',
    footer: `<a href="javascript:void(0)" class="btn btn-sm btn-outline-secondary" data-dismiss="modal">Cerrar</a>
             <a href="javascript:void(0)" class="btn btn-sm btn-danger" id="btnManualPay">Pagar</a>`
  });

  $('#btnManualPay').on('click', () => {
    let data = { 'userpayment_id': prm }

    $.ajax({
      type: 'POST',
      url: '/ui/manualpayment/',
      data: JSON.stringify(data),
      beforeSend:
        this.loadingButton({
          selector: '#btnManualPay',
          loading: true 
        })
    }).done(() => {
      alert = `<div class="alert alert-success" role="alert">Pago efectuado correctamente.</div>`;
      $(app.config.tableSelector).DataTable().ajax.reload();
    }).fail(resp => {
      alert = `<div class="alert alert-danger" role="alert">${resp.responseJSON.message}</div>`;
    }).always(() => {
      $('.modal-body').prepend(alert);
      this.loadingButton({
        selector: '#btnManualPay'
      })
    });
  });
}

/**
 * Historial de pago - Detalle
 * @param {string} prm
 */
app.modalHisDetail = prm => {
  let rowDecoded = window.atob(prm);
  let row = JSON.parse(rowDecoded);

  this.modal({
    class: 'modal-lg',
    title: 'Detalle de pago',
    body: `<div class="alert alert-secondary shadow-sm">
            <b>Usuario:</b> ${row.user}
           </div>
           <div class="card shadow-sm mt-3">
            <div class="card-body">
              <div class="row">
                <div class="col">
                  <p><b>ID de Pago:</b> ${row.payment_id}</p>
                  <p><b>ID de Recurrencia:</b> ${row.user_payment}</p>
                  <p><b>Código:</b> ${row.code}</p>
                  <p><b>Tarjeta de Crédito:</b> ${row.card_id}</p>
                  <p><b>Número Tarjeta de Crédito:</b> ${this.renders.creditCard(row.card)}</p>
                  <p><b>Estado:</b> ${this.renders.hisPayState(row.status)}</p>
                  <p><b>Integrador:</b> ${row.integrator} (${row.gateway_id})</p>
                </div>
                <div class="col-5">
                  <p><b>Monto:</b> ${row.amount}</p>
                  <p><b>Impuesto:</b> ${row.vat_amount}</p>
                  <p><b>Neto:</b> ${row.taxable_amount}</p>
                  <p><b>Descuento:</b> ${row.disc_pct}</p>
                  <p><b>Descripción:</b> ${row.description}</p>
                  <p><b>Mensaje:</b> <a href="#message" 
                                        role="button" aria-expanded="false" 
                                        aria-controls="message"
                                        data-toggle="collapse" 
                                        class="badge badge-secondary">
                                          <span>Ver mensaje</span>
                                          <span style="display:none;">Ocultar mensaje</span>
                                        </a>
                  </p>
                  <p><b>Pago manual:</b> ${this.renders.boolean(row.manual)}</p>
                </div>
              </div>
              <div class="row">
                <div class="col">
                  <div class="collapse multi-collapse" id="message">
                    <hr>
                    <h6>Mensaje</h6>
                    <p>${row.message}</p>
                  </div>
                </div>
              </div>
            </div>
           </div>`
  });

  $('.modal [role=button]').click(() => {
    $('.modal [role=button] span').toggle();
  })
}

/**
 * Filtro (captura parametro "filter" por URL)
 * @param {string} prm
 * @todo Mejorar creación de array de búsqueda
 */
app.columnSearch = (field, key) => {
  let search = [];

  if (field == 'recurringpay') {
    switch (key) {
      case 'error':
        search = [
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          { 'search': 'Error en recurrencia' }
        ]
        break;
      case 'erroract':
        search = [
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          { 'search': 'true' },
          { 'search': 'Error en recurrencia' }
        ]
        break;
      case 'errordes':
        search = [
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          { 'search': 'false' },
          { 'search': 'Error en recurrencia' }
        ]
        break;
    }
  } else if (field == 'usuario' && key) {
    search = [
      { 'search': key }
    ]
  }

  return search
}

/**
 * Resetear filtros
 */
app.resetFilters = () => {
  let table = $(app.config.tableSelector).DataTable();

  table
    .search('')
    .columns().search('')
    .draw();

  $('#search-box, select').val('');
}

/**
 * Navegación
 * @todo Mejorar búsqueda de parametros en la URL
 */
app.navigation = () => {
  let page = window.location.pathname.split('/')[2];
  let field = window.location.search.split('=')[0].slice(1);
  let key = window.location.search.split('=').pop();

  switch (page) {
    case 'usuarios':
      app.iniTable({
        api: app.config.api + 'users',
        columns: [
          { 'title': 'ID', 'data': 'user_id' },
          { 'title': 'Email', 'data': 'email' },
          { 'title': 'Tarjeta de Crédito', 'data': 'card', 'render': data => this.renders.creditCard(data) },
          { 'title': 'Activo', 'data': 'is_active', 'render': data => this.renders.boolean(data) },
          { 'title': 'País', 'data': 'country' },
          { 'title': 'Expiración', 'type': 'date-eu', 'data': 'expiration', 'render': data => this.renders.date(data) },
          { 'title': 'Acciones', 'orderable': false, 'render': (data, type, row) => this.renders.usersActions(data, type, row) },
        ],
        filters: [
          { column_number: 4, filter_label: 'País' },
          { column_number: 3, filter_label: 'Activo' },
        ],
        order: [[ 5, "desc" ]]
      });
    break;
    case 'pagos-recurrentes':
      app.iniTable({
        api: app.config.api + 'payments',
        searchCols: this.columnSearch(field, key),
        columns: [
          { 'title': 'Usuario', 'data': 'user' },
          { 'title': 'Monto', 'data': 'amount' },
          { 'title': 'Moneda', 'data': 'currency' },
          { 'title': 'País', 'data': 'country' },
          { 'title': 'Fecha de Modificación', 'type': 'date-eu', 'data': 'modification_date', 'render': data => this.renders.date(data) },
          { 'title': 'Fecha de Pago', 'type': 'date-eu', 'data': 'payment_date', 'render': data => this.renders.date(data) },
          { 'title': 'Recurrencia', 'data': 'recurrence' },
          { 'title': 'Activo', 'data': 'is_active', 'visible': false },
          { 'title': 'Estado', 'data': 'status', 'render': data => this.renders.rePayState(data) },
          { 'title': 'Reintentos', 'data': 'retries' },
          { 'title': 'Mensaje', 'data': 'message', 'render': data => this.renders.rePayMessage(data) },
          { 'title': 'Acciones', 'orderable': false, 'render': (data, type, row) => this.renders.rePayActions(data, type, row) },
        ],
        filters: [
          { column_number: 7, filter_label: 'Estado'},
          { column_number: 6, filter_label: 'Recurrencia'},
          { filter_type: 'date_range', column_number: 5, filter_label: 'Pago' },
          { filter_type: 'date_range', column_number: 4, filter_label: 'Modificación' },
          { column_number: 3, filter_label: 'País'},
        ],
        order: [[ 4, "desc" ]]
      });
      break;
    case 'historial-pagos':
      app.iniTable({
        api: app.config.api + 'paymenthistory',
        searchCols: this.columnSearch(field, key),
        columns: [
          { 'title': 'Usuario', 'data': 'user' },
          { 'title': 'Integrador', 'data': 'gateway_id' },
          { 'title': 'Estado', 'data': 'status', 'render': data => app.renders.hisPayState(data) },
          { 'title': 'Monto', 'data': 'amount' },
          { 'title': 'Fecha de Modificación', 'type': 'date-eu', 'data': 'modification_date', 'render': data => app.renders.date(data) },
          { 'title': 'Descripción', 'data': 'description' },
          { 'title': 'Manual', 'data': 'manual', 'render': data => app.renders.boolean(data) },
          { 'title': 'Código', 'data': 'code' },
          { 'title': 'Acciones', 'orderable': false, 'render': (data, type, row) => app.renders.hisPayActions(data, type, row) },
        ],
        filters: [
          { column_number: 2, filter_label: 'Estado' },
          { filter_type: 'date_range', column_number: 4, filter_label: 'Modificación' },
          { column_number: 6, filter_label: 'Manual' },
        ],
        order: [[ 4, "desc" ]]
      });
      break;
  }
}

$(document).ready(() => {
  $('#sidebar').mCustomScrollbar({
    theme: 'minimal'
  });

  $('#sidebarCollapse').on('click', () => {
    $('#sidebar, #content').toggleClass('active');
  });

  $('#fullScreen').on('click', () => {
    if (!this.fullScreenState) {
      this.fullScreen(true);
    } else {
      this.fullScreen();
    }
  });

  app.navigation();
});