var _idEstacao;
var _codEstacao;
var _lnk;
function setCodEstacao(lnk, idEstacao, codEstacao) {
    _idEstacao = idEstacao;
    _codEstacao = codEstacao;
    _lnk = lnk.attributes["data-page"].value;
    setSession();
}
function setSession() {
    PageMethods.SetSessionIdEstacao(_idEstacao, _codEstacao, OnSucceeded, OnFailed);
}
// Função de retorno caso seja invocado com sucesso

function OnSucceeded(result, userContext, methodName) {
    if (_lnk == "Compartilhar") return;
    //window.location.href = _lnk;
    //window.location.href(_lnk, "_blank");
    window.open(_lnk, '_blank');
}
// Função de retorno caso algo dê errado
function OnFailed(error, userContext, methodName)
{
    if(error !== null) {
        alert(error.get_message());
    }
}

// Exibir Hits
function exibirHits(param) {
    document.getElementById(param).style.display = 'block';
}
// Ocultar Hits
function ocultarHits(param) {
    document.getElementById(param).style.display = 'none';
}


//function myclick(i, evento, evOrigem) {
//    var eventoo = window.event || evento;
//    var tecla = eventoo.keyCode || eventoo.witch;
//    if (tecla != 'undefined') {
//        if (tecla == 13) {
//            alert("Não é permitido apertar a tecla Enter! quando terminado o cadastro aperte o botão concluir ao final do formulário.");
//            return;
//        }
//    }
//    //Pegar a estação Selecionada no click.
//    i = document.getElementById("cphCorpo_ctl01_lstEstacoes").selectedIndex;
//    i = document.getElementById("cphCorpo_ctl01_lstEstacoes")[i].value;
//    if (evento == 'load')
//        google.maps.event.trigger(gMarkers[i], 'load');
//    else {
//        if (evento == 'click') {
//            google.maps.event.trigger(gMarkers[i], 'click');
//        }
//        else
//            google.maps.event.trigger(gMarkers[i], 'onkeypress');
//    }

//    // call server side method
//    PageMethods.SetSessionIdEstacao(i, gMarkers[i].Codigo.split('/')[0].trim());

//}


function abrirjanela(id, tipo, div) {
    //http://200.140.135.136/hidrosat/
    document.getElementById(div).style.display = "block";
    var tipoPg;
    if (tipo == 'graf')
        tipoPg = "Grafico";
    else
        tipoPg = "Tabela";

    if (navigator.appVersion.indexOf('Chrome') > 0) {
        window.open("/"+tipoPg+".aspx?idEstacao=" + id, id, 'width=1022,height=550,titlebar=no,statusbar=no,menubar=no,resizable=no,scrollbars=no');
    } else {
        var ret;
        //if (tipo == 'graf') {
        ret = window.showModalDialog(tipoPg + ".aspx?idEstacao=" + id, id, "dialogWidth:1038px;dialogHeight:550px;status:no;resizable:no;center:yes");
        //}
        //else
        //    ret = window.showModalDialog("Tabela.aspx?idEstacao=" + id, id, "dialogWidth:1022px;dialogHeight:550px;status:no;resizable:yes;center:yes");
    }
}
function abrir(div) {
    document.getElementById(div).style.display = "block";
}
function fechar(div) {
    document.getElementById(div).style.display = "none";
    //document.getElementById("saibaMais").style.display = "none";
}

/** Marcar / Desmarcar Row's **/
function marcar(row) {
    document.getElementById(row).bgColor = "#ECECFB";
    //alert('marcar');
    //alert(row);
}
function desmarcar(row) {
    document.getElementById(row).bgColor = "#FFFFFF";
    //alert('desmarcar');
}
/** Marcar / Desmarcar Row's **/

/** Link (...) Criterios **/
//<%-- onmouseover="style.textDecoration='underline';" onmouseout="style.fontWeight='normal';"--%>
function lnkMaisCriterio(item, op) {
    document.getElementById(item).style.paddingLeft = "1px";
    document.getElementById(item).style.paddingRight = "4px";
    document.getElementById(item).style.fontWeight="bold";
    document.getElementById(item).style.textDecoration = "underline";

    if (op == '0') {
        document.getElementById(item).style.paddingLeft = "3px";
        document.getElementById(item).style.paddingRight = "5px";
        document.getElementById(item).style.fontWeight="normal";
        document.getElementById(item).style.textDecoration = "none";
    }
}
/** Link (...) Criterios **/

/** Classe janela com atributos do browser */
function Janela() {
    this.getLargura = function () {
        return window.innerWidth ? window.innerWidth :
                document.body ? document.body.clientWidth :
                document.documentElement ? document.documentElement.clientWidth :
                window.screen.width;
    }
    this.getAltura = function () {
        if (navigator.appName == "Netscape") return window.innerHeight - 60; // window.innerHeight - 19
        return document.documentElement ? document.documentElement.clientHeight :
                window.innerHeight ? window.innerHeight :
                document.body ? document.body.clientHeight :
                window.screen.height;
    }
}

/** Utilizando a classe */
var janela = new Janela();
//window.alert("Altura da janela: " + janela.getAltura()+"px");
// window.alert("Largura da janela: " + janela.getLargura());
//Publicar com este perfil
//document.getElementById("map_canvas").style.height = janela.getAltura() - 213 + "px";



/*
Função inicial para habilitar ou desabilitar as estações seguindo os crítérios das legendas.
Recebe um ou uma lista de ID e a imagem padrao do controle
A função modifica:
    A imagem da legenda;
    A exibição dos pontos no mapa;
    A lista de estações no listbox de Estações;
    O label com o total de pontos/estações sendo exibidas;
    pontosMap --> ShowHideLines
*/
//Variavel para o controle da função do "Selecionar" (Item 1º da legenda)
var selAll = "Sel";


