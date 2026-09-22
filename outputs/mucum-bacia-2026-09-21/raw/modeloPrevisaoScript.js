
function setUpModeloPrevisao()
{
	$("#dlgModeloPrevisaoCadastro").dialog(
			{
				resizable: true,
				height: 330,
				width: 500,
				autoOpen: false,
				modal: true,
				buttons: {
					"Fechar" : function()
					{
						closeModeloPrevisao();
					}
				},
				close: CloseFunction,
				scroll: hideAll
			}
		);
	if (!$("#dlgModeloPrevisaoListagem").hasClass('ui-dialog-content')){
		$("#dlgModeloPrevisaoListagem").dialog(
				{
					resizable: true,
					height: 325,
					width: 580,
					autoOpen: false,
					modal: false
				}
			);
	}
}

function closeModeloPrevisao(){
	 hideAll();
	$("#dlgModeloPrevisaoCadastro").dialog("close");
}

function clickButtonArquivoModeloPrevisao(com,grid) {

}

function clickButtonModeloPrevisao(com,grid)
{
	if (com=='Excluir')
	{
		var ids = getGridId(grid);
		if (ids){
			excluirModeloPrevisao(ids,com,grid);
		}else{
			jError("Selecione ao menos um item da listagem.", 'Aten\u00e7\u00e3o');
		}

	}else if (com=='Novo')
	{
		abreModeloPrevisao().complete(function(){bindFields();});
	}
}

function abreModeloPrevisaoListagem(){
	$.get("telas/medicao/modeloPrevisao/modeloPrevisaoListagem.html",
			function(data)
			{
				$("#dlgModeloPrevisaoListagem").html( data );
				criaGridModeloPrevisao();
				$("#dlgModeloPrevisaoListagem").dialog("open");
			});
}


function abreModeloPrevisao()
{
	return $.get("telas/medicao/modeloPrevisao/modeloPrevisaoCadastro.html",
		function(data)
		{

			$("#dlgModeloPrevisaoCadastro").html( data );
			$("#dlgModeloPrevisaoCadastro").dialog("open");
			populaSelect(PontoMonitoramentoService, $("#ModeloPrevisao_selPontoMonitoramento"), 'id', 'nome',true,'GPP');
		});


}

function criaGridModeloPrevisao(){

	$("#gridModeloPrevisao").flexigrid
	(
			{
				service: ModeloPrevisaoService,
				colModel : [{display: 'ID', name : 'id', width : 40, sortable : true, align: 'center', hide: true},
				            {display: 'Nome', name : 'nome', width : 200, sortable : true, align: 'left'},
							{display: 'Sigla', name : 'sigla', width : 50, sortable : true, align: 'left'},
							{display: 'Ponto de monitoramento', name : 'pontoMonitoramento.nome', width : 200, sortable : true, align: 'left'},
							{display: 'Status', name : 'status', width : 60, sortable : true, align: 'left',render: 'Ativo/Inativo'}
				            ],
				            buttons : [{name: '<input type="checkbox" name="all" style="display:none;" />Selecionar todos', onpress : selectAllGrid},{separator: true},
				                       {name: 'Novo', bclass: 'add', onpress : clickButtonModeloPrevisao},
				                       {name: 'Excluir', bclass: 'delete', onpress : clickButtonModeloPrevisao},
				                       {separator: true},
				                       {name: 'Exportar', bclass: 'excel_export', onpress : function(){$("#gridModeloPrevisao").exportExcel();}}
				                       ],
	                       searchitems : [
	        								{display: 'nome', name : 'nome', isdefault: true},
	        								{display: 'Ponto de monitoramento', name : 'pontoMonitoramento.nome'}
	        								],
				                       usepager: true,
				                       sortname: "nome,pontoMonitoramento.nome",
									   sortorder: "asc",
				                       singleSelect: false,
				                       pagestat: 'Exibidos {from} at\u00e9 {to} de {total} registros',	                       pagetext: 'P&aacute;gina',
				          			   outof: 'de',
				          			   findtext: 'Busca',
				          			   procmsg: 'Buscando registros, aguarde ...',
				          			   nomsg: 'Nenhum registro encontrado.',
				                       useRp: true,
				                       showTableToggleBtn: true,
				                       height: 180,
				                       dblclickFunction: dblclickModeloPrevisao,
				                       parentElement: $("#dlgModeloPrevisaoListagem")
			}
	);


	$('b.top').click
	(
			function ()
			{
				$(this).parent().toggleClass('fh');
			}
	);


}

function dblclickModeloPrevisao(row) {
	abreModeloPrevisao().complete(function() {

		var id = getIdSelectRow(row);

		$('#ModeloPrevisao_id').val(id);

		populaDadosModeloPrevisao();
		bindFields();
	});


}

function populaDadosModeloPrevisao() {

	var id = 0;
	if($('#ModeloPrevisao_id').val()){
		id = parseInt($('#ModeloPrevisao_id').val());
	}

	var fn = function(bean) {
		$('#ModeloPrevisao_id').val(bean.id);
		$('#ModeloPrevisao_nome').val(bean.nome);
		$('#ModeloPrevisao_sigla').val(bean.sigla);
		$('#ModeloPrevisao_observacao').val(bean.observacao);
		$('#ModeloPrevisao_selPontoMonitoramento').val(bean.pontoMonitoramento.id);

		if (bean.status){
			$('#ModeloPrevisao_statusAtivo').addClass('selected');
			$('#ModeloPrevisao_statusInativo').removeClass('selected');
		}else{
			$('#ModeloPrevisao_statusInativo').addClass('selected');
			$('#ModeloPrevisao_statusAtivo').removeClass('selected');
		}

	};

	ModeloPrevisaoService.findById(id,{callback: fn});

}

function excluirModeloPrevisao(ids,com,grid) {
	jConfirm('Deseja realmente excluir este registro?', 'Confirma\u00e7\u00e3o', function(r) {
		if (r){
			var fn = function() {

				jAlert("Registro exclu\u00eddo com sucesso.", 'Sucesso');
				$("#gridModeloPrevisao").flexReload();

			};

			ModeloPrevisaoService.deleteByIds(ids,{callback: fn});
		}
	});

}


function saveModeloPrevisao(com,grid) {


	if ($('#ModeloPrevisao_form').validationEngine('validate')) {

		var bean = {
				id:$('#ModeloPrevisao_id').val(),
				nome:$("#ModeloPrevisao_nome").val(),
				sigla:$("#ModeloPrevisao_sigla").val().toUpperCase(),
				observacao: $("#ModeloPrevisao_observacao").val(),
				pontoMonitoramento: $("#ModeloPrevisao_selPontoMonitoramento").objectId(),
				status: $('#ModeloPrevisao_statusAtivo').hasClass('selected')
		};

			var fn = function() {

				if(!$("#ModeloPrevisao_id").val()) {
					jAlert("Inserido com sucesso.", 'Sucesso');
				} else {
					jAlert("Atualizado com sucesso.", 'Sucesso');
				}

				$("#gridModeloPrevisao").flexReload();
				closeModeloPrevisao();

			};

			ModeloPrevisaoService.save(bean,{callback: fn});
	}
}