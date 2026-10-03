/* Fly Kai Tak blog: search all posts (blog/search.json, built by tools/blog.py). Results replace the post list, 20 per page. */
(function(){
var form=document.getElementById('blogsearch'),input=document.getElementById('blogq');
var list=document.getElementById('postlist'),box=document.getElementById('results');
if(!form||!input||!list||!box)return;
var cards=document.getElementById('resultcards'),count=document.getElementById('resultcount'),pager=document.getElementById('resultpager');
var PER=20,root=document.documentElement,data=null,loading=null,failed=false,q='',page=1,found=[],lastTracked='',trackTimer=0,timer=0;
var TAGS={Feature:'新功能',Update:'更新','Behind the scenes':'幕後花絮',Fix:'修正',New:'新增',History:'歷史'};
function zh(){return root.getAttribute('data-lang')==='zh'}
var T={
  en:{none:'No posts match your search.',err:'Search is not available right now.',read:'Read the post →',prev:'← Previous',next:'Next →',
      found:function(n){return n===1?'1 post found':n+' posts found'},pg:function(n,m){return 'Page '+n+' of '+m}},
  zh:{none:'搵唔到相關文章。',err:'暫時用唔到搜尋。',read:'閱讀文章 →',prev:'← 上一頁',next:'下一頁 →',
      found:function(n){return '搵到 '+n+' 篇文章'},pg:function(n,m){return '第 '+n+' 頁，共 '+m+' 頁'}}};
function t(){return zh()?T.zh:T.en}
function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e}
function load(){
  if(data)return Promise.resolve(data);
  if(!loading)loading=fetch('/blog/search.json').then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(j){
    data=j.map(function(e){
      var title=(e.t+' '+e.tz).toLowerCase();
      var meta=[e.d,e.dz,e.k,e.tag,e.cn,e.cz,e.dh,e.dhz].join(' ').toLowerCase();
      e._t=title;e._m=meta;e._x=(e.x+' '+e.xz).toLowerCase();return e});return data}).catch(function(){failed=true;loading=null;return null});
  return loading}
function run(query,pg){
  q=query.trim();page=pg||1;
  var tokens=q.toLowerCase().split(/\s+/).filter(Boolean);
  if(!tokens.length){found=[];show();return Promise.resolve()}
  return load().then(function(d){
    if(q!==query.trim())return;
    if(!d){found=null;show();return}
    found=d.map(function(e){
      var s=0;
      for(var i=0;i<tokens.length;i++){
        var k=tokens[i],a=e._t.indexOf(k)>-1,b=e._m.indexOf(k)>-1,c=e._x.indexOf(k)>-1;
        if(!a&&!b&&!c)return null;
        s+=(a?6:0)+(b?3:0)+(c?1:0)}
      return {e:e,s:s}}).filter(Boolean).sort(function(x,y){return y.s-x.s||(x.e.date<y.e.date?1:x.e.date>y.e.date?-1:0)}).map(function(r){return r.e});
    show()})}
function card(e){
  var a=el('a','pcard');a.href='/blog/'+e.s+'/';
  var img=el('img');img.src=e.img;img.width=1200;img.height=630;img.loading='lazy';img.alt=zh()?e.az:e.a;a.appendChild(img);
  var b=el('div','body');
  b.appendChild(el('span','catpill',zh()?e.cz:e.cn));
  b.appendChild(el('div','meta',(zh()?(TAGS[e.tag]||e.tag):e.tag)+' · '+(zh()?e.dhz:e.dh)));
  b.appendChild(el('h3',null,zh()?e.tz:e.t));
  b.appendChild(el('p',null,zh()?e.dz:e.d));
  b.appendChild(el('span','more',t().read));
  a.appendChild(b);return a}
function btn(label,pg,cur){
  var b=el('button','pg',label);b.type='button';
  if(cur)b.setAttribute('aria-current','page');
  b.addEventListener('click',function(){page=pg;show(true)});return b}
function show(scroll){
  var active=q.length>0;
  list.hidden=active;box.hidden=!active;
  var url=location.pathname+(active?'?q='+encodeURIComponent(q)+(page>1?'&p='+page:''):'');
  try{history.replaceState(null,'',url)}catch(e){}
  cards.textContent='';pager.textContent='';pager.hidden=true;
  if(!active){count.textContent='';return}
  if(found===null){count.textContent=t().err;return}
  var pages=Math.max(1,Math.ceil(found.length/PER));if(page>pages)page=pages;
  count.textContent=found.length?t().found(found.length):t().none;
  found.slice((page-1)*PER,page*PER).forEach(function(e){cards.appendChild(card(e))});
  if(pages>1){
    pager.hidden=false;pager.appendChild(el('span','pginfo',t().pg(page,pages)));
    if(page>1)pager.appendChild(btn(t().prev,page-1));
    for(var i=1;i<=pages;i++)pager.appendChild(btn(String(i),i,i===page));
    if(page<pages)pager.appendChild(btn(t().next,page+1));
    if(scroll)box.scrollIntoView({block:'start'})}}
function track(){
  clearTimeout(trackTimer);
  trackTimer=setTimeout(function(){
    if(q.length<2||q.toLowerCase()===lastTracked)return;
    lastTracked=q.toLowerCase();
    try{window.gtag&&gtag('event','search',{search_term:q,results:found?found.length:0,page_type:'blog'})}catch(e){}},900)}
input.addEventListener('input',function(){clearTimeout(timer);timer=setTimeout(function(){run(input.value,1).then(track)},120)});
form.addEventListener('submit',function(e){e.preventDefault();clearTimeout(timer);run(input.value,1).then(track)});
new MutationObserver(function(){if(q)show()}).observe(root,{attributes:true,attributeFilter:['data-lang']});
var m=/[?&]q=([^&]*)/.exec(location.search);
if(m){try{q=decodeURIComponent(m[1].replace(/\+/g,' '))}catch(e){q=''}
  var pm=/[?&]p=(\d+)/.exec(location.search);
  if(q){input.value=q;run(q,pm?parseInt(pm[1],10):1)}}
})();