function ShowHideEstacoes(idControl, srcPadrao, item) {
    //////Descobrir o "Tipo de Informação" selecionado
    ////var tpVariavel = "";
    ////var lsVariavel = document.getElementById("cphCorpo_ctl01_rblVariavel").getElementsByTagName("input");
    ////for (var x = 0; x < lsVariavel.length; x++) {
    ////    if (lsVariavel[x].checked) {
    ////        tpVariavel = lsVariavel[x].value;
    ////        break;
    ////    }
    ////}

    //Se a legenda "Selecionar" for clicada quando estiver com todas as legendas marcadas
    if (srcPadrao == "Sel.png") {
        //Instanciar array com os controles associados ao item "Selecionar" da legenda segundo o "Tipo da Informação"
        var ctrl = idControl.split(",");
        //Varrer os controles associado ao item "Selecionar" da legenda segundo o "Tipo da Informação"
        for (var z = 0; z < ctrl.length; z++) {
            var control = document.getElementById(ctrl[z]);
            var arrImg = control.src.split("/");
            var img = (arrImg[arrImg.length - 2] + arrImg[arrImg.length - 1]).replace("pontos", "");

            //Modifica a imagem da legenda do item "Selecionar"
            if (img == "SelNd.png" || img == "SelVazio.png") {
                control.src = "inc/img/pontos/Sel.png";
                selAll = "Sel";
                continue;
            } else if (img == "Sel.png") {
                control.src = "inc/img/pontos/SelVazio.png";
                selAll = "SelVazio";
                continue;
            }

            if (selAll === "SelVazio" && img.toLowerCase().indexOf("vazio.png") == -1) {
                hideEstacoes(control, (ctrl[z].replace("img", "") + ".png").toLowerCase(), item);
                ////if (item.toLowerCase().indexOf("mapa") != -1)
                ////    hidePontosMap(control, (ctrl[z].replace("img", "") + ".png").toLowerCase());
                ////else if (item.toLowerCase().indexOf("dados") != -1)
                ////    hideLines(control, (ctrl[z].replace("img", "") + ".png").toLowerCase());
                ////else alert('Não foi possível executar esta operação');

            } else if (selAll === "Sel" && img.toLowerCase().indexOf("vazio.png") >= 0) {
                showEstacoes(control, (ctrl[z].replace("img", "") + ".png").toLowerCase(), item);
                ////if (item.toLowerCase().indexOf("mapa") != -1)
                ////    showPontosMap(control, (ctrl[z].replace("img", "") + ".png").toLowerCase());
                ////else if (item.toLowerCase().indexOf("dados") != -1)
                ////    showLines(control, (ctrl[z].replace("img", "") + ".png").toLowerCase());
                ////else alert('Não foi possível executar esta operação');
            }
        }
    }
    else //Ação para cada um dos itens da legenda ao ser clicado
    {
        var control = document.getElementById(idControl);
        if (control == null) return;
        var arrImg = control.src.split("/");
        var img = arrImg[arrImg.length - 2] + arrImg[arrImg.length - 1];
        var dir = arrImg[arrImg.length - 2];

        if (img != dir + "vazio.png") {
            hideEstacoes(control, img, item);
            ////if (item.toLowerCase().indexOf("mapa") != -1)
            ////    hidePontosMap(control, img);
            ////else if (item.toLowerCase().indexOf("dados") != -1) 
            ////    hideLines(control, img);
            ////else alert('Não foi possível executar esta operação');
        } else {
            img = srcPadrao;
            showEstacoes(control, img, item);
            ////if (item.toLowerCase().indexOf("mapa") != -1)
            ////    showPontosMap(control, img);
            ////else if (item.toLowerCase().indexOf("dados") != -1)
            ////    showLines(control, img);
            ////else alert('Não foi possível executar esta operação');
        }
    }
    if(item.toLowerCase().indexOf("mapa") != -1)
        infowindow.close();
}

//Função para exibir (modificar) os itens na página
function showEstacoes(control, img, item) {
    var count = 0;
    if (item.toLowerCase().indexOf("mapa") != -1) {
        var codIdx = 0;
        for (var i = 0; i < markers.length; i++) {
            codIdx = markers[i].EstCodigo;
            //alert(gMarkers[codIdx].TipoDado);
            if (gMarkers[codIdx].category == img.replace('/', '').replace('.png', '_.png')) {
                //alert(gMarkers[codIdx].TipoDado);
                gMarkers[codIdx].setVisible(true);
                /*Adicionar estação */
                AddItem(img.replace('/', '').replace('.png', '_.png'), gMarkers[codIdx], item);
                count++;
            }
        }
    } else if (item.toLowerCase().indexOf("dados") != -1) {
        var tableDados = document.getElementById("cphCorpo_gdUltimos");
        var l = tableDados.getElementsByTagName("tr");
        var c;
        for (var i = 2; i < l.length; i++) {
            c = l[i].getElementsByTagName("td");
            var hdfReferencia = document.getElementById("cphCorpo_gdUltimos_hdfReferencia_" + (i - 2));
            //document.getElementById("cphCorpo_gdUltimos_hdfReferencia_" + (i - 2)).value.replace('/', '')
            if (hdfReferencia.value.replace('/', '') === img.replace('/', '')) {
                //l[i].style = "display:table-row";
                l[i].style.display = "table-row";
                /*Adicionar estação */
                AddItem(img.replace('/', '').replace('.png', '_.png'), l[i], item);
                count++;
            }
        }
    } else alert('Não foi possível executar esta operação');

    /*Modifica a imagem do "tipo de informação" clicado para a imagem do ponto padrão por "tipo de informação"*/
    img = img.replace("/", "");
    control.src = "inc/img/pontos/" + img.substring(0, 1) + "/" + img.substring(1, img.length);
    MarcaSelecionar();
    document.getElementById("cphCorpo_ctl01_lblTotalPontos").innerText = Number(document.getElementById("cphCorpo_ctl01_lblTotalPontos").innerText) + count;
}

