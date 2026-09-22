
function setUpExibirDados()
{
	$("#dlgExibirDados").dialog(
			{
				resizable: true,
				height: 600,
				width: 840,
				autoOpen: false,
				modal: false,
				title:"Visualiza&ccedil;&atilde;o das informa&ccedil;&otilde;es do ponto de monitoramento",
				close: CloseFunction,
				scroll: hideAll,
				buttons: {
					"Imprimir" : function()
					{
						$("#divDadosPrint").jqprint();
					},
					"Fechar" : function()
					{
						closeExibirDados();
					}
				}
			}
		);

}

function closeExibirDados(){
	 hideAll();
	$("#dlgExibirDados").dialog("close");
}


function verDadosIdentity(idPontoMonitoramento){

	abreExibirDados().complete(function(){
		startLoading();

		var fn = function(bean) {

			$('#ExibirDados_nome').html(bean.nome);
			$('#ExibirDados_sigla').html(bean.sigla);
			$('#ExibirDados_rio').html(bean.rio);
			$('#ExibirDados_area').html(bean.areaDrenagem);
			$('#ExibirDados_altitude').html(bean.altitude);

			$('#ExibirDados_longitude').html(convertLonToDegrees(bean.longitude));
			$('#ExibirDados_latitude').html(convertLatToDegrees(bean.latitude));


		};

		PontoMonitoramentoService.findById(idPontoMonitoramento,{callback: fn});

		/*var fnGrafico = function(objScript) {
			stopLoading();
			$("#divGraficoDados").html(objScript);

		};
		GeradorGraficoService.obtemGraficoPontoMonitoramento("divGraficoDados",parseInt(idPontoMonitoramento),765,410,false,'GPM',false,{callback: fnGrafico});
		*/

		gerarRelatorioExibirDados(idPontoMonitoramento,gerarChuvaAcumuladaExibirDados);
		montaExportacaoDados(idPontoMonitoramento);
		bindFields();

	});
}

function gerarRelatorioExibirDados(idPontoMonitoramento, acaoEmCascata){

	var fn = function(relatorio) {
		$('#divMedicoesDados').html(relatorio);
		stopLoading();
		acaoEmCascata(idPontoMonitoramento);
	};
	RelatorioService.gerarRelatorioVerDados('tableRelatorio',24,idPontoMonitoramento,{callback: fn,errorHandler: function(){stopLoading();}});
}

function gerarChuvaAcumuladaExibirDados(idPontoMonitoramento){

	var fn = function(relatorio) {
		$('#divChuvaAcumulada').html(relatorio);
		stopLoading();
	};
	RelatorioService.gerarRelatorioChuvaAcumulada('tableRelatorio',idPontoMonitoramento,{callback: fn,errorHandler: function(){stopLoading();}});
}

function abreExibirDados()
{
	setUpExibirDados();
	 return $.get("telas/publicacao/exibirDados/exibirDados.html",
		function(data)
		{
			$("#dlgExibirDados").html( data );
			$("#dlgExibirDados").dialog("open");
			bindFields();
		});

}

function exportaDadosSensoresExportacao(idsSensores){
	startLoading();
	var fn = function(dados) {
		stopLoading();
		if (dados) {
			openDownloadDialog(dados);
		} else {
			jError("N\u00e3o existe nenhum dado a ser exibido.", 'Erro');
		}
	};

	ExportacaoDadosService.exportarPorSensor(idsSensores,{callback: fn});
}

function montaExportacaoDados(idPontoMonitoramento){

	var fn = function(sensores) {
		if (sensores && sensores.length >0){
			$("#fieldSetDados").show();
		}
		var html = "";
		var ids = new Array();

		for ( var i = 0; i < sensores.length; i++) {
			var nomeColuna ='';
			if (sensores[i].nomeColuna){
				nomeColuna =sensores[i].nomeColuna;
			}else 	if (sensores[i].sensor){
				nomeColuna =sensores[i].sensor.siglaRelatorio;
			}else 	if (sensores[i].nomeFormula){
				nomeColuna =sensores[i].nomeFormula;
			}

			html+="<a href='#' onclick='exportaDadosSensoresExportacao(["+sensores[i].id+"]);'><span style='color: #0000FF;'>" + nomeColuna + "&nbsp;-&nbsp;" +  sensores[i].exportacaoDados.nome + " &nbsp;&nbsp;Clique aqui!</span></a>";
			html+="</br>";
		}

		$("#divExportacaoDados").html( html );
	};

	SensorExportacaoDadosService.findByPontoMonitoramentoForExportacao(idPontoMonitoramento,{callback: fn,errorHandler: function(){stopLoading();}});
}
