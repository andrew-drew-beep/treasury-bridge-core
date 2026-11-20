'use strict';
let report;
let selectedScope = null;
const scopeFields = ['company','bank_account','ledger_account','currency','direction'];
const inSelectedScope = row => !selectedScope || scopeFields.every(key => row[key] === selectedScope[key]);
const scopeLabel = scope => scope.company+', '+scope.bank_account+', '+(scope.direction==='IN'?'Entrada':'Saída')+', '+scope.ledger_account+', '+scope.currency;
const $ = id => document.getElementById(id);
const labels = {RULE_MATCH:'Por regra · revisar', APPROVED:'Aprovado', HELD:'Revisão pendente', AMBIGUOUS:'Ambíguo', MISSING_ID:'Sem CNPJ', UNMATCHED:'Sem correspondência', PENDING:'Há pendências', READY_FOR_REVIEW:'Pronto para revisão', REVIEWED:'Conferido'};
const el = (tag, text, cls) => {const n = document.createElement(tag); if(text !== undefined) n.textContent=text; if(cls) n.className=cls; return n;};
const amount = (value,currency) => new Intl.NumberFormat('pt-BR',{style:'currency',currency}).format(value);
const badge = status => el('span', labels[status]||status, 'badge '+(['APPROVED','REVIEWED'].includes(status)?'good':['RULE_MATCH','READY_FOR_REVIEW'].includes(status)?'neutral':'warn'));
function message(text,error=false){$('message').textContent=text;$('message').className=error?'error':'';}
async function api(url,body){const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); const data=await response.json();if(!response.ok)throw Error(data.error||'Falha ao processar');return data;}
function render(data){if(report?.run_id!==data.run_id)selectedScope=null;report=data;$('workspace').hidden=false;localStorage.setItem('treasuryRun',data.run_id);$('exportCsv').href='/api/export.csv?run='+data.run_id;$('exportJson').href='/api/export.json?run='+data.run_id;
 const c=data.counts;const unresolved=data.items.filter(x=>!['RULE_MATCH','APPROVED'].includes(x.status)).length;
 const metrics=[['Movimentos bancários',data.bank.length,'12 contas no cenário demonstrativo'],['Correspondências por regra',c.RULE_MATCH||0,'Evidências disponíveis para conferência'],['Pendências bancárias',unresolved,'Mesmo total não significa conciliação'],['Aprovadas na revisão',c.APPROVED||0,'Decisões registradas no histórico']];
 $('metrics').replaceChildren(...metrics.map(([title,value,sub])=>{const n=el('div',undefined,'metric');n.append(el('div',title,'label'),el('strong',value),el('span',sub));return n;}));
 $('metrics').firstChild.lastChild.textContent=new Set(data.bank.map(x=>x.company+'|'+x.bank_account)).size+' contas nesta execução';
 $('runInfo').textContent='Execução '+data.run_id+' · Regras '+data.rule_version+' · Janela de '+data.window_days+' dias corridos · '+data.ledger.length+' registros contábeis';
 renderGroups();
 renderScopeContext();
 renderItems();
 renderLedgerPending();
 $('events').replaceChildren(...(data.events?.length?data.events.map(e=>el('div',new Date(e.created_at).toLocaleString('pt-BR')+' · '+e.reviewer+' · '+e.bank_id+' / '+(e.ledger_id||'sem vínculo')+' · '+(e.decision==='APPROVE'?'Aprovou':'Rejeitou')+' — '+e.note,'event')):[el('p','As decisões aparecerão aqui com responsável, justificativa e horário.','empty')]));
}
function renderGroups(){
 $('groups').replaceChildren(...report.groups.map(g=>{
  const row=el('tr');row.classList.toggle('selected-scope',Boolean(selectedScope)&&inSelectedScope(g));
  const first=el('td',g.bank_account);first.append(el('small',g.company+' / '+g.ledger_account));
  row.append(first,el('td',g.direction==='IN'?'Entrada':'Saída'),el('td',amount(g.bank_total,g.currency)),el('td',amount(g.ledger_total,g.currency)),el('td',amount(g.difference,g.currency)));
  const state=el('td');
  if(g.status==='PENDING'){
   const shortcut=el('button','Há pendências →','badge warn pending-shortcut');shortcut.type='button';
   shortcut.setAttribute('aria-label','Ver pendências de '+scopeLabel(g));
   shortcut.setAttribute('aria-controls','items ledgerPending');
   shortcut.setAttribute('aria-pressed',String(Boolean(selectedScope)&&inSelectedScope(g)));
   shortcut.addEventListener('click',()=>openPendingGroup(g));state.append(shortcut);
  }else state.append(badge(g.status));
  row.append(state);return row;
 }));
}
function renderScopeContext(){
 $('scopeContext').hidden=!selectedScope;
 $('scopeLabel').textContent=selectedScope?'Conta selecionada: '+scopeLabel(selectedScope):'';
}
function renderLedgerPending(){
 const rows=report.unmatched_ledger.filter(inSelectedScope);
 $('ledgerPending').replaceChildren(...(rows.length?rows.map(l=>{
  const n=el('div',l.id+' · '+l.bank_account+' · '+(l.direction==='IN'?'Entrada':'Saída')+' · '+amount(l.amount,l.currency)+' · '+l.cnpj,'event pending-record');n.tabIndex=-1;return n;
 }):[el('p',selectedScope?'Nenhum registro contábil sem vínculo nesta conta e fluxo.':'Todos os registros contábeis possuem vínculo nesta execução.','empty')]));
}
function openPendingGroup(group){
 selectedScope=Object.fromEntries(scopeFields.map(key=>[key,group[key]]));
 $('filter').value='pending';renderGroups();renderScopeContext();renderItems();renderLedgerPending();
 const target=$('items').querySelector('article')||$('ledgerPending').querySelector('.pending-record');
 if(target){target.focus({preventScroll:true});target.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});}
}
function renderItems(){if(!report)return;const filter=$('filter').value;const items=report.items.filter(x=>inSelectedScope(x.bank)&&(filter==='all'||filter==='pending'&&!['RULE_MATCH','APPROVED'].includes(x.status)||filter==='rule'&&x.status==='RULE_MATCH'||filter==='approved'&&x.status==='APPROVED'));
 $('items').replaceChildren(...(items.length?items.map(item=>{const b=item.bank,n=el('article',undefined,'item');n.tabIndex=-1;const head=el('div',undefined,'item-head');head.append(el('strong',b.id+' · '+(b.direction==='IN'?'Entrada':'Saída')+' · '+amount(b.amount,b.currency)),badge(item.status));n.append(head,el('p',item.reason));n.append(el('div',b.company+' / '+b.bank_account+' · '+b.date+' · CNPJ: '+(b.cnpj||'não informado'),'evidence'));n.append(el('div','Referência: '+(b.reference||'ausente')+' · Origem: '+b.source+', linha '+b.source_row+(item.ledger_id?' · Vínculo: '+item.ledger_id:''),'evidence'));
 const details=el('details',undefined,'review');details.append(el('summary','Examinar candidatos e registrar decisão'));const form=el('form');const grid=el('div',undefined,'review-grid');const select=el('select');select.setAttribute('aria-label','Registro contábil para '+b.id);select.append(new Option('Selecione um candidato',''));for(const id of item.candidate_ids){const l=report.ledger.find(x=>x.id===id);select.append(new Option(id+' · '+l.cnpj+' · '+amount(l.amount,l.currency)+' · '+l.date,id));}if(item.ledger_id)select.value=item.ledger_id;const reviewer=el('input');reviewer.placeholder='Seu nome';reviewer.required=true;reviewer.maxLength=100;reviewer.setAttribute('aria-label','Responsável por '+b.id);const note=el('input');note.placeholder='Evidência consultada ou motivo da pendência';note.required=true;note.maxLength=1000;note.setAttribute('aria-label','Justificativa para '+b.id);for(const [title,input]of [['Candidato contábil',select],['Responsável',reviewer],['Justificativa',note]]){const label=el('label',title);label.append(input);grid.append(label);}const actions=el('div',undefined,'actions');const approve=el('button','Aprovar vínculo');approve.type='submit';approve.disabled=!item.candidate_ids.length;const reject=el('button','Manter pendente');reject.type='button';async function submit(decision){if(!form.reportValidity())return;if(decision==='APPROVE'&&!select.value)return message('Selecione um registro contábil.',true);try{render(await api('/api/review',{run_id:report.run_id,bank_id:b.id,ledger_id:select.value||null,decision,reviewer:reviewer.value,note:note.value}));message('Decisão registrada. Os valores contabilizados permanecem os mesmos.');}catch(e){message(e.message,true);}}form.addEventListener('submit',e=>{e.preventDefault();submit('APPROVE');});reject.addEventListener('click',()=>submit('REJECT'));actions.append(approve,reject);form.append(grid,actions);details.append(form);n.append(details);return n;}):[el('p',selectedScope&&filter==='pending'?'Nenhuma pendência bancária neste recorte. Confira abaixo os registros contábeis sem vínculo.':'Nenhum movimento neste filtro.','empty')]));
}
$('clearScope').addEventListener('click',()=>{selectedScope=null;renderGroups();renderScopeContext();renderItems();renderLedgerPending();$('filter').focus();});
$('filter').addEventListener('change',renderItems);
$('demo').addEventListener('click',async()=>{const button=$('demo');button.disabled=true;try{render(await api('/api/demo',{}));message('Cenário fictício carregado. Comece pelas pendências e examine as evidências.');}catch(e){message(e.message,true);}finally{button.disabled=false;}});
function encoded(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(Error('Falha na leitura do arquivo'));reader.readAsDataURL(file);});}
$('upload').addEventListener('submit',async e=>{e.preventDefault();try{const files=[];for(const f of $('banks').files)files.push({name:f.name,side:'bank',content:await encoded(f)});const ledger=$('ledger').files[0];files.push({name:ledger.name,side:'ledger',content:await encoded(ledger)});render(await api('/api/import',{files,window:Number($('window').value)}));message('Arquivos conferidos. Verifique as pendências antes de concluir.');}catch(err){message(err.message,true);}});
const previous=localStorage.getItem('treasuryRun');if(previous)fetch('/api/report?run='+encodeURIComponent(previous)).then(r=>r.ok?r.json():null).then(data=>{if(data)render(data);}).catch(()=>{});
