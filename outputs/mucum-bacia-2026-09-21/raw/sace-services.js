// Provide a default path to dwr.engine
if (typeof this['dwr'] == 'undefined') this.dwr = {};
if (typeof dwr['engine'] == 'undefined') dwr.engine = {};
if (typeof dwr.engine['_mappedClasses'] == 'undefined') dwr.engine._mappedClasses = {};

if (window['dojo']) dojo.provide('dwr.interface.FonteDadosService');

if (typeof this['FonteDadosService'] == 'undefined') FonteDadosService = {};

FonteDadosService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FonteDadosService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FonteDadosService._path, 'FonteDadosService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConfiguracaoConexaoService');

if (typeof this['ConfiguracaoConexaoService'] == 'undefined') ConfiguracaoConexaoService = {};

ConfiguracaoConexaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoConexaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoConexaoService._path, 'ConfiguracaoConexaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoConexaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoConexaoService._path, 'ConfiguracaoConexaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoConexaoService.findById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoConexaoService._path, 'ConfiguracaoConexaoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoConexaoService.save = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoConexaoService._path, 'ConfiguracaoConexaoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoConexaoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoConexaoService._path, 'ConfiguracaoConexaoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoConexaoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoConexaoService._path, 'ConfiguracaoConexaoService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoConexaoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoConexaoService._path, 'ConfiguracaoConexaoService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.GeoJsonService');

if (typeof this['GeoJsonService'] == 'undefined') GeoJsonService = {};

GeoJsonService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {function|Object} callback callback function or options object
 */
