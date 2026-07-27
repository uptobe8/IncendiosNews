const SEED = {
  generated_at: "2026-07-27T13:45:00+02:00",
  items: [
    {id:"of-mad-1",type:"official",severity:"critical",province:"Madrid",town:"Sierra Oeste",published:"2026-07-27T10:30:00+02:00",source:"Comunidad de Madrid · ASEM 112",title:"Situación Operativa 3 de INFOMA26 y seguimiento oficial del incendio de Sierra Oeste",summary:"Actualización oficial: el incendio sigue afectando a municipios de la Sierra Oeste, con confinamientos, evacuaciones, cortes de carreteras y operativo reforzado.",url:"https://www.comunidad.madrid/seguridad-emergencias-asem-112/incendio-forestal-sierra-oeste-ifsierraoeste-julio-2026"},
    {id:"of-clm-1",type:"official",severity:"alert",province:"Toledo",town:"La Iglesuela del Tiétar",published:"2026-07-27T12:00:00+02:00",source:"Gobierno de Castilla-La Mancha",title:"Castilla-La Mancha consolida un perímetro de seguridad de 30 km en apoyo a Ávila y Madrid",summary:"El Gobierno regional informa de trabajos para frenar el avance por el sur y de una posible desescalada progresiva siempre condicionada a la evolución del incendio.",url:"https://www.castillalamancha.es/actualidad/notasdeprensa/castilla-la-mancha-consolida-un-perimetro-de-seguridad-de-30-kilometros-apoyando-avila-y-madrid-en"},
    {id:"of-pc-1",type:"official",severity:"alert",province:"Madrid",town:"Madrid / Ávila / Toledo",published:"2026-07-27T09:00:00+02:00",source:"Protección Civil y Emergencias",title:"Red de Alerta Nacional y avisos oficiales de Protección Civil",summary:"Acceso directo a las alertas oficiales estatales y recomendaciones de Protección Civil. La app mantiene esta fuente separada del flujo de medios.",url:"https://www.proteccioncivil.es/"},
    {id:"of-av-1",type:"official",severity:"alert",province:"Ávila",town:"Provincia de Ávila",published:"2026-07-27T08:00:00+02:00",source:"Junta de Castilla y León · INFOCAL",title:"Parte diario oficial de incendios forestales de Castilla y León",summary:"Fuente de datos abiertos de la Junta con municipio, nivel/IGR, situación, medios de extinción, superficie y horas de actualización. El servidor local la consulta automáticamente.",url:"https://analisis.datosabiertos.jcyl.es/explore/dataset/incendios-forestales/map/"},
    {id:"of-infocam-1",type:"official",severity:"alert",province:"Toledo",town:"Provincia de Toledo",published:"2026-07-27T08:00:00+02:00",source:"INFOCAM · Castilla-La Mancha",title:"Mapa y situación oficial de incendios forestales de Castilla-La Mancha",summary:"Portal oficial con incendios significativos, estado, localización, medios y boletín de riesgo por incendio forestal.",url:"https://infocam.castillalamancha.es/"},
    {id:"news-efe-1",type:"news",severity:"info",province:"Madrid",town:"Madrid / Ávila / Toledo",published:"2026-07-27T12:30:00+02:00",source:"EFE",title:"Treinta y ocho localidades evacuadas y siete confinadas por fuegos en Madrid, Ávila y Toledo",summary:"EFE recopila la actualización del Ministerio del Interior sobre municipios evacuados y confinados en las tres provincias afectadas.",url:"https://efe.com/espana/2026-07-27/evacuados-incendios-espana/"},
    {id:"news-rtve-1",type:"news",severity:"info",province:"Ávila",town:"Burgohondo",published:"2026-07-27T11:02:00+02:00",source:"RTVE",title:"Leve mejoría en los incendios de Madrid y Ávila, que siguen activos",summary:"La información de RTVE señala una evolución algo más favorable, aunque continúan los focos activos y miles de personas fuera de sus viviendas.",url:"https://www.rtve.es/noticias/20260727/incendios-madrid-avila-desalojados-hectareas/17169953.shtml"},
    {id:"news-efe-2",type:"news",severity:"info",province:"Ávila",town:"Burgohondo",published:"2026-07-27T10:45:00+02:00",source:"EFE",title:"El incendio de Ávila afronta una situación de leve mejoría tras una noche complicada por el viento",summary:"El foco iniciado en Burgohondo continúa bajo vigilancia con especial atención a las zonas de Mijares, Gavilanes, Casavieja, La Adrada, Sotillo y Piedralaves.",url:"https://efe.com/espana/2026-07-27/evolucion-del-incendio-en-avila/"},
    {id:"news-efe-3",type:"news",severity:"info",province:"Madrid",town:"Sierra Oeste",published:"2026-07-27T10:15:00+02:00",source:"EFE",title:"El fuego en Madrid disminuye su avance, pero sigue activo y sin estabilizar",summary:"EFE recoge que el incendio mantiene varios frentes y que el operativo centra la atención en el entorno del pantano de San Juan.",url:"https://efe.com/espana/2026-07-27/evolucion-incendios-comunidad-madrid/"},
    {id:"news-efe-4",type:"news",severity:"alert",province:"Madrid",town:"Red viaria",published:"2026-07-27T09:55:00+02:00",source:"EFE · DGT",title:"Los incendios mantienen cortadas decenas de vías secundarias en Madrid, Ávila y Toledo",summary:"Información sobre carreteras afectadas y recomendación de consultar los canales oficiales de Tráfico antes de cualquier desplazamiento.",url:"https://efe.com/espana/2026-07-27/carreteras-cortadas-incendios-forestales-espana/"},
    {id:"news-ep-1",type:"news",severity:"info",province:"Madrid",town:"Sierra Oeste",published:"2026-07-27T08:58:00+02:00",source:"Europa Press",title:"La evolución de los incendios de Ávila y Madrid es positiva, pero avanza despacio",summary:"Seguimiento en directo del operativo y de los focos activos en Madrid, Ávila y Toledo.",url:"https://www.europapress.es/sociedad/noticia-ultima-hora-incendios-forestales-espana-directo-focos-activos-zonas-afectadas-evacuaciones-20260724081326.html"},
    {id:"news-rtve-2",type:"news",severity:"info",province:"Madrid",town:"Madrid / Ávila / Toledo",published:"2026-07-26T23:45:00+02:00",source:"RTVE",title:"Mejoran los fuegos del centro de España tras una jornada de enorme impacto",summary:"Directo de RTVE con evolución, evacuaciones, confinamientos y balance de los incendios de Madrid, Ávila y Toledo.",url:"https://www.rtve.es/noticias/20260726/incendios-espana-hoy-ultima-hora-directo/17169680.shtml"},
    {id:"news-efe-5",type:"news",severity:"info",province:"Toledo",town:"Almorox",published:"2026-07-26T18:00:00+02:00",source:"EFE",title:"El fuego obliga a evacuar municipios de Ávila, Madrid y Toledo",summary:"Seguimiento de la ampliación de las zonas evacuadas y confinadas, incluyendo localidades de Toledo vinculadas a la propagación del incendio.",url:"https://efe.com/espana/2026-07-26/evolucion-incendios-madrid-avila-toledo/"}
  ],
  sources: [
    {name:"Comunidad de Madrid · ASEM 112",kind:"official",area:"Madrid",url:"https://www.comunidad.madrid/112",desc:"Emergencias, INFOMA, evacuaciones, confinamientos y recomendaciones."},
    {name:"Junta de Castilla y León · INFOCAL",kind:"official",area:"Ávila",url:"https://analisis.datosabiertos.jcyl.es/explore/dataset/incendios-forestales/map/",desc:"Parte diario oficial en datos abiertos con estado y medios de extinción."},
    {name:"INFOCAM · Castilla-La Mancha",kind:"official",area:"Toledo",url:"https://infocam.castillalamancha.es/",desc:"Mapa, situación actual, incendios significativos y boletín de riesgo."},
    {name:"Protección Civil y Emergencias",kind:"official",area:"España",url:"https://www.proteccioncivil.es/",desc:"Red de Alerta Nacional y avisos estatales."},
    {name:"DGT",kind:"official",area:"Carreteras",url:"https://www.dgt.es/conoce-el-estado-del-trafico/",desc:"Estado y restricciones de tráfico actualizadas."},
    {name:"AEMET",kind:"official",area:"Meteorología",url:"https://www.aemet.es/",desc:"Avisos meteorológicos y riesgo asociado a condiciones extremas."},
    {name:"EFE",kind:"media",area:"General",url:"https://efe.com/",desc:"Agencia de noticias."},
    {name:"RTVE",kind:"media",area:"General",url:"https://www.rtve.es/noticias/",desc:"Servicio público de información."},
    {name:"Europa Press",kind:"media",area:"General",url:"https://www.europapress.es/",desc:"Agencia de noticias."},
    {name:"Cadena SER",kind:"media",area:"General / local",url:"https://cadenaser.com/",desc:"Cobertura nacional y local."},
    {name:"Onda Cero",kind:"media",area:"General / local",url:"https://www.ondacero.es/",desc:"Cobertura nacional y local."},
    {name:"Telemadrid",kind:"media",area:"Madrid",url:"https://www.telemadrid.es/",desc:"Cobertura autonómica de Madrid."},
    {name:"Diario de Ávila",kind:"media",area:"Ávila",url:"https://www.diariodeavila.es/",desc:"Cobertura local de la provincia de Ávila."},
    {name:"La Tribuna de Toledo",kind:"media",area:"Toledo",url:"https://www.latribunadetoledo.es/",desc:"Cobertura local de Toledo."}
  ]
};