//Função para esconder (modificar) os itens na página
function hideEstacoes(control, img, item) {
    var count = 0;
    var lst = document.getElementById("cphCorpo_ctl01_lstEstacoes");
    if (item.toLowerCase().indexOf("mapa") != -1) {
        var codIdx = 0;
        for (var i = 0; i < markers.length; i++) {
            codIdx = markers[i].EstCodigo;
            if (gMarkers[codIdx].category == img.replace('/', '').replace('.png', '_.png')) {
                gMarkers[codIdx].setVisible(false);
                /*Remove item do list box*/


                var x = 0;
                do {
                    if (codIdx == lst.options[x].value)
                        lst.options[x].style.display = "none";
                    x++;
                }
                while (x < lst.options.length);



                //for (var x = 0; x < lst.options.length; x++) {
                //    if (lst.options[x].value == gMarkers[codIdx].EstCodigo) {
                //        //lst.options.remove(x);
                //        lst.options[x].style.display = "none";
                //        x = 0;
                //    }
                //}
                count++;
            }
        }
    } else if (item.toLowerCase().indexOf("dados") != -1) {
        var tableDados = document.getElementById("cphCorpo_gdUltimos");
        var l = tableDados.getElementsByTagName("tr");
        var c;
        for (var i = 2; i < l.length; i++) {
            c = l[i].getElementsByTagName("td");
            var hdfReferencia = document.getElementById("cphCorpo_gdUltimos_hdfReferencia_" + (i - 2));
            if (hdfReferencia.value.replace('/', '') === img.replace('/', '')) {
                //l[i].style = "display:none";
                l[i].style.display = "none";
                /*Remove item do list box*/
                for (var x = 0; x < lst.options.length; x++) {
                    if (lst.options[x].text.indexOf(c[2].innerHTML) != -1 && hdfReferencia.value.replace('/', '') === img.replace('/', '')) {
                        //lst.options.remove(x);

                        lst.options[x].style.display = "none";
                    }
                }

                count++;
            }
        }
    } else alert('Não foi possível executar esta operação');

    /*Modifica a imagem do "tipo de informação" clicado para a imagem do hifen (-)*/
    control.src = "inc/img/pontos/" + img.substring(0, 1) + "/vazio.png";
    MarcaSelecionar();
    document.getElementById("cphCorpo_ctl01_lblTotalPontos").innerText = Number(document.getElementById("cphCorpo_ctl01_lblTotalPontos").innerText) - count;
    /*Modifica a imagem do "tipo de informação" clicado para a imagem do ponto padrão por "tipo de informação"*/
}

function MarcaSelecionar() {
    /*INICIO - CONTROLAR O COMPONENTE "Selecionar" */
    /*Ref. para varrer as imagens da tabela: http://forum.imasters.com.br/topic/375419-contar-numero-de-elementos-inputs-dentro-de-uma-tabela/ */
    var table = document.getElementById("tblLegReferencias");
    var imgs = table.getElementsByTagName("img");
    var cntSel = 0;
    
    for (var i = 1; i < imgs.length; i++) {
        var src = imgs[i].src.toLocaleLowerCase();
        //if (src.indexOf("nd.png") >= 0)
        //alert('src: ' + src + ' - src.indexOf(vazio.png): ' + src.indexOf("vazio.png"));
        if (src.indexOf("vazio.png") >= 0)
            cntSel++;
    }

    //alert(cntSel + ' - ' + (table.getElementsByTagName("img").length - 1));
    if (cntSel === 0) {
        document.getElementById("imgSel").src = "inc/img/pontos/Sel.png";
    }
    else if (cntSel === (table.getElementsByTagName("img").length - 1)) {
        document.getElementById("imgSel").src = "inc/img/pontos/SelVazio.png";

    } else {
        document.getElementById("imgSel").src = "inc/img/pontos/SelNd.png";
    }
}

//function AddItem(category, marker, item) {
function AddItem(category, objEstacao, item) {
    var lst = document.getElementById("cphCorpo_ctl01_lstEstacoes");
    var x = 0;

    if (item.toLowerCase().indexOf("mapa") != -1) {
        do {
            if (objEstacao.EstCodigo == lst.options[x].value)
                lst.options[x].style.display = "block";
            x++;
        }
        while (x < lst.options.length);

    } else if (item.toLowerCase().indexOf("dados") != -1) {

        var hdf = objEstacao.getElementsByTagName('input')[1];
        var idOrigem = "";
        if (hdf.id.indexOf("hdfOrigem") >= 0)
            idOrigem = hdf.value;

        var it = idOrigem + ' - ' + objEstacao.cells[2].innerHTML + ' - ' + objEstacao.cells[3].innerHTML;
        do {
            if (it == lst.options[x].text)
                lst.options[x].style.display = "block";
            x++;
        }
        while (x < lst.options.length);
    }




    //////Codigo antigo. Apagar depois.
    ////var opt = document.createElement("option");
    ////if (item.toLowerCase().indexOf("mapa") != -1)
    ////{
    ////    //opt.text = objEstacao.IdOr + ' - ' + objEstacao.Codigo.substring(0, 8) + ' - ' + objEstacao.NomeEst;
    ////    //opt.value = objEstacao.EstCodigo;

    ////    var lst = document.getElementById("cphCorpo_ctl01_lstEstacoes");
    ////    var x = 0;
    ////    do {
    ////        if (objEstacao.EstCodigo == lst.options[x].value)
    ////            lst.options[x].style.display = "block";
    ////        x++;
    ////    }
    ////    while (x < lst.options.length);

    ////} else if (item.toLowerCase().indexOf("dados") != -1) {

    ////    var inputs = objEstacao.getElementsByTagName('input');
    ////    var idOrigem;
    ////    for (i = 0; i < inputs.length; i++) {
    ////        if (inputs[i].type == 'hidden') {
    ////            if (inputs[i].id.indexOf("hdfOrigem") >= 0)
    ////                idOrigem = inputs[i].value;// alert(inputs[i].value + ' - ' + inputs[i].id);
    ////        }
    ////    }
    ////    opt.text = idOrigem + ' - ' + objEstacao.cells[2].innerHTML + ' - ' + objEstacao.cells[3].innerHTML;
    ////    //opt.value = "";//marker.EstCodigo; //Se necessário, passar o ESTCODIGO da estação.
    ////}
    ////document.getElementById("cphCorpo_ctl01_lstEstacoes").options.add(opt);
}

