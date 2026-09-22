function setUpIdentifyDialog()
{
	$("#dlgExibirDados").dialog(
			{
				resizable: true,
				height: 580,
				title: 'Gr&aacute;fico',
				width: 800,
				autoOpen: false,
				modal: false,
				close: CloseFunction,
				scroll: hideAll,
				buttons: {
					"Fechar" : function()
					{
						closeIdentify();
					}
				}
			}
		);
}

function closeIdentify(){
	 hideAll();
	$("#dlgExibirDados").dialog("close");
}

function visualizarTemplateGraficoIdentity(idPontoMonitoramento){

	startLoading();
	var fnGrafico = function(objScript) {
		stopLoading();
		if (objScript!= null && objScript!= ""){
			abreIdentify().complete(function(){
					$("#divGraficoDados").html(objScript);
			});
		}else{
			jAlert("N\u00e3o existe dados para exibir este gr\u00e1fico.", 'Aten\u00e7\u00e3o');
		}
	};

	GeradorGraficoService.obtemGraficoPontoMonitoramento("divGraficoDados",parseInt(idPontoMonitoramento),765,410,true,'GPM',false,{callback: fnGrafico,errorHandler: function(){stopLoading();}});
	bindFields();
}

function abreIdentify()
{
	setUpIdentifyDialog();
	 return $.get("telas/publicacao/identify/identify.html",
		function(data)
		{
			$("#dlgExibirDados").html( data );
			$("#dlgExibirDados").dialog("open");
			bindFields();
		});

}