let DATA = structuredClone(SEED);
let activeTab = "now";
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];

function esc(v=""){return String(v).replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));}
function parseDate(v){const d=new Date(v);return Number.isNaN(d.getTime())?new Date(0):d;}
function fmtTime(v){return new Intl.DateTimeFormat("es-ES",{hour:"2-digit",minute:"2-digit"}).format(parseDate(v));}
function fmtDate(v){return new Intl.DateTimeFormat("es-ES",{day:"2-digit",month:"short"}).format(parseDate(v)).replace('.','');}
function relTime(v){const ms=Date.now()-parseDate(v);const h=Math.max(0,Math.round(ms/36e5)); if(h<1)return "hace menos de 1 h"; if(h<24)return `hace ${h} h`; const d=Math.round(h/24);return `hace ${d} d`}
function provClass(p){return p==="Ávila"?"avila":p==="Toledo"?"toledo":"madrid";}

function getFiltered(type=null){
  const q=$("#searchInput").value.trim().toLowerCase();
  const prov=$("#provinceFilter").value;
  const ftype=$("#typeFilter").value;
  const hours=$("#timeFilter").value;
  const now=Date.now();
  return DATA.items.filter(x=>{
    if(type && x.type!==type)return false;
    if(prov!=="all" && x.province!==prov)return false;
    if(ftype!=="all" && x.type!==ftype)return false;
    if(hours!=="all" && now-parseDate(x.published)>Number(hours)*36e5)return false;
    if(q && !`${x.title} ${x.summary} ${x.source} ${x.town} ${x.province}`.toLowerCase().includes(q))return false;
    return true;
  }).sort((a,b)=>parseDate(b.published)-parseDate(a.published));
}

