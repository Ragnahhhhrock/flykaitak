/* Fly Kai Tak blog: English / Cantonese toggle. The choice is stored under the same key as the home screen. */
(function(){
var ZH={
'Skip to content':'跳到內容','Blog':'網誌','Play':'開始玩',
'© Fly Kai Tak.':'© Fly Kai Tak。','Another Mal Gordon project':'Mal Gordon 嘅另一個作品',
'Map data © Lands Department, HKSAR Government. Elevation: SRTM via AWS Terrain Tiles. Aircraft and liveries are not real airlines.':'地圖數據 © 香港特別行政區政府地政總署。高度數據：SRTM，經 AWS Terrain Tiles 提供。飛機同塗裝並非真實航空公司。',
'Feature':'新功能','Update':'更新','Behind the scenes':'幕後花絮',
'Share this post':'分享呢篇文章','Post on X':'喺 X 發佈','Email':'電郵','Copy link':'複製連結','Share…':'分享…','Link copied':'已複製連結',
'Fly the approach yourself':'親自飛一次進場',
'It runs in your browser. Pick an aircraft, a time of day and the weather, then hit the checkerboard.':'喺瀏覽器就玩得。揀機型、時間同天氣，然後飛向棋盤。',
'Begin descent':'開始下降','More from the blog':'網誌更多文章','Read the post →':'閱讀文章 →',
'The Fly Kai Tak blog':'Fly Kai Tak 網誌','New features, bug fixes and notes from the Kai Tak approach.':'新功能、錯誤修正，以及啟德進場嘅筆記。','Latest posts':'最新文章',
'Search':'搜尋','Category':'分類','Sort':'排序','Newest':'最新','By category':'按分類','All':'全部','Posts by category':'按分類排列嘅文章',
'← Previous':'← 上一頁','Next →':'下一頁 →','1 post':'1 篇文章'};
var MON={January:1,February:2,March:3,April:4,May:5,June:6,July:7,August:8,September:9,October:10,November:11,December:12};
var TAGS={Feature:'新功能',Update:'更新','Behind the scenes':'幕後花絮',Fix:'修正',New:'新增',History:'歷史'};
function zhDate(d,m,y){return y+' 年 '+MON[m]+' 月 '+d+' 日'}
function zhOf(s){
  var t=s.trim();if(!t)return null;
  if(Object.prototype.hasOwnProperty.call(ZH,t))return ZH[t];
  var m;
  if((m=/^(\d+) min read$/.exec(t)))return m[1]+' 分鐘閱讀';
  if((m=/^(\d+) (January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})$/.exec(t)))return zhDate(m[1],m[2],m[3]);
  if((m=/^(\d+) posts$/.exec(t)))return m[1]+' 篇文章';
  if((m=/^Page (\d+) of (\d+)$/.exec(t)))return '第 '+m[1]+' 頁，共 '+m[2]+' 頁';
  if((m=/^(Feature|Update|Fix|New|History|Behind the scenes) · (\d+) (\w+) (\d{4})$/.exec(t))&&MON[m[3]])return TAGS[m[1]]+' · '+zhDate(m[2],m[3],m[4]);
  return null}
var lang='en';try{if(localStorage.getItem('fkt-lang')==='zh')lang='zh'}catch(e){}
var orig=new WeakMap();
function apply(){
  var root=document.documentElement;
  root.setAttribute('data-lang',lang);root.lang=lang==='zh'?'zh-HK':'en';
  var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  for(var n;n=w.nextNode();){
    var p=n.parentNode;if(!p||p.closest('.prose,[data-zh],script,style,#btnLang'))continue;
    var o=orig.get(n);if(o===undefined){o=n.nodeValue;orig.set(n,o)}
    var z=lang==='zh'?zhOf(o):null;
    var v=z===null?o:o.slice(0,o.length-o.trimStart().length)+z+o.slice(o.trimEnd().length);
    if(n.nodeValue!==v)n.nodeValue=v}
  document.querySelectorAll('[data-zh]').forEach(function(el){
    if(el.dataset.en===undefined)el.dataset.en=el.textContent;
    var v=lang==='zh'?el.getAttribute('data-zh'):el.dataset.en;if(el.textContent!==v)el.textContent=v});
  document.querySelectorAll('[data-zh-alt]').forEach(function(el){
    if(el.dataset.enAlt===undefined)el.dataset.enAlt=el.getAttribute('alt')||'';
    el.setAttribute('alt',lang==='zh'?el.getAttribute('data-zh-alt'):el.dataset.enAlt)});
  var t=document.querySelector('meta[name=fkt-zh-title]');
  if(t){if(!document.documentElement.dataset.enTitle)document.documentElement.dataset.enTitle=document.title;
    document.title=lang==='zh'?t.content:document.documentElement.dataset.enTitle}
  var b=document.getElementById('btnLang');
  if(b){b.setAttribute('aria-pressed',lang==='zh');b.querySelectorAll('span').forEach(function(s){s.classList.toggle('on',s.getAttribute('data-l')===lang)})}}
var btn=document.getElementById('btnLang');
if(btn)btn.addEventListener('click',function(e){
  lang=lang==='zh'?'en':'zh';try{localStorage.setItem('fkt-lang',lang)}catch(_){}
  try{window.gtag&&gtag('event','language_toggle',{language:lang==='zh'?'cantonese':'english',page_type:'blog'})}catch(_){}
  apply();e.currentTarget.blur()});
apply();
})();
