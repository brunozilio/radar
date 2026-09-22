"""Monthly wrapper check justified by official ANA HIDRO table Data=MM/AAAA."""
import importlib.util,calendar
from datetime import datetime,timezone
from urllib.parse import urlencode
from pathlib import Path
s=importlib.util.spec_from_file_location('collect',Path(__file__).with_name('collect.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
if __name__=='__main__':
 m.fetch({'file':'sources/ana-formato-hidro.pdf','url':'https://www.ana.gov.br/arquivos/infohidrologicas/cadastro/OrientacoesParaEnvioDosDadosHidrologicosColetadosDuranteaResolucaoANEEL_396_1998.pdf','kind':'Official ANA table layout; historical ingestion convention, not certification of current API'})
 jobs=[]
 for year,month in [(2011,7),(2015,10),(2017,5)]:
  a=f'{year}-{month:02d}-01';b=f'{year}-{month:02d}-{calendar.monthrange(year,month)[1]}'
  for qc in (2,1):
   params={'codEstacao':'86510000','dataInicio':datetime.fromisoformat(a).strftime('%d/%m/%Y'),'dataFim':datetime.fromisoformat(b).strftime('%d/%m/%Y'),'tipoDados':'1','nivelConsistencia':str(qc)}
   jobs.append(dict(start=a,end=b,parameters=params,file=f'raw/month-hidro-86510000-{a}--{b}-consistencia{qc}.xml',url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/HidroSerieHistorica?'+urlencode(params)))
 m.dump(m.P/'monthly-plan.json',{'registered_at_utc':datetime.now(timezone.utc).isoformat(),'reason':'Source ANA describes monthly Data field; weeks could exclude firstday monthly rows. Three sameevent months only; raw andconsistent explicitly queried. No yearlydata or newevent.', 'max_additional_get':6,'no_retry':True,'jobs':jobs,'official_format_sha256':m.sha(m.P/'sources/ana-formato-hidro.pdf')})
 attempts=[]
 for j in jobs:
  r=m.fetch(j);attempts.append(r);m.dump(m.P/'monthly-attempts.json',attempts)
  if r.get('http_status') in (401,403):break