GeoJsonService.getMonitoringPointsGeoJsonSemFiltro = function(callback) {
  return dwr.engine._execute(GeoJsonService._path, 'GeoJsonService', 'getMonitoringPointsGeoJsonSemFiltro', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
GeoJsonService.getMonitoringPointsGeoJson = function(callback) {
  return dwr.engine._execute(GeoJsonService._path, 'GeoJsonService', 'getMonitoringPointsGeoJson', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
GeoJsonService.getBounds = function(callback) {
  return dwr.engine._execute(GeoJsonService._path, 'GeoJsonService', 'getBounds', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.LogAgendamentoEntradaService');

if (typeof this['LogAgendamentoEntradaService'] == 'undefined') LogAgendamentoEntradaService = {};

LogAgendamentoEntradaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
LogAgendamentoEntradaService.deleteById = function(p0, callback) {
  return dwr.engine._execute(LogAgendamentoEntradaService._path, 'LogAgendamentoEntradaService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
LogAgendamentoEntradaService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(LogAgendamentoEntradaService._path, 'LogAgendamentoEntradaService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
LogAgendamentoEntradaService.findById = function(p0, callback) {
  return dwr.engine._execute(LogAgendamentoEntradaService._path, 'LogAgendamentoEntradaService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
LogAgendamentoEntradaService.deleteAll = function(callback) {
  return dwr.engine._execute(LogAgendamentoEntradaService._path, 'LogAgendamentoEntradaService', 'deleteAll', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
LogAgendamentoEntradaService.deleteByMedicaoBruta = function(p0, callback) {
  return dwr.engine._execute(LogAgendamentoEntradaService._path, 'LogAgendamentoEntradaService', 'deleteByMedicaoBruta', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
LogAgendamentoEntradaService.findAll = function(callback) {
  return dwr.engine._execute(LogAgendamentoEntradaService._path, 'LogAgendamentoEntradaService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
LogAgendamentoEntradaService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(LogAgendamentoEntradaService._path, 'LogAgendamentoEntradaService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
LogAgendamentoEntradaService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(LogAgendamentoEntradaService._path, 'LogAgendamentoEntradaService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ParametroService');

if (typeof this['ParametroService'] == 'undefined') ParametroService = {};

ParametroService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ParametroService._path, 'ParametroService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ParametroService._path, 'ParametroService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroService.findById = function(p0, callback) {
  return dwr.engine._execute(ParametroService._path, 'ParametroService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Parametro} p0 a param
 * @param {class java.util.ArrayList} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroService.saveParametro = function(p0, p1, callback) {
  return dwr.engine._execute(ParametroService._path, 'ParametroService', 'saveParametro', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Parametro} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroService.save = function(p0, callback) {
  return dwr.engine._execute(ParametroService._path, 'ParametroService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ParametroService._path, 'ParametroService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ParametroService._path, 'ParametroService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ParametroService._path, 'ParametroService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FonteAquisicaoDadosService');

if (typeof this['FonteAquisicaoDadosService'] == 'undefined') FonteAquisicaoDadosService = {};

FonteAquisicaoDadosService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.deleteById = function(p0, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.findById = function(p0, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'findById', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.findByPontoMonitoramento = function(p0, p1, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'findByPontoMonitoramento', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.findByPontoMonitoramento = function(p0, p1, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'findByPontoMonitoramento', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.FonteAquisicaoDados} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.save = function(p0, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'exportExcel', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p1 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p2 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.populateSelectParam = function(p0, p1, p2, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'populateSelectParam', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FonteAquisicaoDadosService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FonteAquisicaoDadosService._path, 'FonteAquisicaoDadosService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ModeloEmailService');

if (typeof this['ModeloEmailService'] == 'undefined') ModeloEmailService = {};

ModeloEmailService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloEmailService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ModeloEmailService._path, 'ModeloEmailService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloEmailService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ModeloEmailService._path, 'ModeloEmailService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloEmailService.findById = function(p0, callback) {
  return dwr.engine._execute(ModeloEmailService._path, 'ModeloEmailService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ModeloEmailService.findAll = function(callback) {
  return dwr.engine._execute(ModeloEmailService._path, 'ModeloEmailService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.ModeloEmail} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloEmailService.save = function(p0, callback) {
  return dwr.engine._execute(ModeloEmailService._path, 'ModeloEmailService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloEmailService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ModeloEmailService._path, 'ModeloEmailService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloEmailService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ModeloEmailService._path, 'ModeloEmailService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.BoletimDisseminacaoService');

if (typeof this['BoletimDisseminacaoService'] == 'undefined') BoletimDisseminacaoService = {};

BoletimDisseminacaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimDisseminacaoService.exportPdf = function(p0, callback) {
  return dwr.engine._execute(BoletimDisseminacaoService._path, 'BoletimDisseminacaoService', 'exportPdf', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimDisseminacaoService.exportBytePdf = function(p0, callback) {
  return dwr.engine._execute(BoletimDisseminacaoService._path, 'BoletimDisseminacaoService', 'exportBytePdf', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.ConfiguracaoEmailBoletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimDisseminacaoService.enviaBoletimEmail = function(p0, callback) {
  return dwr.engine._execute(BoletimDisseminacaoService._path, 'BoletimDisseminacaoService', 'enviaBoletimEmail', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.DecimalService');

if (typeof this['DecimalService'] == 'undefined') DecimalService = {};

DecimalService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
DecimalService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(DecimalService._path, 'DecimalService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.SensorTemplateGraficoService');

if (typeof this['SensorTemplateGraficoService'] == 'undefined') SensorTemplateGraficoService = {};

SensorTemplateGraficoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorTemplateGraficoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(SensorTemplateGraficoService._path, 'SensorTemplateGraficoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorTemplateGraficoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(SensorTemplateGraficoService._path, 'SensorTemplateGraficoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorTemplateGraficoService.findById = function(p0, callback) {
  return dwr.engine._execute(SensorTemplateGraficoService._path, 'SensorTemplateGraficoService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
SensorTemplateGraficoService.findAll = function(callback) {
  return dwr.engine._execute(SensorTemplateGraficoService._path, 'SensorTemplateGraficoService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.SensorTemplateGrafico} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorTemplateGraficoService.save = function(p0, callback) {
  return dwr.engine._execute(SensorTemplateGraficoService._path, 'SensorTemplateGraficoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorTemplateGraficoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(SensorTemplateGraficoService._path, 'SensorTemplateGraficoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorTemplateGraficoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(SensorTemplateGraficoService._path, 'SensorTemplateGraficoService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorTemplateGraficoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(SensorTemplateGraficoService._path, 'SensorTemplateGraficoService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.PermissaoService');

if (typeof this['PermissaoService'] == 'undefined') PermissaoService = {};

PermissaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PermissaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(PermissaoService._path, 'PermissaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PermissaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(PermissaoService._path, 'PermissaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PermissaoService.findById = function(p0, callback) {
  return dwr.engine._execute(PermissaoService._path, 'PermissaoService', 'findById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
PermissaoService.savePermissaoInList = function(p0, p1, callback) {
  return dwr.engine._execute(PermissaoService._path, 'PermissaoService', 'savePermissaoInList', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PermissaoService.findByGrupoUsuario = function(p0, callback) {
  return dwr.engine._execute(PermissaoService._path, 'PermissaoService', 'findByGrupoUsuario', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
PermissaoService.findAll = function(callback) {
  return dwr.engine._execute(PermissaoService._path, 'PermissaoService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.bean.Permissao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PermissaoService.save = function(p0, callback) {
  return dwr.engine._execute(PermissaoService._path, 'PermissaoService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.LayerService');

if (typeof this['LayerService'] == 'undefined') LayerService = {};

LayerService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {function|Object} callback callback function or options object
 */
LayerService.getLayers = function(callback) {
  return dwr.engine._execute(LayerService._path, 'LayerService', 'getLayers', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TemplateGraficoImagemService');

if (typeof this['TemplateGraficoImagemService'] == 'undefined') TemplateGraficoImagemService = {};

TemplateGraficoImagemService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoImagemService.findById = function(p0, callback) {
  return dwr.engine._execute(TemplateGraficoImagemService._path, 'TemplateGraficoImagemService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.TemplateGraficoImagem} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoImagemService.saveImagem = function(p0, callback) {
  return dwr.engine._execute(TemplateGraficoImagemService._path, 'TemplateGraficoImagemService', 'saveImagem', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoImagemService.removeImage = function(p0, callback) {
  return dwr.engine._execute(TemplateGraficoImagemService._path, 'TemplateGraficoImagemService', 'removeImage', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoImagemService.findAllByTemplateGraficoImagem = function(p0, callback) {
  return dwr.engine._execute(TemplateGraficoImagemService._path, 'TemplateGraficoImagemService', 'findAllByTemplateGraficoImagem', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.AnexoByteService');

if (typeof this['AnexoByteService'] == 'undefined') AnexoByteService = {};

AnexoByteService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AnexoByteService.downloadArquivoById = function(p0, callback) {
  return dwr.engine._execute(AnexoByteService._path, 'AnexoByteService', 'downloadArquivoById', arguments);
};

/**
 * @param {class com.coffey.cprm.persistence.BaseBean} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AnexoByteService.saveFiles = function(p0, callback) {
  return dwr.engine._execute(AnexoByteService._path, 'AnexoByteService', 'saveFiles', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.CurvaChaveService');

if (typeof this['CurvaChaveService'] == 'undefined') CurvaChaveService = {};

CurvaChaveService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.deleteByIdPontoCurvaChave = function(p0, callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'deleteByIdPontoCurvaChave', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.PontoCurvaChave} p0 a param
 * @param {class java.lang.Double} p1 a param
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.findByPontoCurvaChaveValorCota = function(p0, p1, callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'findByPontoCurvaChaveValorCota', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.PontoCurvaChave} p0 a param
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.findByPontoCurvaChave = function(p0, callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'findByPontoCurvaChave', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.PontoMonitoramento} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {class java.util.Date} p2 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p3 a param
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.findCurvaChaveViewByDataIniAndDataTer = function(p0, p1, p2, p3, callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'findCurvaChaveViewByDataIniAndDataTer', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.deleteById = function(p0, callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.findById = function(p0, callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.findAll = function(callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.CurvaChave} p0 a param
 * @param {function|Object} callback callback function or options object
 */
CurvaChaveService.save = function(p0, callback) {
  return dwr.engine._execute(CurvaChaveService._path, 'CurvaChaveService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TemplateService');

if (typeof this['TemplateService'] == 'undefined') TemplateService = {};

TemplateService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.Template} p0 a param
 * @param {class [B} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.recuperaPrimeiraLinhaDoArquivoPorTemplate = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'recuperaPrimeiraLinhaDoArquivoPorTemplate', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.deleteById = function(p0, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.findById = function(p0, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.Template} p0 a param
 * @param {boolean} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.saveTemplate = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'saveTemplate', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.Template} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.save = function(p0, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'populateSelect', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p1 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p2 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateService.populateSelectParam = function(p0, p1, p2, callback) {
  return dwr.engine._execute(TemplateService._path, 'TemplateService', 'populateSelectParam', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TesteFormatoNomeArquivoURLService');

if (typeof this['TesteFormatoNomeArquivoURLService'] == 'undefined') TesteFormatoNomeArquivoURLService = {};

TesteFormatoNomeArquivoURLService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TesteFormatoNomeArquivoURLService.testaFormatosNomesArquivos = function(p0, callback) {
  return dwr.engine._execute(TesteFormatoNomeArquivoURLService._path, 'TesteFormatoNomeArquivoURLService', 'testaFormatosNomesArquivos', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.MedicaoBrutaService');

if (typeof this['MedicaoBrutaService'] == 'undefined') MedicaoBrutaService = {};

MedicaoBrutaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.util.Date} p0 a param
 * @param {class com.coffey.cprm.medicao.crud.bean.Sensor} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.existeMedicaoParaDataHoraMedicaoESensor = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'existeMedicaoParaDataHoraMedicaoESensor', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.deleteById = function(p0, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.findById = function(p0, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'findById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.updateMedicoesList = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'updateMedicoesList', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Sensor} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.countByDataHoraMedicaoESensor = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'countByDataHoraMedicaoESensor', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.saveInList = function(p0, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'saveInList', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.MedicaoBruta} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.searchAndUpdate = function(p0, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'searchAndUpdate', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.MedicaoBruta} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.save = function(p0, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoBrutaService._path, 'MedicaoBrutaService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FormatoNomeArquivoService');

if (typeof this['FormatoNomeArquivoService'] == 'undefined') FormatoNomeArquivoService = {};

FormatoNomeArquivoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoNomeArquivoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(FormatoNomeArquivoService._path, 'FormatoNomeArquivoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoNomeArquivoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(FormatoNomeArquivoService._path, 'FormatoNomeArquivoService', 'deleteByIds', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.FormatoNomeArquivo} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoNomeArquivoService.save = function(p0, callback) {
  return dwr.engine._execute(FormatoNomeArquivoService._path, 'FormatoNomeArquivoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoNomeArquivoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(FormatoNomeArquivoService._path, 'FormatoNomeArquivoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoNomeArquivoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(FormatoNomeArquivoService._path, 'FormatoNomeArquivoService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoNomeArquivoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FormatoNomeArquivoService._path, 'FormatoNomeArquivoService', 'populateSelect', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p1 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p2 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoNomeArquivoService.populateSelectParam = function(p0, p1, p2, callback) {
  return dwr.engine._execute(FormatoNomeArquivoService._path, 'FormatoNomeArquivoService', 'populateSelectParam', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.EquacaoConversaoService');

if (typeof this['EquacaoConversaoService'] == 'undefined') EquacaoConversaoService = {};

EquacaoConversaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EquacaoConversaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(EquacaoConversaoService._path, 'EquacaoConversaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EquacaoConversaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(EquacaoConversaoService._path, 'EquacaoConversaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EquacaoConversaoService.findById = function(p0, callback) {
  return dwr.engine._execute(EquacaoConversaoService._path, 'EquacaoConversaoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.EquacaoConversao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EquacaoConversaoService.save = function(p0, callback) {
  return dwr.engine._execute(EquacaoConversaoService._path, 'EquacaoConversaoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
EquacaoConversaoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(EquacaoConversaoService._path, 'EquacaoConversaoService', 'populateSelect', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
EquacaoConversaoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(EquacaoConversaoService._path, 'EquacaoConversaoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
EquacaoConversaoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(EquacaoConversaoService._path, 'EquacaoConversaoService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.InstituicaoResponsavelService');

if (typeof this['InstituicaoResponsavelService'] == 'undefined') InstituicaoResponsavelService = {};

InstituicaoResponsavelService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
InstituicaoResponsavelService.deleteById = function(p0, callback) {
  return dwr.engine._execute(InstituicaoResponsavelService._path, 'InstituicaoResponsavelService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
InstituicaoResponsavelService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(InstituicaoResponsavelService._path, 'InstituicaoResponsavelService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
InstituicaoResponsavelService.findById = function(p0, callback) {
  return dwr.engine._execute(InstituicaoResponsavelService._path, 'InstituicaoResponsavelService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.InstituicaoResponsavel} p0 a param
 * @param {function|Object} callback callback function or options object
 */
InstituicaoResponsavelService.save = function(p0, callback) {
  return dwr.engine._execute(InstituicaoResponsavelService._path, 'InstituicaoResponsavelService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
InstituicaoResponsavelService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(InstituicaoResponsavelService._path, 'InstituicaoResponsavelService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
InstituicaoResponsavelService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(InstituicaoResponsavelService._path, 'InstituicaoResponsavelService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
InstituicaoResponsavelService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(InstituicaoResponsavelService._path, 'InstituicaoResponsavelService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.AlertaService');

if (typeof this['AlertaService'] == 'undefined') AlertaService = {};

AlertaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.rejeitar = function(p0, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'rejeitar', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.liberar = function(p0, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'liberar', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
AlertaService.rejeitarAll = function(callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'rejeitarAll', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.obtemInfoAlertas = function(p0, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'obtemInfoAlertas', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.exportInfo = function(p0, p1, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'exportInfo', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
AlertaService.marcarAlertasVisualizados = function(callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'marcarAlertasVisualizados', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.findById = function(p0, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'findById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.findByIds = function(p0, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'findByIds', arguments);
};

/**
 * @param {class com.coffey.cprm.alerta.crud.bean.Alerta} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.save = function(p0, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
AlertaService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(AlertaService._path, 'AlertaService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.PontoMonitoramentoSpatialService');

if (typeof this['PontoMonitoramentoSpatialService'] == 'undefined') PontoMonitoramentoSpatialService = {};

PontoMonitoramentoSpatialService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.medicao.spatial.crud.bean.PontoMonitoramentoSpatial} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoSpatialService.deleteByAlpha = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoSpatialService._path, 'PontoMonitoramentoSpatialService', 'deleteByAlpha', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.PontoMonitoramento} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoSpatialService.createGeometry = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoSpatialService._path, 'PontoMonitoramentoSpatialService', 'createGeometry', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.spatial.crud.bean.PontoMonitoramentoSpatial} p0 a param
 * @param {class com.coffey.cprm.geral.spatial.bean.SistemaCoordenadas} p1 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoSpatialService.save = function(p0, p1, callback) {
  return dwr.engine._execute(PontoMonitoramentoSpatialService._path, 'PontoMonitoramentoSpatialService', 'save', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoSpatialService.getSpatialDAO = function(callback) {
  return dwr.engine._execute(PontoMonitoramentoSpatialService._path, 'PontoMonitoramentoSpatialService', 'getSpatialDAO', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoSpatialService.getSpatialExtentByAlphaId = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoSpatialService._path, 'PontoMonitoramentoSpatialService', 'getSpatialExtentByAlphaId', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoSpatialService.getSpatialExtent = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoSpatialService._path, 'PontoMonitoramentoSpatialService', 'getSpatialExtent', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TipoBoletimService');

if (typeof this['TipoBoletimService'] == 'undefined') TipoBoletimService = {};

TipoBoletimService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TipoBoletimService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(TipoBoletimService._path, 'TipoBoletimService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.MedicaoBrutaViewService');

if (typeof this['MedicaoBrutaViewService'] == 'undefined') MedicaoBrutaViewService = {};

MedicaoBrutaViewService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.ParametroUnidade} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {class java.lang.Boolean} p2 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p3 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaViewService.populateByParametroUnidadeDataHoraMedicaoCamposBrancos = function(p0, p1, p2, p3, callback) {
  return dwr.engine._execute(MedicaoBrutaViewService._path, 'MedicaoBrutaViewService', 'populateByParametroUnidadeDataHoraMedicaoCamposBrancos', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.FiltroEntradaCompleta} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoBrutaViewService.populateByFiltroEntradaCompleta = function(p0, callback) {
  return dwr.engine._execute(MedicaoBrutaViewService._path, 'MedicaoBrutaViewService', 'populateByFiltroEntradaCompleta', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.SeparadorService');

if (typeof this['SeparadorService'] == 'undefined') SeparadorService = {};

SeparadorService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SeparadorService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(SeparadorService._path, 'SeparadorService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConfiguracaoDiretorioService');

if (typeof this['ConfiguracaoDiretorioService'] == 'undefined') ConfiguracaoDiretorioService = {};

ConfiguracaoDiretorioService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoDiretorioService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoDiretorioService._path, 'ConfiguracaoDiretorioService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoDiretorioService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoDiretorioService._path, 'ConfiguracaoDiretorioService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoDiretorioService.findById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoDiretorioService._path, 'ConfiguracaoDiretorioService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoDiretorioService.save = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoDiretorioService._path, 'ConfiguracaoDiretorioService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoDiretorioService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoDiretorioService._path, 'ConfiguracaoDiretorioService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoDiretorioService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoDiretorioService._path, 'ConfiguracaoDiretorioService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoDiretorioService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoDiretorioService._path, 'ConfiguracaoDiretorioService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ImportacaoCurvaChaveService');

if (typeof this['ImportacaoCurvaChaveService'] == 'undefined') ImportacaoCurvaChaveService = {};

ImportacaoCurvaChaveService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.importacao.bean.ConfiguracaoImportacaoCurvaChave} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ImportacaoCurvaChaveService.importar = function(p0, callback) {
  return dwr.engine._execute(ImportacaoCurvaChaveService._path, 'ImportacaoCurvaChaveService', 'importar', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TesteFormatoNomeArquivoDiretorioService');

if (typeof this['TesteFormatoNomeArquivoDiretorioService'] == 'undefined') TesteFormatoNomeArquivoDiretorioService = {};

TesteFormatoNomeArquivoDiretorioService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TesteFormatoNomeArquivoDiretorioService.testaFormatosNomesArquivos = function(p0, callback) {
  return dwr.engine._execute(TesteFormatoNomeArquivoDiretorioService._path, 'TesteFormatoNomeArquivoDiretorioService', 'testaFormatosNomesArquivos', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConfiguracaoEntradaService');

if (typeof this['ConfiguracaoEntradaService'] == 'undefined') ConfiguracaoEntradaService = {};

ConfiguracaoEntradaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoEntradaService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoEntradaService._path, 'ConfiguracaoEntradaService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoEntradaService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoEntradaService._path, 'ConfiguracaoEntradaService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoEntradaService.findById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoEntradaService._path, 'ConfiguracaoEntradaService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoEntrada} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoEntradaService.save = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoEntradaService._path, 'ConfiguracaoEntradaService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoEntradaService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoEntradaService._path, 'ConfiguracaoEntradaService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoEntradaService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoEntradaService._path, 'ConfiguracaoEntradaService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoEntradaService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoEntradaService._path, 'ConfiguracaoEntradaService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConfiguracaoFtpService');

if (typeof this['ConfiguracaoFtpService'] == 'undefined') ConfiguracaoFtpService = {};

ConfiguracaoFtpService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFtpService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFtpService._path, 'ConfiguracaoFtpService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFtpService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFtpService._path, 'ConfiguracaoFtpService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFtpService.findById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFtpService._path, 'ConfiguracaoFtpService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFtpService.save = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFtpService._path, 'ConfiguracaoFtpService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFtpService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoFtpService._path, 'ConfiguracaoFtpService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFtpService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoFtpService._path, 'ConfiguracaoFtpService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFtpService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoFtpService._path, 'ConfiguracaoFtpService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.AuditoriaService');

if (typeof this['AuditoriaService'] == 'undefined') AuditoriaService = {};

AuditoriaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AuditoriaService.findById = function(p0, callback) {
  return dwr.engine._execute(AuditoriaService._path, 'AuditoriaService', 'findById', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
AuditoriaService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(AuditoriaService._path, 'AuditoriaService', 'findAllOrderBy', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
AuditoriaService.deleteAll = function(callback) {
  return dwr.engine._execute(AuditoriaService._path, 'AuditoriaService', 'deleteAll', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
AuditoriaService.findAll = function(callback) {
  return dwr.engine._execute(AuditoriaService._path, 'AuditoriaService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.bean.Auditoria} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AuditoriaService.save = function(p0, callback) {
  return dwr.engine._execute(AuditoriaService._path, 'AuditoriaService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
AuditoriaService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(AuditoriaService._path, 'AuditoriaService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
AuditoriaService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(AuditoriaService._path, 'AuditoriaService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.AbaPlanilhaSimulacaoService');

if (typeof this['AbaPlanilhaSimulacaoService'] == 'undefined') AbaPlanilhaSimulacaoService = {};

AbaPlanilhaSimulacaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AbaPlanilhaSimulacaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(AbaPlanilhaSimulacaoService._path, 'AbaPlanilhaSimulacaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AbaPlanilhaSimulacaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(AbaPlanilhaSimulacaoService._path, 'AbaPlanilhaSimulacaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AbaPlanilhaSimulacaoService.findById = function(p0, callback) {
  return dwr.engine._execute(AbaPlanilhaSimulacaoService._path, 'AbaPlanilhaSimulacaoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.AbaPlanilhaSimulacao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
AbaPlanilhaSimulacaoService.save = function(p0, callback) {
  return dwr.engine._execute(AbaPlanilhaSimulacaoService._path, 'AbaPlanilhaSimulacaoService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.DelimitadorHoraService');

if (typeof this['DelimitadorHoraService'] == 'undefined') DelimitadorHoraService = {};

DelimitadorHoraService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
DelimitadorHoraService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(DelimitadorHoraService._path, 'DelimitadorHoraService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TipoPlanilhaService');

if (typeof this['TipoPlanilhaService'] == 'undefined') TipoPlanilhaService = {};

TipoPlanilhaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TipoPlanilhaService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(TipoPlanilhaService._path, 'TipoPlanilhaService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TipoAcessoService');

if (typeof this['TipoAcessoService'] == 'undefined') TipoAcessoService = {};

TipoAcessoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TipoAcessoService.findById = function(p0, callback) {
  return dwr.engine._execute(TipoAcessoService._path, 'TipoAcessoService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
TipoAcessoService.findAll = function(callback) {
  return dwr.engine._execute(TipoAcessoService._path, 'TipoAcessoService', 'findAll', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TipoAvisoAlertaService');

if (typeof this['TipoAvisoAlertaService'] == 'undefined') TipoAvisoAlertaService = {};

TipoAvisoAlertaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TipoAvisoAlertaService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(TipoAvisoAlertaService._path, 'TipoAvisoAlertaService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.MilharesService');

if (typeof this['MilharesService'] == 'undefined') MilharesService = {};

MilharesService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MilharesService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(MilharesService._path, 'MilharesService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TesteConexaoFTPService');

if (typeof this['TesteConexaoFTPService'] == 'undefined') TesteConexaoFTPService = {};

TesteConexaoFTPService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TesteConexaoFTPService.testaConexao = function(p0, callback) {
  return dwr.engine._execute(TesteConexaoFTPService._path, 'TesteConexaoFTPService', 'testaConexao', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ModeloPrevisaoService');

if (typeof this['ModeloPrevisaoService'] == 'undefined') ModeloPrevisaoService = {};

ModeloPrevisaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloPrevisaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ModeloPrevisaoService._path, 'ModeloPrevisaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloPrevisaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ModeloPrevisaoService._path, 'ModeloPrevisaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloPrevisaoService.findById = function(p0, callback) {
  return dwr.engine._execute(ModeloPrevisaoService._path, 'ModeloPrevisaoService', 'findById', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloPrevisaoService.findByPontoMonitoramento = function(p0, callback) {
  return dwr.engine._execute(ModeloPrevisaoService._path, 'ModeloPrevisaoService', 'findByPontoMonitoramento', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.ModeloPrevisao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloPrevisaoService.save = function(p0, callback) {
  return dwr.engine._execute(ModeloPrevisaoService._path, 'ModeloPrevisaoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloPrevisaoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ModeloPrevisaoService._path, 'ModeloPrevisaoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloPrevisaoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ModeloPrevisaoService._path, 'ModeloPrevisaoService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ModeloPrevisaoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ModeloPrevisaoService._path, 'ModeloPrevisaoService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TesteFormatoNomeArquivoFTPService');

if (typeof this['TesteFormatoNomeArquivoFTPService'] == 'undefined') TesteFormatoNomeArquivoFTPService = {};

TesteFormatoNomeArquivoFTPService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TesteFormatoNomeArquivoFTPService.testaFormatosNomesArquivos = function(p0, callback) {
  return dwr.engine._execute(TesteFormatoNomeArquivoFTPService._path, 'TesteFormatoNomeArquivoFTPService', 'testaFormatosNomesArquivos', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ImportacaoMedicoesService');

if (typeof this['ImportacaoMedicoesService'] == 'undefined') ImportacaoMedicoesService = {};

ImportacaoMedicoesService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.Template} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {class [B} p2 a param
 * @param {function|Object} callback callback function or options object
 */
ImportacaoMedicoesService.forcarImportar = function(p0, p1, p2, callback) {
  return dwr.engine._execute(ImportacaoMedicoesService._path, 'ImportacaoMedicoesService', 'forcarImportar', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.Template} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {class [B} p2 a param
 * @param {function|Object} callback callback function or options object
 */
ImportacaoMedicoesService.validar = function(p0, p1, p2, callback) {
  return dwr.engine._execute(ImportacaoMedicoesService._path, 'ImportacaoMedicoesService', 'validar', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.Template} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {class [B} p2 a param
 * @param {function|Object} callback callback function or options object
 */
ImportacaoMedicoesService.importar = function(p0, p1, p2, callback) {
  return dwr.engine._execute(ImportacaoMedicoesService._path, 'ImportacaoMedicoesService', 'importar', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.SensorService');

if (typeof this['SensorService'] == 'undefined') SensorService = {};

SensorService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p2 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.findByPontoMonitoramentoFonteAquisicao = function(p0, p1, p2, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'findByPontoMonitoramentoFonteAquisicao', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.deleteById = function(p0, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.findById = function(p0, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'findById', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.findByFonteAquisicao = function(p0, p1, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'findByFonteAquisicao', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.findByFonteAquisicao = function(p0, p1, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'findByFonteAquisicao', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'findAllOrderBy', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.findAllSecurity = function(p0, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'findAllSecurity', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.findByIdPontoMonitoramento = function(p0, p1, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'findByIdPontoMonitoramento', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Sensor} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.save = function(p0, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(SensorService._path, 'SensorService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.MedicaoConvertidaService');

if (typeof this['MedicaoConvertidaService'] == 'undefined') MedicaoConvertidaService = {};

MedicaoConvertidaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoConvertidaService.deleteById = function(p0, callback) {
  return dwr.engine._execute(MedicaoConvertidaService._path, 'MedicaoConvertidaService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoConvertidaService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(MedicaoConvertidaService._path, 'MedicaoConvertidaService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoConvertidaService.findById = function(p0, callback) {
  return dwr.engine._execute(MedicaoConvertidaService._path, 'MedicaoConvertidaService', 'findById', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.medicao.crud.bean.MedicaoConvertida} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoConvertidaService.setIdByIdMedicaoBruta = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoConvertidaService._path, 'MedicaoConvertidaService', 'setIdByIdMedicaoBruta', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.MedicaoConvertida} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoConvertidaService.save = function(p0, callback) {
  return dwr.engine._execute(MedicaoConvertidaService._path, 'MedicaoConvertidaService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoConvertidaService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoConvertidaService._path, 'MedicaoConvertidaService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoConvertidaService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoConvertidaService._path, 'MedicaoConvertidaService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.EmailService');

if (typeof this['EmailService'] == 'undefined') EmailService = {};

EmailService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.deleteById = function(p0, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.findById = function(p0, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'findById', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'findAllOrderBy', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.findByGrupos = function(p0, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'findByGrupos', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.Email} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.cadastraEmail = function(p0, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'cadastraEmail', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {class java.lang.String} p2 a param
 * @param {class com.coffey.cprm.seguranca.crud.bean.GrupoUsuario} p3 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.cadastraEmailAdm = function(p0, p1, p2, p3, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'cadastraEmailAdm', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
EmailService.findAll = function(callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.Email} p0 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.save = function(p0, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
EmailService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(EmailService._path, 'EmailService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.SistemaCoordenadasService');

if (typeof this['SistemaCoordenadasService'] == 'undefined') SistemaCoordenadasService = {};

SistemaCoordenadasService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SistemaCoordenadasService.findAllByDescricao = function(p0, callback) {
  return dwr.engine._execute(SistemaCoordenadasService._path, 'SistemaCoordenadasService', 'findAllByDescricao', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SistemaCoordenadasService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(SistemaCoordenadasService._path, 'SistemaCoordenadasService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.UnidadeService');

if (typeof this['UnidadeService'] == 'undefined') UnidadeService = {};

UnidadeService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UnidadeService.deleteById = function(p0, callback) {
  return dwr.engine._execute(UnidadeService._path, 'UnidadeService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UnidadeService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(UnidadeService._path, 'UnidadeService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UnidadeService.findById = function(p0, callback) {
  return dwr.engine._execute(UnidadeService._path, 'UnidadeService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
UnidadeService.findAll = function(callback) {
  return dwr.engine._execute(UnidadeService._path, 'UnidadeService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Unidade} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UnidadeService.save = function(p0, callback) {
  return dwr.engine._execute(UnidadeService._path, 'UnidadeService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
UnidadeService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(UnidadeService._path, 'UnidadeService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
UnidadeService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(UnidadeService._path, 'UnidadeService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
UnidadeService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(UnidadeService._path, 'UnidadeService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ItemResultadoSimulacaoService');

if (typeof this['ItemResultadoSimulacaoService'] == 'undefined') ItemResultadoSimulacaoService = {};

ItemResultadoSimulacaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.previsao.crud.enums.TipoPlanilha} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ItemResultadoSimulacaoService.findByPontoMonitoramentoAndTipoPlanilha = function(p0, p1, callback) {
  return dwr.engine._execute(ItemResultadoSimulacaoService._path, 'ItemResultadoSimulacaoService', 'findByPontoMonitoramentoAndTipoPlanilha', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ItemResultadoSimulacaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ItemResultadoSimulacaoService._path, 'ItemResultadoSimulacaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ItemResultadoSimulacaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ItemResultadoSimulacaoService._path, 'ItemResultadoSimulacaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ItemResultadoSimulacaoService.findById = function(p0, callback) {
  return dwr.engine._execute(ItemResultadoSimulacaoService._path, 'ItemResultadoSimulacaoService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ItemResultadoSimulacaoService.findAll = function(callback) {
  return dwr.engine._execute(ItemResultadoSimulacaoService._path, 'ItemResultadoSimulacaoService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.ItemResultadoSimulacao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ItemResultadoSimulacaoService.save = function(p0, callback) {
  return dwr.engine._execute(ItemResultadoSimulacaoService._path, 'ItemResultadoSimulacaoService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TesteConexaoDiretorioService');

if (typeof this['TesteConexaoDiretorioService'] == 'undefined') TesteConexaoDiretorioService = {};

TesteConexaoDiretorioService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TesteConexaoDiretorioService.testaConexao = function(p0, callback) {
  return dwr.engine._execute(TesteConexaoDiretorioService._path, 'TesteConexaoDiretorioService', 'testaConexao', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConfiguracaoFiltroService');

if (typeof this['ConfiguracaoFiltroService'] == 'undefined') ConfiguracaoFiltroService = {};

ConfiguracaoFiltroService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.medicao.crud.enums.TipoAvisoAlerta} p1 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p2 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.findByPontoMonitoramentoTipoAvisoAlerta = function(p0, p1, p2, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'findByPontoMonitoramentoTipoAvisoAlerta', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.PontoMonitoramento} p0 a param
 * @param {class com.coffey.cprm.medicao.crud.enums.TipoAvisoAlerta} p1 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p2 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.addByPontoMonitoramentoTipoAvisoAlerta = function(p0, p1, p2, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'addByPontoMonitoramentoTipoAvisoAlerta', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.findById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'findById', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.findByFilter = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'findByFilter', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.ConfiguracaoFiltro} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.save = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'populateSelect', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFiltroService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoFiltroService._path, 'ConfiguracaoFiltroService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FormatoHoraService');

if (typeof this['FormatoHoraService'] == 'undefined') FormatoHoraService = {};

FormatoHoraService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoHoraService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FormatoHoraService._path, 'FormatoHoraService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ParceiroService');

if (typeof this['ParceiroService'] == 'undefined') ParceiroService = {};

ParceiroService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.findByValidade = function(callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'findByValidade', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.findById = function(p0, callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.findAll = function(callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'findAll', arguments);
};

/**
 * @param {class [B} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.createImage = function(p0, p1, callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'createImage', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.Parceiro} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.save = function(p0, callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParceiroService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ParceiroService._path, 'ParceiroService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ReleaseNoteService');

if (typeof this['ReleaseNoteService'] == 'undefined') ReleaseNoteService = {};

ReleaseNoteService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ReleaseNoteService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ReleaseNoteService._path, 'ReleaseNoteService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ReleaseNoteService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ReleaseNoteService._path, 'ReleaseNoteService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ReleaseNoteService.findById = function(p0, callback) {
  return dwr.engine._execute(ReleaseNoteService._path, 'ReleaseNoteService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ReleaseNoteService.findAll = function(callback) {
  return dwr.engine._execute(ReleaseNoteService._path, 'ReleaseNoteService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.crud.bean.ReleaseNote} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ReleaseNoteService.save = function(p0, callback) {
  return dwr.engine._execute(ReleaseNoteService._path, 'ReleaseNoteService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ReleaseNoteService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ReleaseNoteService._path, 'ReleaseNoteService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ReleaseNoteService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ReleaseNoteService._path, 'ReleaseNoteService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.RelatorioService');

if (typeof this['RelatorioService'] == 'undefined') RelatorioService = {};

RelatorioService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {class java.util.Date} p2 a param
 * @param {class java.lang.String} p3 a param
 * @param {function|Object} callback callback function or options object
 */
RelatorioService.gerarRelatorio = function(p0, p1, p2, p3, callback) {
  return dwr.engine._execute(RelatorioService._path, 'RelatorioService', 'gerarRelatorio', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {function|Object} callback callback function or options object
 */
RelatorioService.gerarRelatorioVerDados = function(p0, p1, p2, callback) {
  return dwr.engine._execute(RelatorioService._path, 'RelatorioService', 'gerarRelatorioVerDados', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {function|Object} callback callback function or options object
 */
RelatorioService.gerarRelatorioChuvaAcumulada = function(p0, p1, callback) {
  return dwr.engine._execute(RelatorioService._path, 'RelatorioService', 'gerarRelatorioChuvaAcumulada', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {class java.util.Date} p2 a param
 * @param {class java.lang.String} p3 a param
 * @param {function|Object} callback callback function or options object
 */
RelatorioService.exportPdfRelatorioAcompanhamentoHidrologico = function(p0, p1, p2, p3, callback) {
  return dwr.engine._execute(RelatorioService._path, 'RelatorioService', 'exportPdfRelatorioAcompanhamentoHidrologico', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.InformacaoService');

if (typeof this['InformacaoService'] == 'undefined') InformacaoService = {};

InformacaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {function|Object} callback callback function or options object
 */
InformacaoService.obtemPontos = function(callback) {
  return dwr.engine._execute(InformacaoService._path, 'InformacaoService', 'obtemPontos', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
InformacaoService.obtemAlertasBacia = function(callback) {
  return dwr.engine._execute(InformacaoService._path, 'InformacaoService', 'obtemAlertasBacia', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
InformacaoService.obtemStatusBacia = function(callback) {
  return dwr.engine._execute(InformacaoService._path, 'InformacaoService', 'obtemStatusBacia', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.EquationSolver');

if (typeof this['EquationSolver'] == 'undefined') EquationSolver = {};

EquationSolver._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {class java.lang.Object} p2 a param
 * @param {function|Object} callback callback function or options object
 */
EquationSolver.solve = function(p0, p1, p2, callback) {
  return dwr.engine._execute(EquationSolver._path, 'EquationSolver', 'solve', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.SimulacaoService');

if (typeof this['SimulacaoService'] == 'undefined') SimulacaoService = {};

SimulacaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.resultadoVerify = function(callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'resultadoVerify', arguments);
};

/**
 * @param {class java.lang.Boolean} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.findByPrevisaoLog = function(p0, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'findByPrevisaoLog', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.Simulacao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.simularPrevisaoExcel = function(p0, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'simularPrevisaoExcel', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.getRetornoDadosSimulados = function(callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'getRetornoDadosSimulados', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.processaResultadosFinais = function(p0, p1, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'processaResultadosFinais', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.findById = function(p0, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.Simulacao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.save = function(p0, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'populateSelect', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SimulacaoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(SimulacaoService._path, 'SimulacaoService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TipoAlertaService');

if (typeof this['TipoAlertaService'] == 'undefined') TipoAlertaService = {};

TipoAlertaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TipoAlertaService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(TipoAlertaService._path, 'TipoAlertaService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TextoBoletimService');

if (typeof this['TextoBoletimService'] == 'undefined') TextoBoletimService = {};

TextoBoletimService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TextoBoletimService.deleteById = function(p0, callback) {
  return dwr.engine._execute(TextoBoletimService._path, 'TextoBoletimService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TextoBoletimService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(TextoBoletimService._path, 'TextoBoletimService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TextoBoletimService.findById = function(p0, callback) {
  return dwr.engine._execute(TextoBoletimService._path, 'TextoBoletimService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
TextoBoletimService.findAll = function(callback) {
  return dwr.engine._execute(TextoBoletimService._path, 'TextoBoletimService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.TextoBoletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TextoBoletimService.save = function(p0, callback) {
  return dwr.engine._execute(TextoBoletimService._path, 'TextoBoletimService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TemplateGraficoService');

if (typeof this['TemplateGraficoService'] == 'undefined') TemplateGraficoService = {};

TemplateGraficoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.findById = function(p0, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.TemplateGrafico} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.saveTemplateGrafico = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'saveTemplateGrafico', arguments);
};

/**
 * @param {class java.lang.Boolean} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.findByExibirBoletim = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'findByExibirBoletim', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.findAll = function(callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.TemplateGrafico} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.save = function(p0, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'populateSelect', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplateGraficoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(TemplateGraficoService._path, 'TemplateGraficoService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ImportacaoPrevisoesService');

if (typeof this['ImportacaoPrevisoesService'] == 'undefined') ImportacaoPrevisoesService = {};

ImportacaoPrevisoesService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.TemplatePrevisao} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ImportacaoPrevisoesService.forcarImportar = function(p0, p1, callback) {
  return dwr.engine._execute(ImportacaoPrevisoesService._path, 'ImportacaoPrevisoesService', 'forcarImportar', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.TemplatePrevisao} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ImportacaoPrevisoesService.validar = function(p0, p1, callback) {
  return dwr.engine._execute(ImportacaoPrevisoesService._path, 'ImportacaoPrevisoesService', 'validar', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.TemplatePrevisao} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ImportacaoPrevisoesService.importar = function(p0, p1, callback) {
  return dwr.engine._execute(ImportacaoPrevisoesService._path, 'ImportacaoPrevisoesService', 'importar', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TemplatePrevisaoService');

if (typeof this['TemplatePrevisaoService'] == 'undefined') TemplatePrevisaoService = {};

TemplatePrevisaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.TemplatePrevisao} p0 a param
 * @param {class [B} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.recuperaPrimeiraLinhaDoArquivoPorTemplate = function(p0, p1, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'recuperaPrimeiraLinhaDoArquivoPorTemplate', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.findById = function(p0, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.TemplatePrevisao} p0 a param
 * @param {class [Ljava.lang.String;} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.saveTemplate = function(p0, p1, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'saveTemplate', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.TemplatePrevisao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.save = function(p0, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'populateSelect', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p1 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p2 a param
 * @param {function|Object} callback callback function or options object
 */
TemplatePrevisaoService.populateSelectParam = function(p0, p1, p2, callback) {
  return dwr.engine._execute(TemplatePrevisaoService._path, 'TemplatePrevisaoService', 'populateSelectParam', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FormatoArquivoService');

if (typeof this['FormatoArquivoService'] == 'undefined') FormatoArquivoService = {};

FormatoArquivoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoArquivoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(FormatoArquivoService._path, 'FormatoArquivoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoArquivoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(FormatoArquivoService._path, 'FormatoArquivoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoArquivoService.findById = function(p0, callback) {
  return dwr.engine._execute(FormatoArquivoService._path, 'FormatoArquivoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.FormatoArquivo} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoArquivoService.save = function(p0, callback) {
  return dwr.engine._execute(FormatoArquivoService._path, 'FormatoArquivoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoArquivoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(FormatoArquivoService._path, 'FormatoArquivoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoArquivoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(FormatoArquivoService._path, 'FormatoArquivoService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoArquivoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FormatoArquivoService._path, 'FormatoArquivoService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FusoHorarioService');

if (typeof this['FusoHorarioService'] == 'undefined') FusoHorarioService = {};

FusoHorarioService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FusoHorarioService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FusoHorarioService._path, 'FusoHorarioService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FormulaPrevisaoService');

if (typeof this['FormulaPrevisaoService'] == 'undefined') FormulaPrevisaoService = {};

FormulaPrevisaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.FormulaPrevisao} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.saveFormula = function(p0, p1, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'saveFormula', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.FormulaPrevisao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.validaFormula = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'validaFormula', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.traduzFormula = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'traduzFormula', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.getTermoSemHoras = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'getTermoSemHoras', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.validaByIdFormula = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'validaByIdFormula', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.getTermoAntesIgual = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'getTermoAntesIgual', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.deleteByPontoMonitoramento = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'deleteByPontoMonitoramento', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.findById = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'findById', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.findByPontoMonitoramento = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'findByPontoMonitoramento', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'findAllOrderBy', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.atualizaFormulas = function(callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'atualizaFormulas', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.FormulaPrevisao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.save = function(p0, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'populateSelect', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'exportExcel', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p1 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p2 a param
 * @param {function|Object} callback callback function or options object
 */
FormulaPrevisaoService.populateSelectParam = function(p0, p1, p2, callback) {
  return dwr.engine._execute(FormulaPrevisaoService._path, 'FormulaPrevisaoService', 'populateSelectParam', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.GrupoAcessoService');

if (typeof this['GrupoAcessoService'] == 'undefined') GrupoAcessoService = {};

GrupoAcessoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.findById = function(p0, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'findById', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'findAllOrderBy', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.findByGrupoUsuario = function(p0, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'findByGrupoUsuario', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.bean.GrupoAcessoPonto} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {interface java.util.List} p2 a param
 * @param {interface java.util.List} p3 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.saveGrupoAcessoPonto = function(p0, p1, p2, p3, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'saveGrupoAcessoPonto', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.obtemGrupoAcessoPonto = function(p0, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'obtemGrupoAcessoPonto', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.obtemGrupoAcessoTipoAcessoPonto = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'obtemGrupoAcessoTipoAcessoPonto', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.obtemGrupoAcessoTipoAcessoFonte = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'obtemGrupoAcessoTipoAcessoFonte', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.obtemGrupoAcessoTipoAcessoSensor = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'obtemGrupoAcessoTipoAcessoSensor', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.checkTipoAcessoGrupoUsuario = function(p0, p1, p2, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'checkTipoAcessoGrupoUsuario', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.obtemTodosGrupoAcessoPonto = function(callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'obtemTodosGrupoAcessoPonto', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class [Lcom.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso;} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.findByGrupoUsuarioAndTipoAcesso = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'findByGrupoUsuarioAndTipoAcesso', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.findAll = function(callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.bean.GrupoAcesso} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.save = function(p0, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'populateSelect', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoAcessoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoAcessoService._path, 'GrupoAcessoService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.GrupoUsuarioService');

if (typeof this['GrupoUsuarioService'] == 'undefined') GrupoUsuarioService = {};

GrupoUsuarioService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.deleteById = function(p0, callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.findById = function(p0, callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'findById', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'findAllOrderBy', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.findAll = function(callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.bean.GrupoUsuario} p0 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.save = function(p0, callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'populateSelect', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
GrupoUsuarioService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(GrupoUsuarioService._path, 'GrupoUsuarioService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConversorService');

if (typeof this['ConversorService'] == 'undefined') ConversorService = {};

ConversorService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConversorService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ConversorService._path, 'ConversorService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConversorService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ConversorService._path, 'ConversorService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConversorService.findById = function(p0, callback) {
  return dwr.engine._execute(ConversorService._path, 'ConversorService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.conversor.crud.bean.Conversor} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConversorService.save = function(p0, callback) {
  return dwr.engine._execute(ConversorService._path, 'ConversorService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConversorService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ConversorService._path, 'ConversorService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConversorService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ConversorService._path, 'ConversorService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConversorService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ConversorService._path, 'ConversorService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TipoFiltroService');

if (typeof this['TipoFiltroService'] == 'undefined') TipoFiltroService = {};

TipoFiltroService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.deleteById = function(p0, callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.findById = function(p0, callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.filtrosMapa = function(callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'filtrosMapa', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.enums.TipoAvisoAlerta} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.findByTipoAvisoAlerta = function(p0, callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'findByTipoAvisoAlerta', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.findAll = function(callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.TipoFiltro} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.save = function(p0, callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
TipoFiltroService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(TipoFiltroService._path, 'TipoFiltroService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConfiguracaoSimulacaoService');

if (typeof this['ConfiguracaoSimulacaoService'] == 'undefined') ConfiguracaoSimulacaoService = {};

ConfiguracaoSimulacaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.util.Date} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoSimulacaoService.getConfiguracaoSimulacao = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoSimulacaoService._path, 'ConfiguracaoSimulacaoService', 'getConfiguracaoSimulacao', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoSimulacaoService.getConfiguracaoSimulacaoLog = function(callback) {
  return dwr.engine._execute(ConfiguracaoSimulacaoService._path, 'ConfiguracaoSimulacaoService', 'getConfiguracaoSimulacaoLog', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoSimulacaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoSimulacaoService._path, 'ConfiguracaoSimulacaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoSimulacaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoSimulacaoService._path, 'ConfiguracaoSimulacaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoSimulacaoService.findById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoSimulacaoService._path, 'ConfiguracaoSimulacaoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.ConfiguracaoSimulacao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoSimulacaoService.save = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoSimulacaoService._path, 'ConfiguracaoSimulacaoService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FuncionalidadeService');

if (typeof this['FuncionalidadeService'] == 'undefined') FuncionalidadeService = {};

FuncionalidadeService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FuncionalidadeService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(FuncionalidadeService._path, 'FuncionalidadeService', 'findAllOrderBy', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
FuncionalidadeService.findAll = function(callback) {
  return dwr.engine._execute(FuncionalidadeService._path, 'FuncionalidadeService', 'findAll', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FonteService');

if (typeof this['FonteService'] == 'undefined') FonteService = {};

FonteService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FonteService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FonteService._path, 'FonteService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ComunicacaoService');

if (typeof this['ComunicacaoService'] == 'undefined') ComunicacaoService = {};

ComunicacaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ComunicacaoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ComunicacaoService._path, 'ComunicacaoService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConfiguracaoFonteService');

if (typeof this['ConfiguracaoFonteService'] == 'undefined') ConfiguracaoFonteService = {};

ConfiguracaoFonteService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFonteService.getConfiguracaoFonteGridByFormulas = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFonteService._path, 'ConfiguracaoFonteService', 'getConfiguracaoFonteGridByFormulas', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoFonteService.findById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoFonteService._path, 'ConfiguracaoFonteService', 'findById', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ExportacaoDadosService');

if (typeof this['ExportacaoDadosService'] == 'undefined') ExportacaoDadosService = {};

ExportacaoDadosService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.findById = function(p0, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'findById', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'findAllOrderBy', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.exportarPorSensor = function(p0, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'exportarPorSensor', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.exportar = function(p0, p1, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'exportar', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.findAll = function(callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.ExportacaoDados} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.save = function(p0, p1, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ExportacaoDadosService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ExportacaoDadosService._path, 'ExportacaoDadosService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.MedicaoPrevisaoService');

if (typeof this['MedicaoPrevisaoService'] == 'undefined') MedicaoPrevisaoService = {};

MedicaoPrevisaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.util.Date} p0 a param
 * @param {class com.coffey.cprm.medicao.crud.bean.ModeloPrevisao} p1 a param
 * @param {class com.coffey.cprm.medicao.crud.bean.ParametroUnidade} p2 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.findByDataPrevisaoModeloParametroUnidade = function(p0, p1, p2, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'findByDataPrevisaoModeloParametroUnidade', arguments);
};

/**
 * @param {class java.util.Date} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {class com.coffey.cprm.medicao.crud.bean.ModeloPrevisao} p2 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.findByDataPrevisaoAndModelagemAndModelo = function(p0, p1, p2, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'findByDataPrevisaoAndModelagemAndModelo', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.findById = function(p0, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.MedicaoPrevisao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.saveOrUpdate = function(p0, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'saveOrUpdate', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Sensor} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.countByDataHoraMedicaoESensor = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'countByDataHoraMedicaoESensor', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.MedicaoPrevisao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.save = function(p0, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
MedicaoPrevisaoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(MedicaoPrevisaoService._path, 'MedicaoPrevisaoService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FiltroService');

if (typeof this['FiltroService'] == 'undefined') FiltroService = {};

FiltroService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.deleteById = function(p0, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.findById = function(p0, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.PontoMonitoramento} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.findByPontoMonitoramento = function(p0, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'findByPontoMonitoramento', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Filtro} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.saveFiltro = function(p0, p1, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'saveFiltro', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Filtro} p0 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.save = function(p0, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'populateSelect', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FiltroService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(FiltroService._path, 'FiltroService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConfiguracaoURLService');

if (typeof this['ConfiguracaoURLService'] == 'undefined') ConfiguracaoURLService = {};

ConfiguracaoURLService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoURLService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoURLService._path, 'ConfiguracaoURLService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoURLService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoURLService._path, 'ConfiguracaoURLService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoURLService.findById = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoURLService._path, 'ConfiguracaoURLService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoConexao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoURLService.save = function(p0, callback) {
  return dwr.engine._execute(ConfiguracaoURLService._path, 'ConfiguracaoURLService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoURLService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoURLService._path, 'ConfiguracaoURLService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoURLService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoURLService._path, 'ConfiguracaoURLService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ConfiguracaoURLService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ConfiguracaoURLService._path, 'ConfiguracaoURLService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ParametroUnidadeService');

if (typeof this['ParametroUnidadeService'] == 'undefined') ParametroUnidadeService = {};

ParametroUnidadeService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.populateSelectByPontoMonitoramento = function(p0, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'populateSelectByPontoMonitoramento', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.populateSelectByPontoMonitoramentoPrevisao = function(p0, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'populateSelectByPontoMonitoramentoPrevisao', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.findById = function(p0, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.findAll = function(callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.ParametroUnidade} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.save = function(p0, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ParametroUnidadeService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ParametroUnidadeService._path, 'ParametroUnidadeService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.SensorExportacaoDadosService');

if (typeof this['SensorExportacaoDadosService'] == 'undefined') SensorExportacaoDadosService = {};

SensorExportacaoDadosService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorExportacaoDadosService.findByPontoMonitoramentoForExportacao = function(p0, callback) {
  return dwr.engine._execute(SensorExportacaoDadosService._path, 'SensorExportacaoDadosService', 'findByPontoMonitoramentoForExportacao', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorExportacaoDadosService.deleteById = function(p0, callback) {
  return dwr.engine._execute(SensorExportacaoDadosService._path, 'SensorExportacaoDadosService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorExportacaoDadosService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(SensorExportacaoDadosService._path, 'SensorExportacaoDadosService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorExportacaoDadosService.findById = function(p0, callback) {
  return dwr.engine._execute(SensorExportacaoDadosService._path, 'SensorExportacaoDadosService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
SensorExportacaoDadosService.findAll = function(callback) {
  return dwr.engine._execute(SensorExportacaoDadosService._path, 'SensorExportacaoDadosService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.SensorExportacaoDados} p0 a param
 * @param {function|Object} callback callback function or options object
 */
SensorExportacaoDadosService.save = function(p0, callback) {
  return dwr.engine._execute(SensorExportacaoDadosService._path, 'SensorExportacaoDadosService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorExportacaoDadosService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(SensorExportacaoDadosService._path, 'SensorExportacaoDadosService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SensorExportacaoDadosService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(SensorExportacaoDadosService._path, 'SensorExportacaoDadosService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.FormatoDataService');

if (typeof this['FormatoDataService'] == 'undefined') FormatoDataService = {};

FormatoDataService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
FormatoDataService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(FormatoDataService._path, 'FormatoDataService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.PontoMonitoramentoService');

if (typeof this['PontoMonitoramentoService'] == 'undefined') PontoMonitoramentoService = {};

PontoMonitoramentoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.buscaAnexosByIdPontoMonitoramento = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'buscaAnexosByIdPontoMonitoramento', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'populateSelect', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.findById = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.obtemPontosEmAlerta = function(callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'obtemPontosEmAlerta', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'findAllOrderBy', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.findAllSecurity = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'findAllSecurity', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.findBySigla = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'findBySigla', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.findAllSecuritySpatial = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'findAllSecuritySpatial', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.enums.EnumTipoAlerta} p0 a param
 * @param {class com.coffey.cprm.medicao.crud.bean.TipoFiltro} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {class java.util.Date} p3 a param
 * @param {class java.lang.Integer} p4 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.atualizaTipoAlerta = function(p0, p1, p2, p3, p4, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'atualizaTipoAlerta', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.enums.EnumTipoAlerta} p0 a param
 * @param {class com.coffey.cprm.medicao.crud.bean.TipoFiltro} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {class java.util.Date} p3 a param
 * @param {class java.lang.Integer} p4 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.atualizaTipoAlerta = function(p0, p1, p2, p3, p4, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'atualizaTipoAlerta', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.findAll = function(callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.PontoMonitoramento} p0 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.save = function(p0, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
PontoMonitoramentoService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(PontoMonitoramentoService._path, 'PontoMonitoramentoService', 'populateGrid', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.LoginService');

if (typeof this['LoginService'] == 'undefined') LoginService = {};

LoginService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {function|Object} callback callback function or options object
 */
LoginService.loadUser = function(callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'loadUser', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
LoginService.enviaDicaSenha = function(p0, callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'enviaDicaSenha', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {class java.lang.String} p2 a param
 * @param {class java.lang.String} p3 a param
 * @param {function|Object} callback callback function or options object
 */
LoginService.recuperaSenha = function(p0, p1, p2, p3, callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'recuperaSenha', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
LoginService.enviaSenha = function(p0, p1, callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'enviaSenha', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
LoginService.sessionVerify = function(callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'sessionVerify', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
LoginService.getEncryptedPassword = function(p0, p1, callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'getEncryptedPassword', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
LoginService.verifyAdministrator = function(p0, p1, callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'verifyAdministrator', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
LoginService.logout = function(callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'logout', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
LoginService.setTimeZone = function(p0, callback) {
  return dwr.engine._execute(LoginService._path, 'LoginService', 'setTimeZone', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.GeradorGraficoService');

if (typeof this['GeradorGraficoService'] == 'undefined') GeradorGraficoService = {};

GeradorGraficoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {class java.lang.Integer} p3 a param
 * @param {class java.lang.Boolean} p4 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p5 a param
 * @param {class java.lang.Boolean} p6 a param
 * @param {function|Object} callback callback function or options object
 */
GeradorGraficoService.obtemGraficoPontoMonitoramentoComRequest = function(p0, p1, p2, p3, p4, p5, p6, callback) {
  return dwr.engine._execute(GeradorGraficoService._path, 'GeradorGraficoService', 'obtemGraficoPontoMonitoramentoComRequest', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class com.coffey.cprm.publicacao.crud.bean.TemplateGrafico} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {class java.lang.Integer} p3 a param
 * @param {class java.lang.Boolean} p4 a param
 * @param {class java.util.Date} p5 a param
 * @param {function|Object} callback callback function or options object
 */
GeradorGraficoService.obtemGraficoComData = function(p0, p1, p2, p3, p4, p5, callback) {
  return dwr.engine._execute(GeradorGraficoService._path, 'GeradorGraficoService', 'obtemGraficoComData', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {class java.lang.Integer} p3 a param
 * @param {class java.lang.Boolean} p4 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p5 a param
 * @param {class java.lang.Boolean} p6 a param
 * @param {function|Object} callback callback function or options object
 */
GeradorGraficoService.obtemGraficoPontoMonitoramento = function(p0, p1, p2, p3, p4, p5, p6, callback) {
  return dwr.engine._execute(GeradorGraficoService._path, 'GeradorGraficoService', 'obtemGraficoPontoMonitoramento', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {class java.lang.Integer} p3 a param
 * @param {class java.lang.Boolean} p4 a param
 * @param {class java.lang.String} p5 a param
 * @param {class java.util.Date} p6 a param
 * @param {function|Object} callback callback function or options object
 */
GeradorGraficoService.obtemListGraficoComData = function(p0, p1, p2, p3, p4, p5, p6, callback) {
  return dwr.engine._execute(GeradorGraficoService._path, 'GeradorGraficoService', 'obtemListGraficoComData', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class com.coffey.cprm.publicacao.crud.bean.TemplateGrafico} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {class java.lang.Integer} p3 a param
 * @param {class java.lang.Boolean} p4 a param
 * @param {class java.lang.String} p5 a param
 * @param {function|Object} callback callback function or options object
 */
GeradorGraficoService.obtemGrafico = function(p0, p1, p2, p3, p4, p5, callback) {
  return dwr.engine._execute(GeradorGraficoService._path, 'GeradorGraficoService', 'obtemGrafico', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {interface java.util.List} p1 a param
 * @param {class java.lang.Integer} p2 a param
 * @param {class java.lang.Integer} p3 a param
 * @param {class java.lang.Boolean} p4 a param
 * @param {class java.lang.String} p5 a param
 * @param {function|Object} callback callback function or options object
 */
GeradorGraficoService.obtemListGrafico = function(p0, p1, p2, p3, p4, p5, callback) {
  return dwr.engine._execute(GeradorGraficoService._path, 'GeradorGraficoService', 'obtemListGrafico', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.CabecalhoBoletimService');

if (typeof this['CabecalhoBoletimService'] == 'undefined') CabecalhoBoletimService = {};

CabecalhoBoletimService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {function|Object} callback callback function or options object
 */
CabecalhoBoletimService.findUniqueHead = function(callback) {
  return dwr.engine._execute(CabecalhoBoletimService._path, 'CabecalhoBoletimService', 'findUniqueHead', arguments);
};

/**
 * @param {class [B} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
CabecalhoBoletimService.createImage = function(p0, p1, callback) {
  return dwr.engine._execute(CabecalhoBoletimService._path, 'CabecalhoBoletimService', 'createImage', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.CabecalhoBoletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
CabecalhoBoletimService.save = function(p0, callback) {
  return dwr.engine._execute(CabecalhoBoletimService._path, 'CabecalhoBoletimService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ResponsavelService');

if (typeof this['ResponsavelService'] == 'undefined') ResponsavelService = {};

ResponsavelService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResponsavelService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ResponsavelService._path, 'ResponsavelService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResponsavelService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ResponsavelService._path, 'ResponsavelService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResponsavelService.findById = function(p0, callback) {
  return dwr.engine._execute(ResponsavelService._path, 'ResponsavelService', 'findById', arguments);
};

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.Responsavel} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResponsavelService.save = function(p0, callback) {
  return dwr.engine._execute(ResponsavelService._path, 'ResponsavelService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ResponsavelService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(ResponsavelService._path, 'ResponsavelService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ResponsavelService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(ResponsavelService._path, 'ResponsavelService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ResponsavelService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(ResponsavelService._path, 'ResponsavelService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.SincronizacaoManualService');

if (typeof this['SincronizacaoManualService'] == 'undefined') SincronizacaoManualService = {};

SincronizacaoManualService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.crud.bean.ConfiguracaoEntrada} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SincronizacaoManualService.sincroniza = function(p0, p1, callback) {
  return dwr.engine._execute(SincronizacaoManualService._path, 'SincronizacaoManualService', 'sincroniza', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {class java.util.Date} p2 a param
 * @param {function|Object} callback callback function or options object
 */
SincronizacaoManualService.ativaRecuperadorManual = function(p0, p1, p2, callback) {
  return dwr.engine._execute(SincronizacaoManualService._path, 'SincronizacaoManualService', 'ativaRecuperadorManual', arguments);
};

/**
 * @param {class java.util.Date} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {function|Object} callback callback function or options object
 */
SincronizacaoManualService.ativaRecuperadorGeralManual = function(p0, p1, callback) {
  return dwr.engine._execute(SincronizacaoManualService._path, 'SincronizacaoManualService', 'ativaRecuperadorGeralManual', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ConversorMedicao');

if (typeof this['ConversorMedicao'] == 'undefined') ConversorMedicao = {};

ConversorMedicao._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.medicao.crud.bean.MedicaoBruta} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ConversorMedicao.convert = function(p0, callback) {
  return dwr.engine._execute(ConversorMedicao._path, 'ConversorMedicao', 'convert', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ResultadoSimulacaoService');

if (typeof this['ResultadoSimulacaoService'] == 'undefined') ResultadoSimulacaoService = {};

ResultadoSimulacaoService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.gerarExcel = function(p0, callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'gerarExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.enums.TipoPlanilha} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.limparByAba = function(p0, callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'limparByAba', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.confirmaDadoSimulacao = function(p0, callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'confirmaDadoSimulacao', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.deleteById = function(p0, callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.findById = function(p0, callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'findById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {class java.lang.Integer} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.saveInList = function(p0, p1, callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'saveInList', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.findAll = function(callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.previsao.crud.bean.ResultadoSimulacao} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ResultadoSimulacaoService.save = function(p0, callback) {
  return dwr.engine._execute(ResultadoSimulacaoService._path, 'ResultadoSimulacaoService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.DelimitadorDataService');

if (typeof this['DelimitadorDataService'] == 'undefined') DelimitadorDataService = {};

DelimitadorDataService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
DelimitadorDataService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(DelimitadorDataService._path, 'DelimitadorDataService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.ChuvaAcumuladaService');

if (typeof this['ChuvaAcumuladaService'] == 'undefined') ChuvaAcumuladaService = {};

ChuvaAcumuladaService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {interface java.util.List} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ChuvaAcumuladaService.somaMedicoesChuvaAcumuladaVerDados = function(p0, p1, callback) {
  return dwr.engine._execute(ChuvaAcumuladaService._path, 'ChuvaAcumuladaService', 'somaMedicoesChuvaAcumuladaVerDados', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.chuvaAcumulada.filter.ChuvaFilter} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ChuvaAcumuladaService.carregaChuvaAcumulada = function(p0, callback) {
  return dwr.engine._execute(ChuvaAcumuladaService._path, 'ChuvaAcumuladaService', 'carregaChuvaAcumulada', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {class java.util.Date} p1 a param
 * @param {function|Object} callback callback function or options object
 */
ChuvaAcumuladaService.somaMedicoesChuvaAcumulada = function(p0, p1, callback) {
  return dwr.engine._execute(ChuvaAcumuladaService._path, 'ChuvaAcumuladaService', 'somaMedicoesChuvaAcumulada', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
ChuvaAcumuladaService.carregaItemLegenda = function(callback) {
  return dwr.engine._execute(ChuvaAcumuladaService._path, 'ChuvaAcumuladaService', 'carregaItemLegenda', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.chuvaAcumulada.filter.ChuvaFilter} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ChuvaAcumuladaService.obtemDataInicialPorFiltro = function(p0, callback) {
  return dwr.engine._execute(ChuvaAcumuladaService._path, 'ChuvaAcumuladaService', 'obtemDataInicialPorFiltro', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.chuvaAcumulada.filter.ChuvaFilter} p0 a param
 * @param {function|Object} callback callback function or options object
 */
ChuvaAcumuladaService.exportar = function(p0, callback) {
  return dwr.engine._execute(ChuvaAcumuladaService._path, 'ChuvaAcumuladaService', 'exportar', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TabelaBoletimService');

if (typeof this['TabelaBoletimService'] == 'undefined') TabelaBoletimService = {};

TabelaBoletimService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {function|Object} callback callback function or options object
 */
TabelaBoletimService.findUnique = function(callback) {
  return dwr.engine._execute(TabelaBoletimService._path, 'TabelaBoletimService', 'findUnique', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.TabelaBoletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TabelaBoletimService.save = function(p0, callback) {
  return dwr.engine._execute(TabelaBoletimService._path, 'TabelaBoletimService', 'save', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.EquationValidator');

if (typeof this['EquationValidator'] == 'undefined') EquationValidator = {};

EquationValidator._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
EquationValidator.validateLogicExpression = function(p0, p1, callback) {
  return dwr.engine._execute(EquationValidator._path, 'EquationValidator', 'validateLogicExpression', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.UsuarioService');

if (typeof this['UsuarioService'] == 'undefined') UsuarioService = {};

UsuarioService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.deleteById = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.findById = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'findById', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.getGrupoUsuarioByRequest = function(callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'getGrupoUsuarioByRequest', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.findByGrupos = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'findByGrupos', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.findByEmailAndSenha = function(p0, p1, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'findByEmailAndSenha', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.getObjectGrupoUsuarioByRequest = function(callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'getObjectGrupoUsuarioByRequest', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.getUsuarioByRequest = function(callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'getUsuarioByRequest', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.getUsuariosAlerta = function(callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'getUsuariosAlerta', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.getAssinaturaUsuarioByRequest = function(callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'getAssinaturaUsuarioByRequest', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.findByEmail = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'findByEmail', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.checkPass = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'checkPass', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.bean.Usuario} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.saveUsuario = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'saveUsuario', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.findAll = function(callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'findAll', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.findByName = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'findByName', arguments);
};

/**
 * @param {class com.coffey.cprm.seguranca.crud.bean.Usuario} p0 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.save = function(p0, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'exportExcel', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.select.bean.SelectField} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
UsuarioService.populateSelect = function(p0, p1, callback) {
  return dwr.engine._execute(UsuarioService._path, 'UsuarioService', 'populateSelect', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.BoletimService');

if (typeof this['BoletimService'] == 'undefined') BoletimService = {};

BoletimService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.deleteById = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'deleteById', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.deleteByIds = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'deleteByIds', arguments);
};

/**
 * @param {class java.lang.Integer} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.findById = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'findById', arguments);
};

/**
 * @param {class java.lang.String} p0 a param
 * @param {class java.lang.String} p1 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.findAllOrderBy = function(p0, p1, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'findAllOrderBy', arguments);
};

/**
 * @param {interface java.util.List} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.findByIds = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'findByIds', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.ConfiguracaoEmailBoletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.enviaBoletimEmail = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'enviaBoletimEmail', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.enums.EnumTipoBoletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.obtemUltimoNumeroBoletimByTipo = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'obtemUltimoNumeroBoletimByTipo', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
BoletimService.obtemUltimoBoletim = function(callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'obtemUltimoBoletim', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.Boletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.saveBoletim = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'saveBoletim', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.Boletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.gerarBoletim = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'gerarBoletim', arguments);
};

/**
 * @param {function|Object} callback callback function or options object
 */
BoletimService.findAll = function(callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'findAll', arguments);
};

/**
 * @param {class com.coffey.cprm.publicacao.crud.bean.Boletim} p0 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.save = function(p0, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'save', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.populateGrid = function(p0, p1, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'populateGrid', arguments);
};

/**
 * @param {class com.coffey.cprm.geral.ui.flexigrid.bean.GridFilter} p0 a param
 * @param {class com.coffey.cprm.seguranca.crud.enums.EnumTipoAcesso} p1 a param
 * @param {function|Object} callback callback function or options object
 */
BoletimService.exportExcel = function(p0, p1, callback) {
  return dwr.engine._execute(BoletimService._path, 'BoletimService', 'exportExcel', arguments);
};

if (window['dojo']) dojo.provide('dwr.interface.TesteConversorService');

if (typeof this['TesteConversorService'] == 'undefined') TesteConversorService = {};

TesteConversorService._path = ''+JAWR.jawr_dwr_path+'';

/**
 * @param {class com.coffey.cprm.entrada.conversor.crud.bean.Conversor} p0 a param
 * @param {function|Object} callback callback function or options object
 */
TesteConversorService.testaScript = function(p0, callback) {
  return dwr.engine._execute(TesteConversorService._path, 'TesteConversorService', 'testaScript', arguments);
};