// Descontinuado
function checkInGridView(imgControl) {
    alert('checkInGridView(imgControl): APAGAR');
    return false;
    var element = $("img[data-name='check']");
    var countVazios;
    var img = imgControl.src.split('/');

    element[0].src = "inc/img/pontos/SelNd.png";
    if (imgControl.getAttribute("ID").indexOf("imgUnico") >= 0) {
        imgControl.src = (img[img.length - 1].indexOf("SelVazio.png") >= 0) ? "inc/img/pontos/Sel.png" : "inc/img/pontos/SelVazio.png";
    }

    for (var x = 0; x < element.length; x++) {
        var idxImg = element[x].src.split('/');

        if (imgControl.getAttribute("ID").indexOf("imgAll") >= 0) {
            element[x].src = (img[img.length - 1].indexOf("SelVazio.png") >= 0 || img[img.length - 1].indexOf("SelNd.png") >= 0) ? "inc/img/pontos/Sel.png" : "inc/img/pontos/SelVazio.png";
        } else {
            if (x === 0) { countVazios = 0; continue; } //Desconsidera o primeiro elemento (Cabeçalho)
            countVazios = (idxImg[idxImg.length - 1].indexOf("SelVazio.png")) >= 0 ? countVazios + 1 : countVazios;
        }
    }
    //Marca ou desmarca o checkAll
    if (countVazios === 0)
        element[0].src = "inc/img/pontos/Sel.png";
    if (countVazios === element.length - 1)
        element[0].src = "inc/img/pontos/SelVazio.png";


    //element[0].setAttribute("data-src", element[0].src);

    //for (var x = 0; x < element[0].attributes.length; x++)
    //    alert(element[0].attributes[x].name);

    //alert(element[0].getAttribute("data-src"));
}


////// Function para setar a mensagem de SelectAll (link: Selecionar todas as XX medições do período selecionado?)
////function setSelectAll() {

////    if (document.getElementById('cphCorpo_hdfMsgSelectAll').value === "true") {
////        document.getElementById('divSelectAll').style.display = "none";
////        document.getElementById('cphCorpo_hdfMsgSelectAll').value = "false";
////        return false;
////    }

////    var vrTotal = document.getElementById('cphCorpo_lnkMsgSelectAll').text.replace("Selecionar todas as ", "");
////    vrTotal = vrTotal.replace(" medições do período selecionado?", "");

////    document.getElementById('cphCorpo_lblMsgSelectAll').innerHTML = "Todas as <b>" + vrTotal + "</b> medições desta página estão selecionadas.";
////    document.getElementById('cphCorpo_lnkMsgSelectAll').text = "Limpar seleção?";
////    document.getElementById('cphCorpo_hdfMsgSelectAll').value = "true";
////}


function selectInGraficGridView(dtDado, dtDadoIni, dtDadoFim) {
    alert('selectInGraficGridView(dtDado, dtDadoIni, dtDadoFim): APAGAR');
    return false;
    var table = document.getElementById("cphCorpo_gdDados");

    if (dtDadoIni == "" && dtDadoFim == "") {
        dtDadoIni = dtDadoFim = dtDado;
    }

    //var inputList = table.getElementsByTagName("input");
    dtDadoFim = (dtDadoFim == null || dtDadoFim == " ") ? dtDadoIni : dtDadoFim;

    for (var x = 0; x < table.rows.length; x++) {

        var inputList = table.rows[x].getElementsByTagName("input");
        var check = null;
        for (var i = 0; i < inputList.length; i++) 
            if (inputList[i].type === "checkbox" && inputList[i].id !== "cphCorpo_gdDados_ckbUnico_0") {
                check = inputList[i];
                
            if (check != null)
               break;
        }
        if (check == null)
            continue;

        var dtRow = table.rows[x].cells[1].innerText;
        check.checked = false;
        table.rows[x].cells[1].style.background = "";

        if (dtDadoIni != null && dtDadoFim != null) {
            if (dtRow >= dtDadoIni + ":00" && dtRow <= dtDadoFim + ":00") {
                check.checked = true;
                table.rows[x].cells[1].style.background = "#C0C0C0";
            }
        }
    }
}