function itemHTML(x){
  const isOff=x.type==="official";
  const cls=`item ${isOff?'official':''} ${x.severity==='critical'?'critical-item':''}`;
  return `<article class="${cls}">
    <div class="timebox"><div class="time">${fmtTime(x.published)}</div><div class="date">${fmtDate(x.published)}</div></div>
    <div class="itembody">
      <div class="item-tags"><span class="tag ${isOff?'official':''}">${isOff?'FUENTE OFICIAL':'NOTICIA'}</span>${x.severity==='critical'||x.severity==='alert'?'<span class="tag alert">ALERTA</span>':''}<span class="tag ${provClass(x.province)}">${esc(x.province)}</span></div>
      <div class="item-title">${esc(x.title)}</div>
      <div class="item-summary">${esc(x.summary||'')}</div>
    </div>
    <div class="sourcebox"><div><div class="source-name">${esc(x.source)}</div><div class="source-town">${esc(x.town||x.province)} · ${relTime(x.published)}</div></div><a class="open-link" target="_blank" rel="noopener" href="${esc(x.url)}">Abrir fuente ↗</a></div>
  </article>`;
}
function renderList(el,arr){el.innerHTML=arr.length?arr.map(itemHTML).join(''):'<div class="empty">No hay resultados con estos filtros.</div>';}

