
function setUpMapa()
{

	$("#divMapaLayer").dialog(
			{
				height: 235,
				width: 120,
				autoOpen: false,
				modal: false,
				show : "blind",
				buttons: {
					"Fechar" : function()
					{
						closeMapa();
					}
				},
				close : function(event,ui){ panel_marcadores = false }
			}
		);

	 $.get("telas/spatials/mapas/mapa.jsp",
			function(data)
			{
				$("#divMapaLayer").html( data );
				checkMap();
				$("#divMapaLayer").dialog( "option", "position", [260,45] );
				$("#radioMap").buttonset();

			});
}


function closeMapa(){
	 hideAll();
	$("#divMapaLayer").dialog("close");
}

function abreMapa()
{
	setUpMapa();
	//$("#divMapaLayer").dialog( "option", "position", [eventMouse.pageX,eventMouse.pageY] );
	$("#divMapaLayer").dialog( "option", "position", [450,45] );
	$("#divMapaLayer").dialog("open");

}
function checkMap(){

	switch (map.baseLayer.type) {
	case "roadmap":
		$("#radio2").attr('checked','checked');
		$("#radio2").click();
		break;
	case "satellite":
		$("#radio3").attr('checked','checked');
		$("#radio3").click();
		break;
	case "terrain":
		$("#radio4").attr('checked','checked');
		$("#radio4").click();
		break;
	case "hybrid":
		$("#radio5").attr('checked','checked');
		$("#radio5").click();
		break;
	}

}