function selectInGrafic(event, chkIntervalo, arrDateHour) {
    alert('selectInGrafic(event, chkIntervalo, arrDateHour): APAGAR');
    return false;
    var dtDadoIni = null;
    var dtDadoFim = null;
    //var dataSelected = event.item.category;
    //var chartDataGraf = event.chart.chartCursor.data;
    var chartDataGraf;
    var dataSelected = "";
    var bulletGraphics;

    //var arrDrHr = false;
    //for (var x = 0; x < arrDateHour.length; x++) {
    //    arrDateHour[x].style.borderColor = "";
    //    if (arrDateHour[x].value == "") {
    //        arrDateHour[x].style.borderColor = "#FF0000";
    //        arrDrHr = true;
    //    }
    //}
    //if (arrDrHr == true)
    //    return false;

    if (event.item == null) {

        //if (arrDateHour[0].value == "") {
        //    arrDateHour[1].value = "";
        //    return false;
        //} else 

        //if (arrDateHour[2].value == "") {
        //    arrDateHour[3].value = "";
        //    return false;
        //}

        if (arrDateHour[0].value != "") {
            dataSelected = new Date(arrDateHour[0].value.substr(6, 10), arrDateHour[0].value.substr(3, 2) - 1, arrDateHour[0].value.substr(0, 2),
                                arrDateHour[1].value.substr(0, 2), arrDateHour[1].value.substr(3, 2));
        }

        ////dataSelected = new Date(arrDateHour[0].value + ' ' + arrDateHour[1].value); //arrDateHour[0].value + ' ' + arrDateHour[1].value;
        //dataSelected = new Date(arrDateHour[0].value.substr(6, 10), arrDateHour[0].value.substr(3, 2) - 1, arrDateHour[0].value.substr(0, 2),
        //                        arrDateHour[1].value.substr(0, 2), arrDateHour[1].value.substr(3, 2));

        chartDataGraf = chart.chartData;
    } else {
        dataSelected = event.item.category; //.format("yyyy-MM-dd HH:mm");
        chartDataGraf = event.chart.chartCursor.data;
        bulletGraphics = event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics;
    }

    if (chkIntervalo.checked) { // Seleção por série, considerando a menor e a maior data selecionada.
        // Redefine o padrão
        for (var i = 0; i < chartDataGraf.length; i++) {

            if (bulletGraphics == null) {
                chartDataGraf[i].axes.nivelAxis.graphs.g1.graph.bulletColorR = "#000000";
                //chartDataGraf[i].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
                //chartDataGraf[i].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
            } else {
                event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
                event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
            }
            
            //chartDataGraf[i].axes.nivelAxis.graphs.g1.lineColor = "#FF0000";
            //chartDataGraf[i].axes.nivelAxis.graphs.g1.color = "#FF0000";
            //chartDataGraf[i].axes.nivelAxis.graphs.g1.lineColor = "#FF0000";
            
            //event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
            //event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
            //event.chart.chartCursor.data[i].axes.nivelAxis.graphs.g1.lineColor = "#000000";
            //event.chart.chartCursor.data[i].axes.nivelAxis.graphs.g1.color = "#000000";
            //event.chart.chartCursor.data[i].axes.nivelAxis.graphs.g1.lineColor = "#000000";
        }

        //var dtDadoIni = null;
        //var dtDadoFim = null;
        //var dataSelected = event.item.category;

        //var txtDataInicial = document.getElementById('cphCorpo_txtDataInicial');
        var txtDataInicial = arrDateHour[0];
        var txtHoraInicial = arrDateHour[1];
        var txtDataFinal = arrDateHour[2];
        var txtHoraFinal = arrDateHour[3];

        var dataSelecedAux;
        if (txtDataInicial.value != "") {
            //if (event.item.category.format("yyyy-MM-dd HH:mm") <= formatDate(txtDataInicial.value + ' ' + txtHoraInicial.value)) {
            //    txtDataInicial.value = event.item.category.format("dd/MM/yyyy");
            //    txtHoraInicial.value = event.item.category.format("HH:mm");
            //}
            if (dataSelected.format("yyyy-MM-dd HH:mm") <= formatDate(txtDataInicial.value + ' ' + txtHoraInicial.value)) {
                txtDataInicial.value = dataSelected.format("dd/MM/yyyy");
                txtHoraInicial.value = dataSelected.format("HH:mm");
            }
            dataSelecedAux = formatDate(txtDataInicial.value + ' ' + txtHoraInicial.value);

            //if (dataSelected.format("yyyy-MM-dd HH:mm") > dataSelecedAux) {
            //    txtDataFinal.value = event.item.category.format("dd/MM/yyyy");
            //    txtHoraFinal.value = event.item.category.format("HH:mm");
            //}
            if (dataSelected.format("yyyy-MM-dd HH:mm") > dataSelecedAux) {
                txtDataFinal.value = dataSelected.format("dd/MM/yyyy");
                txtHoraFinal.value = dataSelected.format("HH:mm");
            }
        } else {
            //dtDadoIni = dataSelected.format("dd/MM/yyyy HH:mm");
            //dtDadoIni = dataSelected;
            txtDataInicial.value = dataSelected.format("dd/MM/yyyy");
            txtHoraInicial.value = dataSelected.format("HH:mm");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
        }

        //if (txtDataInicial.value != "" && txtDataFinal.value != "") {
        if (txtDataInicial.value != "") {
            if (dataSelected.format("yyyy-MM-dd HH:mm") >= dataSelecedAux) {
                for (var i = 0; i < chartDataGraf.length; i++) {
                    var chartItem = chartDataGraf[i];

                    //if (bulletGraphics == null) {
                    //    chartDataGraf[i].axes.nivelAxis.graphs.g1.graph.bulletColorR = "#FF0000";
                    //    //chartDataGraf[i].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
                    //    //chartDataGraf[i].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
                    //} else {
                    //    event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
                    //    event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
                    //}

                    if (chartItem.axes.nivelAxis.graphs.g1.bulletGraphics == null)
                        continue;

                    if (chartItem.category.format("yyyy-MM-dd HH:mm") >= formatDate(txtDataInicial.value + ' ' + txtHoraInicial.value) && chartItem.category.format("yyyy-MM-dd HH:mm") <= formatDate(txtDataFinal.value + ' ' + txtHoraFinal.value)) {
                        chartItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
                        chartItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
                        chartItem.axes.nivelAxis.graphs.g1.graph.lineColorR = "#FF0000";
                        chartItem.axes.nivelAxis.graphs.g1.bulletColor = "#FF0000";
                        chartItem.axes.nivelAxis.graphs.g1.lineColor = "#FF0000";
                        chartItem.axes.nivelAxis.graphs.g1.color = "#FF0000";
                    } else if (chartItem.category.format("yyyy-MM-dd HH:mm") > formatDate(txtDataFinal.value + ' ' + txtHoraFinal.value)) {
                        chartItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
                        chartItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
                        chartItem.axes.nivelAxis.graphs.g1.graph.lineColorR = "#000000";
                        chartItem.axes.nivelAxis.graphs.g1.bulletColor = "#000000";
                        chartItem.axes.nivelAxis.graphs.g1.lineColor = "#000000";
                        chartItem.axes.nivelAxis.graphs.g1.color = "#000000";
                    }
                }
            }
        }
        dtDadoIni = txtDataInicial.value + ' ' + txtHoraInicial.value;
        dtDadoFim = txtDataFinal.value + ' ' + txtHoraFinal.value;
        selectInGraficGridView(dataSelected.format("dd/MM/yyyy HH:mm:00"), dtDadoIni, dtDadoFim);
    } else {
        // Trata os pontos fazendo a seleção individual 
        if (event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.attributes["stroke"].value == "#FF0000") {
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
        } else {
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
        }
        //selectInGraficGridView(dataSelected.format("dd/MM/yyyy HH:mm"), "", "");
        selectInGraficGridView(dataSelected, "", "");
    }

    //checkBoxInGridView(null, document.getElementById('cphCorpo_gdDados_CheckBox1_0')); //cphCorpo_gdDados_imgAll
    //selectInGraficGridView(formatDate(txtDataInicial.value), dtDadoIni, dtDadoFim);
    //selectInGraficGridView(dataSelected.format("dd/MM/yyyy HH:mm:00"), dtDadoIni, dtDadoFim);
}



