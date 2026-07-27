let DATA={generated_at:null,items:[],sources:[],errors:[]};
let activeTab="now";
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];

function esc(v=""){return String(v).replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));}
function parseDate(v){const d=new Date(v);return Number.isNaN(d.getTime())?new Date(0):d;}
function fmtTime(v){return new Intl.DateTimeFormat("es-ES",{hour:"2-digit",minute:"2-digit"}).format(parseDate(v));}
function fmtDate(v){return new Intl.DateTimeFormat("es-ES",{day:"2-digit",month:"short"}).format(parseDate(v)).replace(".","");}
function relTime(v){const ms=Date.now()-parseDate(v);const h=Math.max(0,Math.floor(ms/36e5));if(h<1)return"hace menos de 1 h";if(h<24)return`hace ${h} h`;return`hace ${Math.floor(h/24)} d`;}
function provClass(p){return p==="Ávila"?"avila":p==="Toledo"?"toledo":"madrid";}

async function loadData(){
  const btn=$("#refreshBtn");
  btn?.classList.add("spinning");
  try{
    const r=await fetch(`data/latest.json?v=${Date.now()}`,{cache:"no-store"});
    if(!r.ok)throw new Error(`HTTP ${r.status}`);
    DATA=await r.json();
    $("#liveText").textContent=DATA.generated_at?"Datos reales":"Actualizando";
    if(DATA.generated_at){
      const d=new Date(DATA.generated_at);
      $("#lastUpdate").textContent=`Última actualización: ${new Intl.DateTimeFormat("es-ES",{hour:"2-digit",minute:"2-digit",day:"2-digit",month:"short"}).format(d)}`;
    }else $("#lastUpdate").textContent="Esperando primera actualización automática";
  }catch(e){
    DATA={generated_at:null,items:[],sources:DATA.sources||[],errors:[String(e)]};
    $("#liveText").textContent="Sin conexión";
    $("#lastUpdate").textContent="No se han podido cargar los datos";
  }finally{btn?.classList.remove("spinning");render();}
}

function getFiltered(type=null){
  const q=$("#searchInput")?.value.trim().toLowerCase()||"";
  const prov=$("#provinceFilter")?.value||"all";
  return (DATA.items||[]).filter(x=>{
    if(type&&x.type!==type)return false;
    if(prov!=="all"&&x.province!==prov)return false;
    if(q&&!`${x.title} ${x.summary||""} ${x.source||""} ${x.town||""} ${x.province||""}`.toLowerCase().includes(q))return false;
    return true;
  }).sort((a,b)=>parseDate(b.published)-parseDate(a.published));
}

function itemHTML(x){
  const official=x.type==="official";
  return `<article class="item ${official?"official":""} ${x.severity==="critical"?"critical-item":""}">
    <div class="timebox"><div class="time">${fmtTime(x.published)}</div><div class="date">${fmtDate(x.published)}</div></div>
    <div><div class="item-tags"><span class="tag ${official?"official":""}">${official?"FUENTE OFICIAL":"NOTICIA"}</span><span class="tag ${provClass(x.province)}">${esc(x.province)}</span></div><div class="item-title">${esc(x.title)}</div>${x.summary?`<div class="item-summary">${esc(x.summary)}</div>`:""}</div>
    <div class="sourcebox"><div class="source-name">${esc(x.source||"")}</div><div class="source-town">${esc(x.town||x.province||"")} · ${relTime(x.published)}</div><a class="open-link" href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">Abrir fuente</a></div>
  </article>`;
}

function renderList(el,arr){if(!el)return;el.innerHTML=arr.length?arr.map(itemHTML).join(""):'<div class="empty">No hay información publicada todavía con estos criterios.</div>';}

function renderProvinceStrip(){
  const root=$("#provinceStrip");if(!root)return;
  root.innerHTML=["Madrid","Ávila","Toledo"].map(p=>{const arr=(DATA.items||[]).filter(x=>x.province===p);const off=arr.filter(x=>x.type==="official").length;return `<button class="province-card" data-province="${p}"><div class="province-left"><div class="province-badge">${p[0]}</div><div><div class="province-name">${p}</div><div class="province-status">${off} avisos oficiales · ${arr.length} publicaciones</div></div></div><div class="province-count">${arr.length}</div></button>`;}).join("");
  $$(".province-card").forEach(b=>b.onclick=()=>{$("#provinceFilter").value=b.dataset.province;switchTab("now");render();});
}

function renderCritical(){
  const box=$("#criticalBox"),official=(DATA.items||[]).filter(x=>x.type==="official").sort((a,b)=>parseDate(b.published)-parseDate(a.published));
  if(!box)return;
  if(!official.length){box.style.display="none";return;}
  box.style.display="grid";const c=official[0];$("#criticalTitle").textContent=c.title;$("#criticalMeta").textContent=`${c.source} · ${c.town||c.province} · ${fmtTime(c.published)}`;$("#criticalLink").href=c.url;
}

function renderSources(){
  const el=$("#sourceGrid");if(!el)return;
  el.innerHTML=(DATA.sources||[]).map(s=>`<article class="source-card"><div class="source-head"><h3>${esc(s.name)}</h3><span class="verified ${s.kind==="official"?"official-source":""}">${s.kind==="official"?"OFICIAL":"MEDIO"}</span></div><p>${esc(s.area||"")}</p>${s.url?`<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">Abrir fuente</a>`:""}</article>`).join("");
}

function renderTowns(){
  const el=$("#townGrid");if(!el)return;
  const map={};for(const x of DATA.items||[]){const key=x.town||x.province||"Sin localidad";if(!map[key])map[key]={town:key,province:x.province,count:0,last:x.published};map[key].count++;if(parseDate(x.published)>parseDate(map[key].last))map[key].last=x.published;}
  const rows=Object.values(map).sort((a,b)=>b.count-a.count);
  el.innerHTML=rows.length?rows.map(x=>`<article class="town-card"><div class="town-top"><div><div class="town-name">${esc(x.town)}</div><div class="town-province">${esc(x.province)}</div></div><div class="town-number">${x.count}</div></div><div class="town-last">Última mención: ${relTime(x.last)}</div></article>`).join(""):'<div class="empty">Todavía no hay municipios detectados.</div>';
}

function switchTab(tab){activeTab=tab;$$('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));$$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${tab}`));}
function render(){const all=getFiltered();renderProvinceStrip();renderCritical();renderList($("#mainFeed"),all);renderList($("#officialFeed"),getFiltered("official"));renderList($("#newsFeed"),getFiltered("news"));renderTowns();renderSources();if($("#resultCount"))$("#resultCount").textContent=`${all.length} resultados`;}

$("#searchInput")?.addEventListener("input",render);
$("#provinceFilter")?.addEventListener("change",render);
$("#refreshBtn")?.addEventListener("click",loadData);
$$('[data-tab]').forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.tab)));

loadData();