function renderProvinceStrip(){
  const provs=["Madrid","Ávila","Toledo"];
  $("#provinceStrip").innerHTML=provs.map(p=>{
    const arr=DATA.items.filter(x=>x.province===p);const off=arr.filter(x=>x.type==='official').length;
    return `<button class="province-card" data-province="${p}"><div class="province-left"><div class="province-badge">${p[0]}</div><div><div class="province-name">${p}</div><div class="province-status">${off} fuentes/avisos oficiales · ${arr.length} entradas</div></div></div><div class="province-count">${arr.length}</div></button>`
  }).join('');
  $$(".province-card").forEach(b=>b.onclick=()=>{$("#provinceFilter").value=b.dataset.province;switchTab('now');render();window.scrollTo({top:520,behavior:'smooth'})});
}
function renderCritical(){
  const c=DATA.items.filter(x=>x.type==='official').sort((a,b)=>(b.severity==='critical')-(a.severity==='critical')||parseDate(b.published)-parseDate(a.published))[0];
  if(!c)return;
  $("#criticalTitle").textContent=c.title;$("#criticalMeta").textContent=`${c.source} · ${c.town} · ${fmtTime(c.published)} · ${fmtDate(c.published)}`;$("#criticalLink").href=c.url;
}
function renderTowns(){
  const map=new Map();
  getFiltered().forEach(x=>{const key=x.town||x.province;if(!map.has(key))map.set(key,{name:key,province:x.province,count:0,last:x.published});const a=map.get(key);a.count++;if(parseDate(x.published)>parseDate(a.last))a.last=x.published});
  const arr=[...map.values()].sort((a,b)=>b.count-a.count||parseDate(b.last)-parseDate(a.last));
  $("#townGrid").innerHTML=arr.length?arr.map(t=>`<button class="town-card" data-town="${esc(t.name)}"><div class="town-top"><div><div class="town-name">${esc(t.name)}</div><div class="town-province">${esc(t.province)}</div></div><div class="town-number">${t.count}</div></div><div class="town-last">Última referencia ${relTime(t.last)} · ${fmtTime(t.last)}</div></button>`).join(''):'<div class="empty">Sin municipios para estos filtros.</div>';
  $$(".town-card").forEach(b=>b.onclick=()=>{$("#searchInput").value=b.dataset.town;switchTab('now');render()});
}
function renderSources(){
  $("#sourceGrid").innerHTML=DATA.sources.map(s=>`<article class="source-card"><div class="source-head"><h3>${esc(s.name)}</h3><span class="verified ${s.kind==='official'?'official-source':''}">${s.kind==='official'?'OFICIAL':'VERIFICADA'}</span></div><p>${esc(s.desc)}</p><div class="town-province">${esc(s.area)}</div><a target="_blank" rel="noopener" href="${esc(s.url)}">Abrir fuente ↗</a></article>`).join('');
}
function render(){
  const all=getFiltered();renderList($("#mainFeed"),all);renderList($("#officialFeed"),getFiltered('official'));renderList($("#newsFeed"),getFiltered('news'));$("#resultCount").textContent=`${all.length} entradas`;renderProvinceStrip();renderCritical();renderTowns();renderSources();
}
function switchTab(tab){activeTab=tab;$$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${tab}`));$$('.tab,.mobile-tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));}
$$('.tab,.mobile-tab').forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.tab)));
['#searchInput','#provinceFilter','#typeFilter','#timeFilter'].forEach(s=>$(s).addEventListener(s==='#searchInput'?'input':'change',render));

async function refreshLive(manual=false){
  const btn=$("#refreshBtn");btn.classList.add('spinning');
  try{
    if(manual){try{await fetch('/api/refresh',{method:'POST',cache:'no-store'});}catch{} }
    const r=await fetch(`/api/feed?ts=${Date.now()}`,{cache:'no-store'});
    if(!r.ok)throw new Error('offline');
    const live=await r.json();
    if(live && Array.isArray(live.items) && live.items.length){DATA=live;$("#liveText").textContent='ACTUALIZACIÓN EN VIVO';$("#connectionMode").textContent='Servidor local conectado';$("#lastUpdate").textContent=`Última carga: ${new Intl.DateTimeFormat('es-ES',{hour:'2-digit',minute:'2-digit'}).format(new Date(live.generated_at||Date.now()))}`;render();}
  }catch(e){$("#liveText").textContent='MODO LOCAL';$("#connectionMode").textContent='Instantánea local disponible';}
  finally{btn.classList.remove('spinning')}
}
$("#refreshBtn").onclick=()=>refreshLive(true);
render();refreshLive(false);setInterval(()=>refreshLive(false),180000);