/*****INI SELECT ITENS***************/
function setDataHoraInicialFinal(dtHrInicial, dtHrFinal, dtHrSelected) {
    if (dtHrInicial === "") {
        dtHrInicial = dtHrSelected;
    } else if (dtHrFinal !== "") {
        dtHrFinal = dtHrSelected;
    }
}
function selectInTextBox() {

    selectInGrid();
    selectInGraf();
}
function selectInGrid() {
    selectInTextBox();
    selectInGrid();
}
function selectInGraf(event, chkIntervalo, arrDateHour) {

    var dataHoraSelected = event.item.category; //.format("yyyy-MM-dd HH:mm");

    if (chkIntervalo.checked) { // Seleção por série, considerando a menor e a maior data selecionada.
        // Redefine o padrão
        for (var i = 0; i < chartDataGraf.length; i++) {
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
            //event.chart.chartCursor.data[i].axes.nivelAxis.graphs.g1.lineColor = "#000000";
            //event.chart.chartCursor.data[i].axes.nivelAxis.graphs.g1.color = "#000000";
            //event.chart.chartCursor.data[i].axes.nivelAxis.graphs.g1.lineColor = "#000000";
        }

        //var txtDataInicial = document.getElementById('cphCorpo_txtDataInicial');
        var txtDataInicial = arrDateHour[0];
        var txtHoraInicial = arrDateHour[1];
        var txtDataFinal = arrDateHour[2];
        var txtHoraFinal = arrDateHour[3];

        var dataSelecedAux;

        setDataHoraInicialFinal(dtHrInicial, dtHrFinal, dtHrSelected);

        if (txtDataInicial.value === "") {
            txtDataInicial.value = dataSelected.format("dd/MM/yyyy");
            txtHoraInicial.value = dataSelected.format("HH:mm");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
        }




        if (txtDataInicial.value !== "") {

            if (dataSelected.format("yyyy-MM-dd HH:mm") <= formatDate(txtDataInicial.value + ' ' + txtHoraInicial.value)) {
                txtDataInicial.value = dataSelected.format("dd/MM/yyyy");
                txtHoraInicial.value = dataSelected.format("HH:mm");
            }
            dataSelecedAux = formatDate(txtDataInicial.value + ' ' + txtHoraInicial.value);

            //if (dataSelected.format("yyyy-MM-dd HH:mm") > dataSelecedAux) {
            //    txtDataFinal.value = event.item.category.format("dd/MM/yyyy");
            //    txtHoraFinal.value = event.item.category.format("HH:mm");
            //}
            if (dataSelected.format("yyyy-MM-dd HH:mm") > dataSelecedAux) {
                txtDataFinal.value = dataSelected.format("dd/MM/yyyy");
                txtHoraFinal.value = dataSelected.format("HH:mm");
            }
        } else {
            //dtDadoIni = dataSelected.format("dd/MM/yyyy HH:mm");
            //dtDadoIni = dataSelected;
            txtDataInicial.value = dataSelected.format("dd/MM/yyyy");
            txtHoraInicial.value = dataSelected.format("HH:mm");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
        }

        //if (txtDataInicial.value != "" && txtDataFinal.value != "") {
        if (txtDataInicial.value != "") {
            if (dataSelected.format("yyyy-MM-dd HH:mm") >= dataSelecedAux) {
                for (var i = 0; i < chartDataGraf.length; i++) {
                    var chartItem = chartDataGraf[i];

                    //if (bulletGraphics == null) {
                    //    chartDataGraf[i].axes.nivelAxis.graphs.g1.graph.bulletColorR = "#FF0000";
                    //    //chartDataGraf[i].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
                    //    //chartDataGraf[i].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
                    //} else {
                    //    event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
                    //    event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
                    //}

                    if (chartItem.axes.nivelAxis.graphs.g1.bulletGraphics == null)
                        continue;

                    if (chartItem.category.format("yyyy-MM-dd HH:mm") >= formatDate(txtDataInicial.value + ' ' + txtHoraInicial.value) && chartItem.category.format("yyyy-MM-dd HH:mm") <= formatDate(txtDataFinal.value + ' ' + txtHoraFinal.value)) {
                        chartItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
                        chartItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
                        chartItem.axes.nivelAxis.graphs.g1.graph.lineColorR = "#FF0000";
                        chartItem.axes.nivelAxis.graphs.g1.bulletColor = "#FF0000";
                        chartItem.axes.nivelAxis.graphs.g1.lineColor = "#FF0000";
                        chartItem.axes.nivelAxis.graphs.g1.color = "#FF0000";
                    } else if (chartItem.category.format("yyyy-MM-dd HH:mm") > formatDate(txtDataFinal.value + ' ' + txtHoraFinal.value)) {
                        chartItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
                        chartItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
                        chartItem.axes.nivelAxis.graphs.g1.graph.lineColorR = "#000000";
                        chartItem.axes.nivelAxis.graphs.g1.bulletColor = "#000000";
                        chartItem.axes.nivelAxis.graphs.g1.lineColor = "#000000";
                        chartItem.axes.nivelAxis.graphs.g1.color = "#000000";
                    }
                }
            }
        }
        dtDadoIni = txtDataInicial.value + ' ' + txtHoraInicial.value;
        dtDadoFim = txtDataFinal.value + ' ' + txtHoraFinal.value;
        selectInGraficGridView(dataSelected.format("dd/MM/yyyy HH:mm:00"), dtDadoIni, dtDadoFim);
    } else {
        // Trata os pontos fazendo a seleção individual 
        if (event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.attributes["stroke"].value == "#FF0000") {
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#000000");
        } else {
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
            event.item.serialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
        }
        //selectInGraficGridView(dataSelected.format("dd/MM/yyyy HH:mm"), "", "");
        //selectInGraficGridView(dataSelected, "", "");
    }


    selectInTextBox();
    selectInGraf();
}
/*****FIM SELECT ITENS***************/


