
function setUpBoletim()
{
	$("#dlgBoletimCadastro").dialog(
			{
				resizable: false,
				height: 470,
				width: 800,
				autoOpen: false,
				modal: false,
				close: CloseFunction,
				scroll: hideAll
			}
		);
	if (!$("#dlgBoletimListagem").hasClass('ui-dialog-content')){
		$("#dlgBoletimListagem").dialog(
				{
					resizable: true,
					height: 480,
					width: 700,
					autoOpen: false,
					modal: false
				}
			);
	}
}

function closeBoletim(){
	 hideAll();
	$("#dlgBoletimCadastro").dialog("close");
}

function clickButtonArquivoBoletim(com,grid) {

}



function criaGridBoletim(filterParams){

	$("#gridBoletim").flexigrid
	(
			{
				service: BoletimService,
				filterParams: filterParams,
				colModel : [{display: 'ID', name : 'id', width : 40, sortable : true, align: 'center', hide: true},
				            {display: 'Nome do boletim', name : 'nome', width : 200, sortable : true, align: 'left'},
				            {display: 'Data da gera&ccedil;&atilde;o', name : 'dataGeracao', width : 100, sortable : true, align: 'center',render: 'dd/mm/yy'},
				            {display: 'Hora da gera&ccedil;&atilde;o', name : 'dataGeracao', width : 100, sortable : true, align: 'center',render: 'HH:MM'},
				            {display: 'Respons&aacute;vel', name : 'usuario.nome', width : 200, sortable : true, align: 'left'}
				            ],
				            buttons : [{name: '<input type="checkbox" name="all" style="display:none;" />Selecionar todos', onpress : selectAllGrid},{separator: true},
				                       {name: 'Visualizar', bclass: 'find', onpress : clickButtonBoletim},
				                       {name: 'Excluir', bclass: 'delete', onpress : clickButtonBoletim},
				                       {separator: true},
				                       {name: 'Enviar boletim', bclass: 'email', onpress : clickButtonBoletim},
				                       {name: 'Exportar', bclass: 'excel_export', onpress : function(){$("#gridBoletim").exportExcel();}}
				                       ],
	                       searchitems : [
	        								{display: 'Nome do boletim', name : 'nome', isdefault: true},
	        								{display: 'Respons&aacute;vel', name : 'usuario.nome'}
	        								],
	                       usepager: true,
	                       sortname: "dataGeracao,id",
						   sortorder: "desc",
	                       singleSelect: true,
	                       pagestat: 'Exibidos {from} at\u00e9 {to} de {total} registros',
	                       pagetext: 'P&aacute;gina',
	          			   outof: 'de',
	          			   findtext: 'Busca',
	          			   procmsg: 'Buscando registros, aguarde ...',
	          			   nomsg: 'Nenhum registro encontrado.',
	                       useRp: true,
	                       showTableToggleBtn: true,
	                       height: 315,
	                       dblclickFunction: dblclickBoletim,
	                       parentElement: $("#dlgBoletimListagem")
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

function dblclickBoletim(row) {

	var id = getIdSelectRow(row);

	$('#Boletim_id').val(id);

	visualizarBoletim(id);

}

function visualizarBoletim(id){
	startLoading();
	var fn = function(boletim) {
		stopLoading();
		if (boletim) {
			openDownloadDialog(boletim);
		} else {
			jError("N\u00e3o existe nenhum dado a ser exibido.", 'Erro');
		}
	};

	BoletimDisseminacaoService.exportPdf(id,{callback: fn});
}

function clickButtonBoletim(com,grid)
{
	if (com=='Excluir')
	{
		var ids = getGridIdNameGrid('gridBoletim');
		if (ids){
			excluirBoletim(ids,com,grid);
		}else{
			jError("Selecione ao menos um item da listagem.", 'Aten\u00e7\u00e3o');
		}

	}else if (com=='Visualizar')
	{
		var ids = getGridIdNameGrid('gridBoletim');
		if (ids){
			visualizarBoletim(ids[0]);
		}else{
			jError("Selecione ao menos um item da listagem.", 'Aten\u00e7\u00e3o');
		}
	}else if(com=='Enviar boletim'){

		var ids = getGridIdNameGrid('gridBoletim');
		if (ids){
			abreEnviarBoletimComIds(ids);
		}else{
			jError("Selecione ao menos um item da listagem.", 'Aten\u00e7\u00e3o');
		}

	}


}

function excluirBoletim(ids,com,grid) {

	jConfirm('Deseja realmente excluir este registro?', 'Confirma\u00e7\u00e3o', function(r) {
		if (r){
			var fn = function() {

				jAlert("Registro exclu\u00eddo com sucesso.", 'Sucesso');
				$("#gridBoletim").flexReload();

			};

			BoletimService.deleteByIds(ids,{callback: fn});
		}
	});

}

function abreBoletimListagem(){
	$.get("telas/publicacao/boletim/boletimListagem.html",
			function(data)
			{
				$("#dlgBoletimListagem").html( data );
				criaGridBoletim(null);
				$("#dlgBoletimListagem").dialog("open");
				bindFields();
			});
}


function buscaNumeroBoletim(){
	var tipoBoletim = $('#Boletim_selTipoBoletim option:selected').toString();

	if (tipoBoletim == null){
		tipoBoletim ='BOLETIM_DIARIO';
	}

	var fn = function(numero) {
		$('#Boletim_numero').val(numero);
	};
	BoletimService.obtemUltimoNumeroBoletimByTipo(tipoBoletim,{callback: fn});

}


function abreBoletim()
{
	 setUpBoletim();
	startLoadingTela('dlgBoletimCadastroMask');
	 $.get("telas/publicacao/boletim/boletimCadastro.html",
		function(data)
		{

			$("#dlgBoletimCadastro").html( data );
			$("#dlgBoletimCadastro").dialog("open");

			var myNicEditor = new nicEditor({fullPanel : true});
	          myNicEditor.setPanel('Boletim_Panel');
	          myNicEditor.addInstance('Boletim_texto');
	          populaDadosTextoBoletim();

	          var myNicEditorChart = new nicEditor({fullPanel : true});
	          myNicEditorChart.setPanel('boletimCharts_Panel');
	          myNicEditorChart.addInstance('boletimCharts');

	          var myNicEditorHead = new nicEditor({fullPanel : false});
	          myNicEditorHead.setPanel('Boletim_head_panel');
	          myNicEditorHead.addInstance('Boletim_head');

	          $("#Boletim_responsavel").val($("#usuarioLogado").text().trim());
	          $("#Boletim_responsavel").attr("readonly", true);

	          constroiGridPontoMonitoramentoBoletim();
	          constroiGridTemplateGrafico();
	          constroiCabecalhoBoletim();
	          populaSelect(TipoBoletimService, $('#Boletim_selTipoBoletim'), 'id', 'nome', false,'GPB');

	          buscaNumeroBoletim();
	          stopLoadingTela('dlgBoletimCadastroMask');

	          $("#Boletim_data").setDateString(new Date());
			  $("#Boletim_hora").setHoraCheia(new Date());

		}).complete(function(){ bindFields();});

}

function checkAllPontos(){
	$("input[name=chkPontoMonitoramentoBoletim][type=checkbox]").each(function() {
		$(this).attr('checked',$("#idGridPontos").is(':checked'));
	});
}
function checkAllTemplates(){
	$("input[name=chkTemplateGrafico][type=checkbox]").each(function() {
		$(this).attr('checked',$("#idGridTemplates").is(':checked'));

	});

	geraGraficoBoletim();
}

function checkAllTemplatesByPonto(idPonto){

	if ($("input[id=idHorasPrevisaoBoletim_"+idPonto+"]").toString()!= null){
		$("input[id=idPontoMonitoramentoBoletim_"+idPonto+"]").attr('checked',true);

		$("input[name=chkTemplateGrafico][type=checkbox]").each(function() {
			var pontos = new Array();

			pontos = $(this).attr('idsPontoMonitoramento').split(",");
			for ( var i = 0; i < pontos.length; i++) {
				if (idPonto==pontos[i]){
					$(this).attr('checked',true);
						geraGraficoBoletim();
				}
			}

		});

	}else{
		$("input[id=idPontoMonitoramentoBoletim_"+idPonto+"]").attr('checked',false);
	}
}

function constroiGridPontoMonitoramentoBoletim(){

	var fn = function(dados) {

		var htmlGrid = "";

		for ( var i = 0; i < dados.length; i++) {
			var htmlTr="";
			var htmlTd="";
			var idLinha = dados[i].id;

			htmlTr= "<tr>"


			// Ponto de Monitoramento Id Ponto
			htmlTd+= "<td valign='top' class='tableBoletim' id='nomePonto_"+idLinha+"'>";
			htmlTd+="<input style='display:none;' type='checkbox' value='"+idLinha+"' name='chkPontoMonitoramentoBoletim' id='idPontoMonitoramentoBoletim_"+idLinha+"'/>";
			htmlTd+= "<span id='spanPonto_"+idLinha+"' name='"+dados[i].sigla+"'>" + dados[i].nome + "</span>" ;
			if (dados[i].rio != null){
				htmlTd+= " - " + dados[i].rio;
			}
			htmlTd+= "</td>";


			// Horas previs\u00e3o
			htmlTd+= "<td valign='top' class='tableBoletim'>"
			htmlTd+="<input size='12' maxlength='3' style='text-align: center;' type='text' value='' name='inpHorasPrevisaoBoletim' id='idHorasPrevisaoBoletim_"+idLinha+"'/>";
			htmlTd+="</td>"

			htmlTr+= htmlTd;
			htmlTr+= "</tr>"
			htmlGrid+= htmlTr;
		}

		$("#gridBoletim_pontoMonitoramento").html(htmlGrid);

		for ( var i = 0; i < dados.length; i++) {
			$("input[id=idHorasPrevisaoBoletim_"+dados[i].id+"]").numeric();
			$("input[id=idHorasPrevisaoBoletim_"+dados[i].id+"]").attr('onBlur',"checkAllTemplatesByPonto("+dados[i].id+")");
		}

	}

	PontoMonitoramentoService.findAllSecurity('GPB',{callback: fn});

}

function constroiGridTemplateGrafico(){

	var fn = function(dados) {

		var htmlGrid = "";

		for ( var i = 0; i < dados.length; i++) {
			var htmlTr="";
			var htmlTd="";
			var idLinha = dados[i].id;

			var idsPontoMonitoramento = new Array();

			for ( var j = 0; j < dados[i].listSensorTemplateGrafico.length; j++) {
				idsPontoMonitoramento.push(dados[i].listSensorTemplateGrafico[j].pontoMonitoramento.id);
			}

			htmlTr= "<tr>"

			// Id Template
			htmlTd+="<td valign='top' class='tableBoletim'>";
			htmlTd+="<input onclick='geraGraficoBoletim()' type='checkbox' idsPontoMonitoramento='"+idsPontoMonitoramento+"' value='"+idLinha+"' name='chkTemplateGrafico' id='idTemplateGrafico_"+idLinha+"'/>";
			htmlTd+="</td>";

			// Template gráfico
			htmlTd+= "<td valign='top' class='tableBoletim' id='nomeTemplateGrafico_"+idLinha+"'>"+ dados[i].nome +"</td>"

			htmlTr+= htmlTd;
			htmlTr+= "</tr>"
			htmlGrid+= htmlTr;
		}

		$("#gridBoletim_Templates").html(htmlGrid);

	}

	TemplateGraficoService.findByExibirBoletim(true,'GPB',{callback: fn});

}


function geraGraficoBoletim(){
	$("#erroChartBoletim").hide();
	var idsTemplate = new Array();
	$('input[name=chkTemplateGrafico][type=checkbox]:checked').each(function(){
		idsTemplate.push($(this).toFloat());
	});

	var fnChart = function(objScript) {
		$('#boletimCharts').html('');
		openDivChart(objScript,"boletimCharts");
		$("#boletimCharts").html(replaceAll($("#boletimCharts").html(),'position: relative;',''));
		$("#boletimCharts").html(replaceAll($("#boletimCharts").html(),'overflow: hidden;',''));
	};

	if ($('#Boletim_form').validationEngine('validate')) {
		var dataHoraGeracao = getDateTime($("#Boletim_data").val(),$("#Boletim_hora").val());
	}else{
		return false;
	}

	GeradorGraficoService.obtemListGraficoComData("boletimCharts",idsTemplate,750,550,false,"folha",dataHoraGeracao,{callback: fnChart});
}

function errhChart (errorMsg, exception){
    $("#erroChartBoletim").show();
}


function limpaGraficoBoletim(){
	$('#boletimCharts').html('');
	$("#erroChartBoletim").hide();
	$('input[name=chkTemplateGrafico][type=checkbox]').attr('checked',false);
	$("#idGridTemplates").attr('checked',false);

}

function montaDadosBoletim() {
	$('#Boletim_texto').html('');
	if ($('#Boletim_data').toString() == null || $('#Boletim_hora').toString() == null || $('#Boletim_numero').toString() == null ){
		$('#Boletim_tabs').tabs('select', '1');
	}

	if ($('#Boletim_form').validationEngine('validate')) {

		startLoading();
		var numero = $('#Boletim_numero').val();
		var data= $('#Boletim_data').val();
		var hora= $('#Boletim_hora').val();
		var responsavel= $('#Boletim_responsavel').val();
		var boletim= $('#Boletim_selTipoBoletim option:selected').text();

		var fn = function(bean) {

			setTimeout(function(){


				if (bean.length>0){

					if ( $("#Boletim_selTipoBoletim").val()=="BOLETIM_DIARIO"){
						$('#Boletim_texto').html(bean[0].textoDiario);
					}else if ( $("#Boletim_selTipoBoletim").val()=="BOLETIM_EXTRAORDINARIO"){
						$('#Boletim_texto').html(bean[0].textoExtraordinario);
					}

					$('#Boletim_texto').html($('#Boletim_texto').html().replace('{num}',numero));
					$('#Boletim_texto').html($('#Boletim_texto').html().replace('{data}',data));
					$('#Boletim_texto').html($('#Boletim_texto').html().replace('{hora}',hora));
					$('#Boletim_texto').html($('#Boletim_texto').html().replace('{responsavel}',responsavel));

					$('#Boletim_texto').html($('#Boletim_texto').html().replace('{boletim}',boletim));

					if ($('#boletimCharts').html().length>20){
						$('#Boletim_texto').html($('#Boletim_texto').html().replace('{grafico}', $('#boletimCharts').html()+'<div class="folha"></div>'));

					}else{
						$('#Boletim_texto').html($('#Boletim_texto').html().replace('{grafico}',''));
					}

				}


				var contexto  = obtemTabelaPontoMonitoramentoBoletim();

				if ($('#Boletim_texto').html().indexOf('{assinatura}')>=0){
					aplicaTabelaBoletim(false,contexto);

					//TAG {assinatura}
					aplicaAssinaturaBoletim(true);

				}else{
					aplicaTabelaBoletim(true,contexto);
				}

				// TAG {relatorio}
				gerarRelatorioBoletim();
				$('#Boletim_tabs').tabs('select', '3');


			},2000);

		};

		TextoBoletimService.findAll({callback: fn});
	}
}

function aplicaTabelaBoletim(aplicaQuebra, contexto){
	if (contexto.length>10){
		$('#Boletim_texto').html($('#Boletim_texto').html().replace('{tabela}',aplicaQuebraFolha(aplicaQuebra, contexto)));
	}else{
		$('#Boletim_texto').html($('#Boletim_texto').html().replace('{tabela}',''));
	}
}

function aplicaQuebraFolha(aplicaQuebra, conteudo){
	if (aplicaQuebra){
		return '<div class="folha">' + conteudo + '</div>';
	}else{
		return conteudo;
	}
}

function aplicaAssinaturaBoletim(aplicaQuebra){

	var fn = function(assinatura) {

		$('#Boletim_texto').html($('#Boletim_texto').html().replace('{assinatura}',aplicaQuebraFolha(aplicaQuebra, assinatura)));
	};

	UsuarioService.getAssinaturaUsuarioByRequest({callback: fn});
}

function geraTabelaBoletim(){

	var textoTabela = "<div align='center'><style type='text/css'>#boletimPontos tbody tr.even td {  background-color: #99CCFF;	border: 1px solid #AAAAAA;}#boletimPontos tbody tr.odd  td {  background-color: #FFFFFF;	border: 1px solid #AAAAAA;}</style>";
	textoTabela += "<span style='font-size: 15px; font-weight: bold; font-family: sans-serif;'>Resumo do ";
	textoTabela+=$('#Boletim_selTipoBoletim option:selected').text() + " n&deg; ";
	textoTabela+= $('#Boletim_numero').val();
	textoTabela+="<br>";
	textoTabela+="Gerado as ";
	textoTabela+=$('#Boletim_hora').val();
	textoTabela+=" do dia  ";
	textoTabela+=$('#Boletim_data').val()+ ". </span></div>";
	textoTabela+="<br>";
	textoTabela+="<br>";
	textoTabela+=$('#Boletim_texto').html();

	var tabela = {texto:textoTabela};
	TabelaBoletimService.save(tabela,{errorHandler: errh});
}


function gerarRelatorioBoletim(){

	var dataHoraGeracao = getDateTime($("#Boletim_data").val(),$("#Boletim_hora").val());
	var numero = $('#Boletim_numero').val();

	var fn = function(relatorio) {

		$('#Boletim_texto').html($('#Boletim_texto').html().replace('{relatorio}',relatorio));
		$('#Boletim_texto').html($('#Boletim_texto').html().replace('{num}',numero))
		stopLoading();
	};

	RelatorioService.gerarRelatorio('tableRelatorio',24,dataHoraGeracao,$('#Boletim_numero').val(),{callback: fn});
}


function obtemTabelaPontoMonitoramentoBoletim(){
	var pontosChecados=0;

	var tabela = getStyleEvenOdd('boletimPontos');

	tabela += "<div align='center' style='width:100%' id='tabelaBoletim'> <table id='boletimPontos' cellpadding='0' cellspacing='0' border='0'><tbody>";
	//tabela += "<tr class='odd'><td>Ponto de monitoramento</td><td>Horas previs&atilde;o</td><td>Observa&ccedil;&atilde;o</td></tr>";

	var flagEvenOdd = 'odd';
	$("input[name=chkPontoMonitoramentoBoletim][type=checkbox]:checked").each(function(){
		pontosChecados++;
		var linha = $(this).val();
		var tr="";
		var td="";

		tr="<tr class='"+flagEvenOdd+"'>";
			//Ponto
			td+='<td style="width: 250px; text-align: left;">';
				td+=$("td[id=nomePonto_"+linha+"]").html();
			td+='</td>';

			//Obs
			td+='<td style="width: 250px; text-align: left;">';
			td+="";
			td+='</td>';

			//Hora
			td+='<td style="width: 250px; text-align: left;">';
				td+= getFullDate(linha);
			td+='</td>';

		tr+=td;
		tr+="</tr>";

		if (flagEvenOdd=='even'){
			flagEvenOdd = 'odd';
		}else if (flagEvenOdd=='odd'){
			flagEvenOdd='even';
		}

		tabela+=tr;
	});

	tabela+= "</tbody></table></div>";

	if (pontosChecados>0){
		return tabela;
	}else{
		return "";
	}
}

function getFullDate(idLinha){

	var horasAdd = $("input[id=idHorasPrevisaoBoletim_"+idLinha+"]").toFloat();

	var dateAux = getDateTime($("#Boletim_data").val(),$("#Boletim_hora").val());

	if (dateAux== null){
		return horasAdd;
	}

	dateAux.setHours(dateAux.getHours()+horasAdd);

	var weekday=new Array("domingo","segunda-feira","ter\u00e7a-feira","quarta-feira","quinta-feira","sexta-feira","sabado")

	var hora = padLeft(dateAux.getHours(), 2);
	var minuto = padLeft(dateAux.getMinutes(), 2);
	var retorno = hora + ":" + minuto;

	var retorno = " \u00e0s " + retorno + " do dia " +  $.datepicker.formatDate('dd/mm/yy', dateAux) + " (" + weekday[dateAux.getDay()] + ")";

	return retorno;
}

function gerarBoletim() {

	if ($('#Boletim_texto').html()=="<br>"){
		jError("O formul\u00e1rio deve ser preenchido antes de gerar o boletim.", 'Erro');
		return false;
	}

	if ($('#Boletim_form').validationEngine('validate')) {
		startLoading();

		var bean = {
				id:null,
				texto: $('#Boletim_texto').html(),
				dataGeracao: getDateTime($("#Boletim_data").val(),$("#Boletim_hora").val()),
				tipoBoletim: $("#Boletim_selTipoBoletim").val(),
				nome: $("#Boletim_selTipoBoletim option:selected").text() + " n. " + $('#Boletim_numero').val(),
				numero: $('#Boletim_numero').val()
		};


		bean.listTemplateGrafico = montaListTemplateGrafico();

		var fn = function(anexoBoletim) {

			geraTabelaBoletim();

			stopLoading();

			if (anexoBoletim.arquivo) {
				openDownloadDialog(anexoBoletim.arquivo);
				var ids = new Array();
				ids.push(anexoBoletim.boletim.id);

				jConfirm('Deseja enviar este boletim?', 'Confirma\u00e7\u00e3o', function(r) {
					if (r){
							abreEnviarBoletimComIds(ids);
					}
				});

				closeBoletim();

			} else {
				jError("N\u00e3o existe nenhum dado a ser exibido.", 'Erro');
			}
		};

		BoletimService.gerarBoletim(bean,{callback: fn});
	}else{
		$('#Boletim_tabs').tabs('select', '1');
	}
}

function montaListTemplateGrafico(){

	var listTemplateGrafico = new Array();

	$("input[name=chkTemplateGrafico][type=checkbox]:checked").each(function() {

		listTemplateGrafico.push({id:$(this).toFloat()});
	});
	return listTemplateGrafico;
}

function filtrarGridBoletim(){

	if ($('#Boletim_formFilter').validationEngine('validate')) {

		var filterParams = new Array();

		var dataInicio = $("#Boletim_dataInicioFilter").val();
		var dataFim = $("#Boletim_dataFimFilter").val();

		filterParams.push(" dataGeracao >= '"+ dataInicio + " 00:00'");
		filterParams.push(" dataGeracao <= '"+ dataFim + " 23:59'");

		setUpBoletim();

		$.get("telas/publicacao/boletim/boletimListagem.html",
			function(data)
			{
				$("#dlgBoletimListagem").html( data );
				criaGridBoletim(filterParams);
				$("#dlgBoletimListagem").dialog("open");

				 $("#Boletim_dataInicioFilter").val(dataInicio);
				 $("#Boletim_dataFimFilter").val(dataFim);
				bindFields();
			});
	}
}

function limparGridBoletim(){

	$.get("telas/publicacao/boletim/boletimListagem.html",
			function(data)
			{
				setUpBoletim();
				$("#dlgBoletimListagem").html( data );
				criaGridBoletim(null);
				$("#dlgBoletimListagem").dialog("open");
				bindFields();
			});
}
/*
function populaImagemBOletimHead(){
	 $('#pathImage').val($('#Boletim_head_img_1').val());
	var file = dwr.util.getValue("Boletim_head_img_1");

	var fn = function(cabecalho) {
		$('#imagem1').attr('src',cabecalho);
	}

	var nameFile = $('#pathImage').val();

	CabecalhoBoletimService.createImage(file,nameFile,{callback: fn});
}*/

function readURLBoletim(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            $('#imagem1')
                .attr('src', e.target.result);
        };

        reader.readAsDataURL(input.files[0]);
    }
}


function constroiCabecalhoBoletim(){

	var fn = function(head) {
		if (head){
			if (head.texto){
				$("#texto_head").html(head.texto);
			}
			$("#Boletim_head_id").val(head.id);
			$("#pathImage").val(head.pathImagem1);
			if (head.imagem1){
				$('#imagem1').attr('src',head.imagem1);
			}
		}
	}

	CabecalhoBoletimService.findUniqueHead({callback: fn});
}

function salvaBoletimHead(){
	if ($('#imagem1').attr('src')=="img/no_image.gif"){
		jError("Informe a imagem para o cabe\u00e7alho.", 'Aten\u00e7\u00e3o');
		return false;
	}

	var cabecalho = {id:$("#Boletim_head_id").toInt(),texto:$("#texto_head").html()};
	cabecalho.pathImagem1 =$('#Boletim_head_img_1').val();

	var file = dwr.util.getValue("Boletim_head_img_1");
	cabecalho.imagem1=file;

	var fn = function(bean){
		$("#Boletim_head_id").val(bean.id);
		jAlert("Cabe\u00e7alho incluido com sucesso.", 'Sucesso');
	}

	CabecalhoBoletimService.save(cabecalho,{callback: fn});
}