/*****INI COMPONENTE CALENDAR***************/
function changeSelectedDates() {
    //chart.Item.SerialDataItem.axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#000000");
    var chartData = chart.chartData;
    for (var x = 0; x < chartData.length; x++) {

        var dt = chartData[x].category.format("dd/MM/yyyy HH:mm");

        //chartData[x].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF8C00");
        //chartData[x].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF8C00");

        if (dt == "01/02/2017 12:00") {
            //chartData[x].dataContext.bulletColor = "#FF0000";
            chartData[x].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
            chartData[x].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
        }
        if (dt == "01/02/2017 10:00") {
            //chartData[x].dataContext.bulletColor = "#FF0000";
            chartData[x].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
            chartData[x].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
        }
        if (dt == "01/02/2017 13:30") {
            //chartData[x].dataContext.bulletColor = "#FF0000";
            chartData[x].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("stroke", "#FF0000");
            chartData[x].axes.nivelAxis.graphs.g1.bulletGraphics.node.setAttribute("fill", "#FF0000");
        }
    }
}
function SetDateHour(ctr) {
    //var date = new Date().format("dd/MM/yyyy"); //new Date().format("dd/MM/yyyy HH:mm:ss");
    ////    document.getElementById("cphCorpo_gdDados_txtHora_0").focus();
    if (ctr._selectedDate > new Date()) {

        alert("Você não pode selecionar uma data superior a atual!");
        ctr._selectedDate = new Date();

        // seleciona a data atual novamente
        ctr._textbox.set_Value(ctr._selectedDate.format(ctr._selectedDate.format("dd/MM/yyyy")));

        ctr.calendar.endDate = "14/07/2015";
        ctr.Date.disabled();

    }
    ctr._selectedDate = new Date();//.format("dd/MM/yyyy");
    document.getElementById("cphCorpo_txtHora").focus();
}
function checkDate(sender, args) {
    if (sender._selectedDate < new Date()) {
        alert("Você não pode selecionar uma data passada!");
        sender._selectedDate = new Date().getUTCDate();
        // seleciona a data atual novamente
        sender._textbox.set_Value(sender._selectedDate.format(sender._format));
    }
}
/*****FIM COMPONENTE CALENDAR***************/


/*****INICIO - MASCARA / VALIDAÇÃO CAMPOS TEXTBOX***************/
function FormataHora(ctl, evt) {
    var hr = ctl.value;
    if (hr === ":") {
        ctl.value = "00:";
        return true;
    }
    hr = somenteNumero(ctl.value);
    if (hr.length >= 3)
        ctl.value = hr.substr(0, 2) + ":" + hr.substr(2, 2);

    if (ctl.value.length == 5)
        VerificaHora(ctl);

    return true;
}
function VerificaHora(campo) {
    var estado = "";
    var hr = campo.value.split(":");
    if ((hr[0] < 00) || (hr[0] > 23)) {
        estado = "Hora inválida!";
    }
    if ((hr[1] < 00) || (hr[1] > 59)) {
        estado = estado != "" ? estado + "\n" : "";
        estado = estado + "Minuto inválido!";
    }
    if (estado != "") {
        alert(estado);
        campo.focus();
    }
}

function FormataData(ctl, evt) {
    var dt = somenteNumero(ctl.value);

    if (dt.length == 3) {
        dt = dt.substr(0, 2) + "/" + dt.substr(2, 2);
    } else if (dt.length >= 5)
        dt = dt.substr(0, 2) + "/" + dt.substr(2, 2) + "/" + dt.substr(4, 4);
    else {
        dt = ctl.value;
    }
    var msg = "";

    if (dt.length == 10) {
        ctl.value = dt;
        msg = validaData(ctl);
    }

    if (msg != "") {
        alert(msg);
        return false;
    }

    ctl.value = dt;
    return true;
}
function validaData(val_data) {
    var msg = "";
    val_data.value = val_data.value.replace('= ', '');
    if (val_data.value != "") {
        var var_data = val_data.value;
        var var_dia = var_data.substring(0, 2);
        var var_mes = var_data.substring(3, 5);
        var var_ano = var_data.substring(6, 10);

        for (i = 0; i <= var_data.length; i++) {
            if (var_data.substring(i, i + 1) == " ") {
                msg = "Digite a \"data\" no formato DD\/MM\/AAAA.";
            }
        }
        if (val_data.value.length < 10) {
            msg = "Digite a \"data\" no formato DD\/MM\/AAAA.";
        }
        if (val_data.value.length > 10) {
            msg = "Digite a \"data\" no formato DD\/MM\/AAAA.";
        }
        if (var_data.substring(2, 3) != "\/") {
            msg = "Digite a \"data\" no formato DD\/MM\/AAAA.";
        }
        if (var_data.substring(5, 6) != "\/") {
            msg = "Digite a \"data\" no formato DD\/MM\/AAAA.";
        }
        if (isNaN(var_ano)) {
            msg = "O \"ano\" da data não é numérico.";
        }
        if (var_ano < 1900) {
            msg = "O \"ano\" da data é inferior a 1900.";
        }
        if (isNaN(var_mes)) {
            msg = "O \"mês\" da data não é numérico.";
        }
        if ((var_mes < 1) || (var_mes > 12)) {
            msg = "O \"mês\" da data não é válido.";
        }
        if (isNaN(var_dia)) {
            msg = "O \"dia\" da data não é numérico.";
        }
        if ((var_mes == 1) || (var_mes == 3) || (var_mes == 5) || (var_mes == 7) || (var_mes == 8) || (var_mes == 10) || (var_mes == 12)) {
            if ((var_dia < 1) || (var_dia > 31)) {
                msg = "O \"dia\" da data não é válido para o mês.";
            }
        }
        if ((var_mes == 4) || (var_mes == 6) || (var_mes == 9) || (var_mes == 11)) {
            if ((var_dia < 1) || (var_dia > 30)) {
                msg = "O \"dia\" da data não é válido para o mês.";
            }
        }
        if (var_mes == 2) {
            if ((var_dia < 1) || (var_dia > 29)) {
                msg = "O \"dia\" da data não é válido para o mês.";
            }
        }
    }
    return msg;
}


function somenteNumero(str) {
    str = str.toString();
    return str.replace(/\D/g, '');
}

function formatMascara(controle, mascara, tpCampo) {
    var tpCampoValida = tpCampo;
    controle.style.borderColor = "";
    var msgReturn = "";
    switch (tpCampo.toLowerCase()) {
        case 'numeric':
            controle.value = somenteNumero(controle.value);
            break;
        case 'decimal':
            const numero = controle.value.replace(',', '.').replace(/[^0-9\.]/g, "");
            controle.value = numero.replace('.',',');
            return;
        case 'date':
            var num = somenteNumero(controle.value);
            if (controle.value.length == 10) {
                msgReturn = validaData(controle);
                if (msgReturn != "") {
                    document.write(msgReturn);
                    controle.style.borderColor = "#FF0000";
                    controle.focus();
                }
            }
            controle.value = num;
            break;
        case 'hora':
            var num = somenteNumero(controle.value);
            if (controle.value.length == 10) {
                msgReturn = validaHora(controle);
                if (msgReturn != "") {
                    document.write(msgReturn);
                    controle.style.borderColor = "#FF0000";
                    controle.focus();
                }
            }
            controle.value = num;
            break;
        case 'fone':
            controle.value = controle.value.replace(/\D/g, "");                                 //Remove tudo o que não é dígito
            controle.value = controle.value.replace(/^(\d{2})(\d)/g, "($1)$2");                 //Coloca parênteses em volta dos dois primeiros dígitos
            if(controle.value.length<13)
                controle.value = controle.value.replace(/(\d)(\d{4})$/, "$1-$2");               //Coloca hífen entre o quarto e o quinto dígitos
            else
                controle.value = controle.value.replace(/(\d{1})(\d{4})(\d{4})$/, "$1.$2-$3");  //Coloca o ponto do nono digito mais o hífen entre o quarto e o quinto dígitos

            return controle.value;
            break;
        case 'text':
            controle.value = controle.value;
            break;
        default:
            return controle.value;
    }

    //transformar mascara
    var mask = new String(mascara);
    var novamask = "";
    var subst = /#/g;
    var novovalor = new String(controle.value);
    var nvalor = new String("");

    tammask = mask.length;

    nvalor = "";
    for (i = 0; i < tammask; i++) {
        tx = novovalor.charAt(i);
        if (testacarac(tx) == "B") {
            nvalor = nvalor + tx;
        }
    }

    var valor = new String(nvalor);
    tamvalor = valor.length;
    novamask = mask.replace(subst, "_");
    //transformar mascara e numero em array

    var arrmask = new Array();
    var i = 1;

    var arrvalor = new Array();

    for (i = 0; i < tammask; i++) {
        tx = novamask.charAt(i);
        arrmask[i] = tx;
    }

    for (i = 0; i < tamvalor; i++) {
        tx = valor.charAt(i);
        arrvalor[i] = tx;
    }

    contval = 0;
    cont = 0;
    var novoArr = new Array();

    //Preencher array com os resultados
    for (j = 0; j < tammask; j++) {
        tx = arrmask[j];
        if (tx != '(' && tx != ')' && tx != '.' && tx != '/' && tx != '-' && tx != ':' && contval < tamvalor) {
            arrmask[cont] = arrvalor[contval];
            contval = contval + 1;
            cont = cont + 1;
        }
        else {
            cont = cont + 1;
        }
    }
    var res = "";
    cont = 0
    for (j = 0; j < tammask; j++) {
        if (testacarac(arrmask[j]) == "B") { cont = cont + 1; }
        if (cont <= tamvalor) {
            res = res + arrmask[j];
            if (cont == tamvalor) { cont = 1000 }
        }
    }

    if (res == '_')
        res = '';

    controle.value = res;
}

function testacarac(car) {
    if (car == '(' || car == ')' || car == '.' || car == '/' || car == '-' || car == '_' || car == ':') {
        rest = "A";
        return (rest);
    }
    else { rest = "B"; return (rest); }
}



function soNumero(str) {
    str = str.toString();
    return str.replace(/\D/g, '');
}




// INICIO FUNÇÃO DE MASCARA MAIUSCULA
function maiuscula(ctr) {
    ctr.value = ctr.value.toUpperCase();
}
function minuscula(ctr) {
    ctr.value = ctr.value.toLowerCase();
}
//FIM DA FUNÇÃO MASCARA MAIUSCULA

